# topic /omni/work_control_req, md5 c75ebd5dda11c42d67fabcbd33a8cc70
uint32 sn

uint8 type    #work_control_type
uint8 onoff   #start=1, stop=0, 好像没用
uint32 run_sec
clean_rag_setting clean_rag
================================================================================
MSG: omni/clean_rag_setting
uint8 off = 0
uint8 on = 1
uint8 pause = 2
uint8 resume = 3

uint8 type
uint8 filling_time
uint8 pump_time
uint8 washing_time
uint8 drying_pump_time
