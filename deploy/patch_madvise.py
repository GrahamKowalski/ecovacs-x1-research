"""Post-build patch for the aarch64 musl-static Valetudo/node binary.

Kernel 4.14 on the X1 makes madvise(MADV_DONTNEED) fail, and V8's
MemoryChunk::DiscardUnusedMemory CHECK-crashes when DiscardSystemPages returns
false. The libc madvise stub is:

    movz x8, #233        ; __NR_madvise  (unique in the binary)
    sxtw x2, w2
    str  x30, [sp,#-16]!
    svc  #0              ; real syscall still runs (frees pages when kernel allows)
    bl   __syscall_ret   ; <-- patched to `mov x0, #0`
    ldr  x30, [sp],#16
    ret

Patching the `bl __syscall_ret` to `mov x0,#0` makes madvise always return 0
(success) while still performing the syscall, so memory is returned to the OS
when possible and V8 never crashes. Idempotent.

    python patch_madvise.py <binary>
"""
import struct
import sys

MOVZ_X8_233 = bytes.fromhex("281d80d2")   # movz x8, #233
MOV_X0_0    = 0xD2800000                   # mov x0, #0
BL_OFFSET   = 16                            # bytes from movz to the `bl __syscall_ret`


def main(path):
    data = bytearray(open(path, "rb").read())
    n = data.count(MOVZ_X8_233)
    if n != 1:
        sys.exit(f"expected exactly one `movz x8,#233`, found {n}; aborting")
    j = data.find(MOVZ_X8_233)
    k = j + BL_OFFSET
    word = struct.unpack_from("<I", data, k)[0]
    if word == MOV_X0_0:
        print(f"already patched at {hex(k)}")
        return
    if (word >> 26) != 0b100101:   # BL opcode
        sys.exit(f"word at {hex(k)} is {word:08x}, not a BL; stub shape changed, aborting")
    struct.pack_into("<I", data, k, MOV_X0_0)
    open(path, "wb").write(data)
    print(f"patched madvise stub: {hex(k)} {word:08x} -> {MOV_X0_0:08x} (mov x0,#0)")


if __name__ == "__main__":
    main(sys.argv[1])
