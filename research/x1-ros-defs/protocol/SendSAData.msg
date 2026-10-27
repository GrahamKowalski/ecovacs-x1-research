# topic /protocol/SendSAData, md5 e1fec84077b768d5901783b5bfe7d778
byte mainCmd
byte subCmd
uint16 size
byte[] data

#type enum
uint8 MSG_TYPE_REQUEST = 0
uint8 MSG_TYPE_RESPONSE = 1
uint8 MSG_TYPE_REPORT = 2
uint8 type    #MSG_TYPE
