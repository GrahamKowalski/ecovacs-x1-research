# topic /protocol/RecvSAData, md5 a9c65577af24aae7e55ec2003ec0a690
byte mainCmd
byte subCmd
uint16 size
byte[] data

uint32 id

#type enum
uint8 MSG_TYPE_REQUEST = 0
uint8 MSG_TYPE_RESPONSE = 1
uint8 MSG_TYPE_REPORT = 2
uint8 type    #MSG_TYPE
