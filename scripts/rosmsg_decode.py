"""Generic ROS1 message decoder/encoder driven by a message_definition text.
(Python 2 and 3: the robot's python2 runs it too.)

A TCPROS publisher header carries `message_definition`: the .msg text of the
topic type followed by `=====` separated sections, one per nested type
(`MSG: pkg/Name`). This module parses that text and deserializes raw TCPROS
message bodies into plain dicts, so any topic can be decoded without the
robot's (incomplete) rospy. Python 3, stdlib only.

    specs = parse_definition(text, root_type="robot/Robot")
    msg = decode(body_bytes, specs, "robot/Robot")
    flat = flatten(msg)   # {"pose.pose.x": 12.5, "onOffInfo.values[5].value": 1, ...}
"""
import re
import struct

BUILTIN = {
    "bool": "?", "int8": "b", "uint8": "B", "byte": "b", "char": "B",
    "int16": "h", "uint16": "H", "int32": "i", "uint32": "I",
    "int64": "q", "uint64": "Q", "float32": "f", "float64": "d",
}
SECTION_RE = re.compile(r"^=+\s*$", re.M)
MSG_RE = re.compile(r"^MSG:\s*(\S+)\s*$", re.M)
FIELD_RE = re.compile(r"^\s*([\w/]+)\s*(\[(\d*)\])?\s+(\w+)\s*(?:=\s*(.*))?$")


class Field(object):
    __slots__ = ("name", "type", "array")  # array: None, -1 (variable), or fixed N

    def __init__(self, name, type_, array):
        self.name, self.type, self.array = name, type_, array

    def __repr__(self):
        return "%s %s%s" % (self.type, self.name, "" if self.array is None else "[]" if self.array == -1 else "[%d]" % self.array)


def parse_section(text):
    """Parse one .msg body into a list of Field (constants are skipped)."""
    fields = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = FIELD_RE.match(line)
        if not m:
            continue
        type_, is_arr, n, name, const = m.groups()
        if const is not None:
            continue  # constant definition
        array = None if not is_arr else (-1 if n == "" else int(n))
        fields.append(Field(name, type_, array))
    return fields


def parse_definition(text, root_type):
    """Return {typename: [Field]} for the root and every nested type."""
    parts = SECTION_RE.split(text)
    specs = {root_type: parse_section(parts[0])}
    for part in parts[1:]:
        m = MSG_RE.search(part)
        if not m:
            continue
        name = m.group(1)
        body = part[m.end():]
        specs[name] = parse_section(body)
    return specs


def resolve(specs, type_, pkg):
    if type_ in BUILTIN or type_ in ("string", "time", "duration"):
        return type_
    if type_ == "Header":
        return "std_msgs/Header"
    if type_ in specs:
        return type_
    if "/" not in type_:
        cand = pkg + "/" + type_
        if cand in specs:
            return cand
        for k in specs:
            if k != "__text__" and k.endswith("/" + type_):
                return k
    raise KeyError("unknown message type %r (from package %s)" % (type_, pkg))


class Cursor(object):
    __slots__ = ("buf", "off")

    def __init__(self, buf):
        self.buf, self.off = buf, 0

    def take(self, fmt):
        v = struct.unpack_from("<" + fmt, self.buf, self.off)
        self.off += struct.calcsize("<" + fmt)
        return v


def _decode_scalar(cur, type_, specs, pkg):
    if type_ in BUILTIN:
        return cur.take(BUILTIN[type_])[0]
    if type_ == "string":
        n = cur.take("I")[0]
        s = cur.buf[cur.off:cur.off + n]
        cur.off += n
        return s.decode("utf-8", "replace")
    if type_ == "time" or type_ == "duration":
        a, b = cur.take("II" if type_ == "time" else "ii")
        return a + b / 1e9
    return _decode_msg(cur, specs, type_)


def _decode_msg(cur, specs, type_):
    pkg = type_.split("/")[0]
    out = {}
    for f in specs[type_]:
        t = resolve(specs, f.type, pkg)
        if f.array is None:
            out[f.name] = _decode_scalar(cur, t, specs, pkg)
            continue
        n = f.array if f.array >= 0 else cur.take("I")[0]
        if t in BUILTIN and t != "bool":
            fmt = "<%d%s" % (n, BUILTIN[t])
            vals = list(struct.unpack_from(fmt, cur.buf, cur.off))
            cur.off += struct.calcsize(fmt)
            out[f.name] = bytes(bytearray(vals)) if t in ("uint8", "char") else vals
        else:
            out[f.name] = [_decode_scalar(cur, t, specs, pkg) for _ in range(n)]
    return out


def decode(buf, specs, root_type):
    """Decode a raw message body. Returns (dict, bytes_consumed)."""
    cur = Cursor(buf)
    msg = _decode_msg(cur, specs, root_type)
    return msg, cur.off


def flatten(obj, prefix="", out=None):
    """Flatten nested dict/list into {"a.b[2].c": value}."""
    if out is None:
        out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(v, prefix + "." + k if prefix else k, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            flatten(v, "%s[%d]" % (prefix, i), out)
    else:
        out[prefix] = obj
    return out


def parse_tcpros_header(raw):
    """Decode a TCPROS header body (sequence of u32-len 'key=value' fields)."""
    fields = {}
    off = 0
    while off + 4 <= len(raw):
        n = struct.unpack_from("<I", raw, off)[0]
        off += 4
        kv = raw[off:off + n]
        off += n
        k, _, v = kv.partition(b"=")
        fields[k.decode()] = v.decode("utf-8", "replace")
    return fields


def load_local_definitions(site_packages):
    """Fallback: build {type: definition_text} from a rootfs dump's generated
    python message modules (<site-packages>/<pkg>/msg/_<Name>.py)."""
    import os
    defs = {}
    for pkg in os.listdir(site_packages):
        d = os.path.join(site_packages, pkg, "msg")
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not (fn.startswith("_") and fn.endswith(".py")) or fn == "__init__.py":
                continue
            s = open(os.path.join(d, fn), encoding="utf-8", errors="replace").read()
            m = re.search(r'_full_text = """(.*?)"""', s, re.S)
            if m:
                defs["%s/%s" % (pkg, fn[1:-3])] = m.group(1)
    return defs


# ---------------------------------------------------------------- encoding

def _encode_scalar(v, type_, specs, pkg):
    if type_ in BUILTIN:
        if type_ == "bool":
            v = 1 if v else 0
        return struct.pack("<" + BUILTIN[type_], v)
    if type_ == "string":
        b = v.encode("utf-8") if not isinstance(v, bytes) else v
        return struct.pack("<I", len(b)) + b
    if type_ in ("time", "duration"):
        secs = int(v)
        nsecs = int(round((v - secs) * 1e9))
        return struct.pack("<II" if type_ == "time" else "<ii", secs, nsecs)
    return encode(v or {}, specs, type_)


def encode(obj, specs, type_):
    """Encode a dict into a message body. Missing fields become zero/empty."""
    pkg = type_.split("/")[0]
    out = b""
    for f in specs[type_]:
        t = resolve(specs, f.type, pkg)
        v = obj.get(f.name) if isinstance(obj, dict) else None
        if f.array is None:
            if v is None:
                v = "" if t == "string" else (0 if t in BUILTIN or t in ("time", "duration") else {})
            out += _encode_scalar(v, t, specs, pkg)
            continue
        items = v if v is not None else []
        if isinstance(items, (bytes, bytearray)):
            items = list(bytearray(items))
        if f.array >= 0 and len(items) != f.array:
            raise ValueError("%s.%s needs exactly %d items" % (type_, f.name, f.array))
        if f.array < 0:
            out += struct.pack("<I", len(items))
        for it in items:
            out += _encode_scalar(it, t, specs, pkg)
    return out


# ---------------------------------------------------------------- md5 (ROS genmsg algorithm)

def _md5_text(specs, type_, cache):
    """Normalized text ROS hashes: constants first, then fields; nested types by md5."""
    if type_ in cache:
        return cache[type_]
    pkg = type_.split("/")[0]
    consts, fields = [], []
    for raw in _section_text(specs, type_).splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = FIELD_RE.match(line)
        if not m:
            continue
        ftype, is_arr, n, name, const = m.groups()
        if const is not None:
            consts.append("%s %s=%s" % (ftype, name, const.strip()))
            continue
        arr = "" if not is_arr else "[%s]" % n
        if ftype in BUILTIN or ftype in ("string", "time", "duration"):
            fields.append("%s%s %s" % (ftype, arr, name))
        else:
            sub = resolve(specs, ftype, pkg)
            fields.append("%s %s" % (md5_of(specs, sub, cache), name))
    text = "\n".join(consts + fields)
    cache[type_] = text
    return text


def md5_of(specs, type_, cache=None):
    import hashlib
    cache = {} if cache is None else cache
    return hashlib.md5(_md5_text(specs, type_, cache).encode()).hexdigest()


def service_md5(req_specs, req_type, resp_specs, resp_type):
    """ROS service md5 = md5(normalized request text + normalized response text)."""
    import hashlib
    a = _md5_text(req_specs, req_type, {})
    b = _md5_text(resp_specs, resp_type, {})
    return hashlib.md5((a + b).encode()).hexdigest()


def _section_text(specs, type_):
    return specs["__text__"][type_]


_orig_parse_definition = parse_definition


def parse_definition(text, root_type):
    """Like before, but also keeps each section's raw text (needed for md5)."""
    specs = _orig_parse_definition(text, root_type)
    parts = SECTION_RE.split(text)
    texts = {root_type: parts[0]}
    for part in parts[1:]:
        m = MSG_RE.search(part)
        if m:
            texts[m.group(1)] = part[m.end():]
    specs["__text__"] = texts
    return specs


if __name__ == "__main__":
    import sys, json
    # usage: rosmsg_decode.py <site-packages> <type> <msg.bin>
    sp, type_, path = sys.argv[1:4]
    defs = load_local_definitions(sp)
    specs = parse_definition(defs[type_], type_)
    buf = open(path, "rb").read()
    msg, used = decode(buf, specs, type_)
    flat = flatten(msg)
    for k in flat:
        if k.startswith("ldsPic.points"):
            continue
        v = flat[k]
        print("%-45s %r" % (k, v if not isinstance(v, bytes) else v.hex()))
    print("-- consumed %d of %d bytes, %d lds points" % (used, len(buf), len(msg.get("ldsPic", {}).get("points", []))))
