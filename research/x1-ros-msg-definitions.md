# X1 ROS message definitions (reference)

Extracted from the firmware dump's generated Python modules
(`/usr/lib/python2.7/site-packages/<pkg>/msg/_<Name>.py`, field `_full_text`) with
`scripts/rosmsg_decode.py`. The same text is sent by each publisher in its TCPROS
header (`message_definition`), so `x1_pc_stream_rx.py` decodes live topics generically.
Nested types are listed once, after the `=====` separators, as ROS emits them.

Total definitions in the dump: 240. Listed here: the state/control types we use.

## robot/Robot

```
Header header
prediction/PredictPose pose
power/Battery battery
power/ChargeState chargestate
motor/MotorCurrent currents
rangeDet/RangeDetect rangeDetects
onOffInfo/OnOffInfo onOffInfo
onOffInfo/BumpValue[] bump
onOffInfo/DownInValue[] downin
onOffInfo/FallValue[] fall
onOffInfo/DirtBoxValue[] dirtbox
onOffInfo/CarpetValue[] carpet
onOffInfo/WaterBoxValue[] waterbox
lds/Lds ldsPic
================================================================================
MSG: std_msgs/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data 
# in a particular coordinate frame.
# 
# sequence ID: consecutively increasing ID 
uint32 seq
#Two-integer timestamp that is expressed as:
# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')
# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')
# time-handling sugar is provided by the client library
time stamp
#Frame this data is associated with
# 0: no frame
# 1: global frame
string frame_id

================================================================================
MSG: prediction/PredictPose
Pose predictPose
Pose pose
================================================================================
MSG: prediction/Pose
Header header
float32 x
float32 y
float32 theta
================================================================================
MSG: power/Battery
uint8 battery	# 0-100
uint8 isLowVoltageToPowerOff #low power signal.
================================================================================
MSG: power/ChargeState
# 0 not on charger , 1 on charger , 3 on 3d charger
uint8 isOnCharger
#enum
uint8 CHARGE_STATE_NOT_CHARGING = 0
uint8 CHARGE_STATE_NORMAL_CHARGING = 1
uint8 CHARGE_STATE_CHARGE_FULL = 2
uint8 CHARGE_STATE_CHARGE_ERROR = 3
uint8 CHARGE_STATE_CHARGE_ERROR_SWITCH_OFF = 4
uint8 chargeState
================================================================================
MSG: motor/MotorCurrent
MotorCurrentValue[] currents
================================================================================
MSG: motor/MotorCurrentValue
MotorType type
uint16 current
================================================================================
MSG: motor/MotorType
# type enum
uint8 MOTOR_TYPE_MAINBRUSH = 0
uint8 MOTOR_TYPE_LEFT_SIDEBRUSH = 1
uint8 MOTOR_TYPE_RIGHT_SIDEBRUSH = 2
uint8 MOTOR_TYPE_FAN = 3
uint8 MOTOR_TYPE_WATERPUMP = 4
uint8 TYPE_LEFTWHEEL = 5
uint8 TYPE_RIGHTWHEEL = 6
uint8 type    # TYPE
================================================================================
MSG: rangeDet/RangeDetect
Header header
RangeDetValue[] rangeDets
================================================================================
MSG: rangeDet/RangeDetValue
RangeDetType type
uint16[] values
================================================================================
MSG: rangeDet/RangeDetType
# type enum
uint8 RANGE_TYPE_FRONT_BUFFER = 0
uint8 RANGE_TYPE_SIDE_IN = 1
uint8 RANGE_TYPE_DOWN_IN = 2
uint8 RANGE_TYPE_ULTRASOUND = 3
uint8 type    # RANGE_TYPE
================================================================================
MSG: onOffInfo/OnOffInfo
OnOffSensorValue[] values
================================================================================
MSG: onOffInfo/OnOffSensorValue
# type enum
uint8 TYPE_BUMP = 0
uint8 TYPE_DOWNIN = 1
uint8 TYPE_FALL = 2
uint8 TYPE_DIRTBOX = 3
uint8 TYPE_CARPET = 4
uint8 TYPE_MOP = 5
uint8 type    # TYPE
uint8 value
================================================================================
MSG: onOffInfo/BumpValue
# type enum
uint8 TYPE_BUMP_LEFT = 0
uint8 TYPE_BUMP_RIGHT = 1
uint8 TYPE_BUMP_LDS = 2

uint8 type    # TYPE

uint8 VALUE_TRIGGER = 1
uint8 value
================================================================================
MSG: onOffInfo/DownInValue
# type enum
uint8 TYPE_DOWNIN_LEFT = 0
uint8 TYPE_DOWNIN_FRONT = 1
uint8 TYPE_DOWNIN_FRONT_RIGHT = 2
uint8 TYPE_DOWNIN_RIGHT = 3
uint8 TYPE_DOWNIN_LEFT_BACK = 4
uint8 TYPE_DOWNIN_RIGHT_BACK = 5
uint8 type    # TYPE

uint8 VALUE_TRIGGER = 1
uint8 value
================================================================================
MSG: onOffInfo/FallValue
# type enum
uint8 TYPE_FALL_LEFT = 0
uint8 TYPE_FALL_RIGHT = 1
uint8 type    # TYPE

uint8 VALUE_TRIGGER = 1
uint8 value
================================================================================
MSG: onOffInfo/DirtBoxValue
# type enum
uint8 TYPE_DIRTBOX_IN = 0
uint8 type    # TYPE

uint8 VALUE_TRIGGER = 1	# 1 represents dirtbox is SETTED.
uint8 value
================================================================================
MSG: onOffInfo/CarpetValue
# type enum
uint8 TYPE_CARPET_DETECT = 0
uint8 type    # TYPE

uint8 VALUE_TRIGGER = 1	# 1 represents carpet is detected.
uint8 value
================================================================================
MSG: onOffInfo/WaterBoxValue
# type enum
uint8 TYPE_WATERBOX_IN = 0
uint8 type    # TYPE

uint8 VALUE_WATERBOX_NOT_SET = 0	
uint8 VALUE_WATERBOX_IS_SET = 1
uint8 VALUE_ULTRA_WATERBOX_IS_SET = 2
uint8 value
================================================================================
MSG: lds/Lds
Header header
LdsPoint[] points
prediction/PredictPose ldsPose
================================================================================
MSG: lds/LdsPoint
float32 x
float32 y
float32 rho
float32 theta
float32 power
```

## power/Battery

```
uint8 battery	# 0-100
uint8 isLowVoltageToPowerOff #low power signal.
```

## power/ChargeState

```
# 0 not on charger , 1 on charger , 3 on 3d charger
uint8 isOnCharger
#enum
uint8 CHARGE_STATE_NOT_CHARGING = 0
uint8 CHARGE_STATE_NORMAL_CHARGING = 1
uint8 CHARGE_STATE_CHARGE_FULL = 2
uint8 CHARGE_STATE_CHARGE_ERROR = 3
uint8 CHARGE_STATE_CHARGE_ERROR_SWITCH_OFF = 4
uint8 chargeState
```

## power/ChargeStateCause

```
#enum ChargerCause type
uint8 CHARGE_STATE_CHANGE_CAUSE_UNKNOW=0 
uint8 CHARGE_STATE_CHANGE_CAUSE_POWER_OFF=1 
uint8 CHARGE_STATE_CHANGE_CAUSE_BUMP = 2 
uint8 CHARGE_STATE_CHANGE_CAUSE_DRAG =3 	
uint8 CHARGE_STATE_CHANGE_CAUSE_LIFT=4 

uint8 ChargerCause
```

## task/WorkState

```
uint8 worktype
uint8 state
WorkData data
uint8 workcause

================================================================================
MSG: task/WorkData
CleanWorkData cleanData
ExtraWorkData extraWorkData

================================================================================
MSG: task/CleanWorkData
uint8[] ids			# areaids or ai point ids 
map/Dot[] customAreas   # two dots forms one area.  spot clean
uint8[] cycles

uint8[] states		# state of the clean procedure.




================================================================================
MSG: map/Dot
float32 x
float32 y

================================================================================
MSG: task/ExtraWorkData
uint8[] ids					# checkpoint ids or patrol point ids. ai guide types.
prediction/Pose[] poses		# goto poses
RemoteMove remotes    # remote control info

uint8[] states		# state of the extra work procedure.

 

================================================================================
MSG: prediction/Pose
Header header
float32 x
float32 y
float32 theta
================================================================================
MSG: std_msgs/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data 
# in a particular coordinate frame.
# 
# sequence ID: consecutively increasing ID 
uint32 seq
#Two-integer timestamp that is expressed as:
# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')
# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')
# time-handling sugar is provided by the client library
time stamp
#Frame this data is associated with
# 0: no frame
# 1: global frame
string frame_id

================================================================================
MSG: task/RemoteMove
# move type.
uint8 RemoteMoveType
uint8 REMOTE_MOVE_FORWARD = 0
uint8 REMOTE_MOVE_BACKWARD = 1
uint8 REMOTE_MOVE_STOP = 2
uint8 REMOTE_MOVE_BRAKE = 3
uint8 REMOTE_MOVE_SPINLEFT = 4
uint8 REMOTE_MOVE_SPINRIGHT = 5
uint8 REMOTE_MOVE_GOTO = 6
uint8 REMOTE_MOVE_ROTATE = 7
uint8 REMOTE_MOVE_REVERSE = 8
uint8 REMOTE_MOVE_MVA_CUSTOM = 9
uint8 REMOTE_MOVE_TURN_LEFT = 10
uint8 REMOTE_MOVE_TURN_RIGHT = 11

uint16 lastTime
int16 v	
int16 w
```

## task/TaskStateReport

```
# tasktype is WorkType
uint8 tasktype
# stateType is TaskStateType
uint32 stateType
# state for every type.
uint32 state
```

## task/TaskResult

```
#typed enum
uint8 GOTO = 0
uint8 PATROL = 1
uint8 REMOTE = 2
uint8 CLEAN = 3
uint8 RETURN = 4
uint8 type

#typed enum
uint8 TASK_SUCCESS = 0
uint8 TASK_FAILD = 1
uint8 TASK_WORKING = 2
uint8 RETURN_FAILD_FIND_CHARGE = 3
uint8 RETURN_FAILD_CANNOT_FIND_CHARGE = 4

uint8 result

string data
```

## task/sleepstate

```
#type enum
uint8 SLEEPSTATE = 0

uint8 type 

#type enum
uint8 RobotSleep = 1
uint8 RobotWakeUp = 0   
uint8 RobotLowPowerOff = 2   

uint8 event 
```

## task/TaskControl

```
uint8 type
uint8 control
string data
```

## task/WorkType

```
uint8 WORK_TYPE_AUTO_CLEAN = 0			# auto clean all room
uint8 WORK_TYPE_AREA_CLEAN = 1			# area clean for specific rooms
uint8 WORK_TYPE_CUSTOM_CLEAN = 2		# custom clean for specific square
uint8 WORK_TYPE_CIRTLE_CLEAN = 3		# circle clean for edge
uint8 WORK_TYPE_AI_COVER_CLEAN = 4		# cover unclean area with ai recogonized points
uint8 WORK_TYPE_RETURN = 5				# return to charger
uint8 WORK_TYPE_GOTO = 6				# goto point
uint8 WORK_TYPE_IDLE = 7				# idle state
uint8 WORK_TYPE_RELOCATION = 8			# relocation work.
uint8 WORK_TYPE_REMOTE_CONTROL = 9		# remote 
uint8 WORK_TYPE_AI_GUIDE = 10			# ai guide.
uint8 WORK_TYPE_CHECK_POINT = 11		# check point 
uint8 WORK_TYPE_PATROL = 12				# patrol work.
uint8 WORK_TYPE_AUTO_COLLECT_DIRT = 13  # manual collect dirt
uint8 WORK_TYPE_CUSTOM_WORK = 254		# custom work test.
uint8 WORK_TYPE_UNKNOWN = 255			# unknown type
```

## task/WorkStateType

```
uint8 WORK_STATE_TYPE_IDLE = 0
uint8 WORK_STATE_TYPE_RUNNING = 1
uint8 WORK_STATE_TYPE_PAUSED = 2
```

## task/TaskStateType

```
# task state type for task state report msg.
# expand task state type enum for extra task state.

uint32 TASK_STATE_TYPE_RETURN_ENTER_TO_FRONT_OF_CHARGER = 0
uint32 TASK_STATE_TYPE_CLEAN_FINISH_SINGLE_AREA = 1
uint32 TASK_STATE_TYPE_CLEAN_AI_DETECT_TO_CONTROL_BRUSH = 2		# value 1 is on , 0 is off.
uint32 TASK_STATE_TYPE_CLEAN_ROBOT_IS_STUCK = 3		# value 1 is on.
uint32 TASK_STATE_TYPE_OFF_ROBOT_WATER_PUMP = 4		# value 1 is on.
```

## task/WorkCauseType

```
uint8 WORK_CAUSE_TYPE_NONE = 0			
uint8 WORK_CAUSE_TYPE_MANUAL = 1
uint8 WORK_CAUSE_TYPE_SCHEDULE = 2
uint8 WORK_CAUSE_TYPE_WORK_COMPLETE = 3
uint8 WORK_CAUSE_TYPE_LOW_BATTERY = 4
uint8 WORK_CAUSE_TYPE_BLOCK_TIME = 5
uint8 WORK_CAUSE_TYPE_CONTINUE = 6
uint8 WORK_CAUSE_TYPE_WORK_INTERRUPT = 7
uint8 WORK_CAUSE_TYPE_ALERT = 8
uint8 WORK_CAUSE_TYPE_APP_MANUAL = 9
```

## task/WorkControlType

```
uint8 WORK_CONTROL_TYPE_START = 0			# start
uint8 WORK_CONTROL_TYPE_STOP = 1			# stop task
uint8 WORK_CONTROL_TYPE_PAUSE = 2			# pause
uint8 WORK_CONTROL_TYPE_RESUME = 3			# resume
uint8 WORK_CONTROL_TYPE_MOD	= 4				# mod task content
```

## task/RobotManageType

```
uint8 ROBOT_MANAGE_TYPE_RESET_MAP = 0
uint8 ROBOT_MANAGE_TYPE_SLEEP_STATE = 1
uint8 ROBOT_MANAGE_TYPE_CONTINUOUS_WORK = 2
uint8 ROBOT_MANAGE_TYPE_VALID_POSE = 3
uint8 ROBOT_MANAGE_TYPE_DOCK_TYPE = 4
uint8 ROBOT_MANAGE_TYPE_COLLECT_STATE = 5
```

## onOffInfo/WaterBoxStateReport

```
# type enum
uint8 TYPE_WATERBOX_TEST = 0
uint8 type    # TYPE

uint8 VALUE_WATERBOX_START = 0	
uint8 VALUE_WATERBOX_STOP = 1

uint8 value
```

## onOffInfo/OnOffInfo

```
OnOffSensorValue[] values
================================================================================
MSG: onOffInfo/OnOffSensorValue
# type enum
uint8 TYPE_BUMP = 0
uint8 TYPE_DOWNIN = 1
uint8 TYPE_FALL = 2
uint8 TYPE_DIRTBOX = 3
uint8 TYPE_CARPET = 4
uint8 TYPE_MOP = 5
uint8 type    # TYPE
uint8 value
```

## onOffInfo/LackofWaterValue

```
# type enum
uint8 TYPE_WATERBOX_IN = 0
uint8 type    # TYPE

uint8 VALUE_HAS_WATER = 0
uint8 VALUE_LACK_OF_WATER = 1
uint8 value
```

## setting/FanMode

```
uint8 FAN_MODE_LOW = 0
uint8 FAN_MODE_HIGH = 1
uint8 FAN_MODE_HIGH_HIGH = 2

uint8 mode
uint8 isSilent
```

## setting/WaterLevel

```
uint8 WATER_LEVEL_LOW = 0
uint8 WATER_LEVEL_MIDDLE = 1
uint8 WATER_LEVEL_HIGH = 2
uint8 WATER_LEVEL_ULTRAHIGH = 3

uint8 level
```

## setting/MopMode

```
uint8 MOP_MODE_EFFECTIVE = 0
uint8 MOP_MODE_PERFORMANCE = 1

uint8 type
```

## lifespan/lifespan

```
#type enum
uint8 LIFESPANCHANGE = 0
uint8 LIFESPANTIMEOUT = 1
uint8 type    #LIFE_TYPE

#type enum
uint8 LIFE_MAIN_BRUSH = 0
uint8 LIFE_SIDE_BRUSH = 1
uint8 LIFE_HEPA = 2
uint8 DUST_HEPA_TIMEOUT = 3
uint8 DUSTER_TIMEOUT = 4
uint8 event   # LIFE_EVENT
```

## map/ChargerDockInfo

```
uint8 CHARGER_DOCK_UPDATE = 0
uint8 CHARGER_DOCK_REPORT = 1
uint8 CHARGER_DOCK_RESET = 2
uint8 CHARGER_DOCK_GET = 3 
uint8 CHARGER_DOCK_UPDATE_FRONT = 4
uint8 CHARGER_DOCK_UPDATE_FRONT_3D = 5
uint8 CHARGER_DOCK_UPDATE_3D = 6

uint8 docktype
uint8 info
uint32 mapid
uint8 hasGotDock
uint8 hasfindDock
uint8 hasFront3DDock
uint8 hasGot3DDock
ChargerDock Dockfront
ChargerDock dock
ChargerDock finddock
ChargerDock T3DDockfront
ChargerDock T3Ddock


================================================================================
MSG: map/ChargerDock
float32 x
float32 y
float32 theta
```

## alert/Alerts

```
AlertInfo[] alerts
================================================================================
MSG: alert/AlertInfo
# alert type.
uint8 type

# 0 means idle , 1 means triggered.
uint8 state 
```

## alert/DirtboxAndFall

```
DirtboxAndFallinfo[] DirtboxAndFall

================================================================================
MSG: alert/DirtboxAndFallinfo
#type enum
uint8 ALERT_DIRT_BOX_STATE = 0
uint8 ALERT_FALL_ERROR = 1
uint8 alert_type

#value 1 has alert,0 cancel
uint8 value
```

## key/Key

```
#type enum
uint8 KEY_TYPE_AUTO = 0
uint8 KEY_TYPE_RESET = 1
uint8 type    #KEY_TYPE

#type enum
uint8 KEY_EVENT_CLICK = 0
uint8 KEY_EVENT_DOUBLE_CLICK = 1
uint8 KEY_EVENT_LONG_PRESSED = 2
uint8 KEY_EVENT_LONG_LONG_PRESSED = 3
uint8 KEY_EVENT_PRESSED_DOWN = 4
uint8 KEY_EVENT_PRESSED_UP = 5
uint8 event   # KEY_EVENT
```

## ota/OtaState

```
uint8 type
# ota state , 0 is off , 1 is on.
uint8 state
```

## Types captured live from publisher headers (not in the dump's python modules)

Saved by `scripts/x1_pc_dump_defs.py` into `x1-ros-defs/<pkg>/<Name>.msg` (all 25 streamed types).

## task/CurrentArea (live)

```
# topic /task/CurrentArea, md5 13b1211c737358f0ee2c333d91f4f543
int32 curareaid	# current cleaning area id
```

## task/omnireport (live)

```
# topic /task/omnireport, md5 992ce8a1687cec8c8bd883ec73ca41d1
string data
```

## onOffInfo/MopStateReport (live)

```
# topic /onOffInfo/MopStateReport, md5 b5aa231d498376b6f3fbd48f76065309
MopState[] states
================================================================================
MSG: onOffInfo/MopState
# type enum
uint8 TYPE_LEFT_MOP = 0
uint8 TYPE_RIGHT_MOP = 1
uint8 type    # TYPE

uint8 VALUE_MOP_NOT_SET = 0	
uint8 VALUE_MOP_IS_SET = 1
uint8 value
```

## onOffInfo/WaterLevel (live)

```
# topic /onOffInfo/WaterLevel, md5 4aa05aceec8ce5a53adee36f0b6cb3dc
# type enum
uint8 TYPE_WATERBOX_IN = 0
uint8 type    # TYPE

uint8 VALUE_EMPTY = 0
uint8 VALUE_HAS_WATER = 1
uint8 VALUE_FULL_OF_WATER = 2
uint8 value
```

## setting/OnlyMopMode (live)

```
# topic /setting/OnlyMopMode, md5 c09060c25bdd401f851f57c30cb859e4
uint8 MODE_ON = 0
uint8 MODE_OFF = 1

uint8 ModeOnOff
```

## omni/key (live)

```
# topic /omni/key, md5 58e5d6e91fcbf35ff9f7e7437416d96a
# type enum
uint8 auto_button = 0
uint8  recall_button = 1
uint8  clean_button = 2
uint8  child_lock_button = 3
uint8 key

# type enum
uint8  click = 0
uint8  double_click = 1
uint8  long_pressed = 2
uint8  long_long_pressed = 3
uint8  press_down = 4
uint8  press_up = 5

uint8 value
```

## alert/DirtboxAndFall (live)

```
# topic /alert/DirtboxAndFall, md5 45312c794ecf39bac8386da021926dbd
DirtboxAndFallinfo[] DirtboxAndFall

================================================================================
MSG: alert/DirtboxAndFallinfo
#type enum
uint8 ALERT_DIRT_BOX_STATE = 0
uint8 ALERT_FALL_ERROR = 1
uint8 alert_type

#value 1 has alert,0 cancel
uint8 value
```

## power/ChargeStateCause (live)

```
# topic /power/ChargeStateCause, md5 95e24bc0c13bd09a6606edfdc9a0bc59
#enum ChargerCause type
uint8 CHARGE_STATE_CHANGE_CAUSE_UNKNOW=0 
uint8 CHARGE_STATE_CHANGE_CAUSE_POWER_OFF=1 
uint8 CHARGE_STATE_CHANGE_CAUSE_BUMP = 2 
uint8 CHARGE_STATE_CHANGE_CAUSE_DRAG =3 	
uint8 CHARGE_STATE_CHANGE_CAUSE_LIFT=4 

uint8 ChargerCause
```

## task/sleepstate (live)

```
# topic /task/sleepstate, md5 9dd1a1814e7e93d60a193a4cf5886c71
#type enum
uint8 SLEEPSTATE = 0

uint8 type 

#type enum
uint8 RobotSleep = 1
uint8 RobotWakeUp = 0   
uint8 RobotLowPowerOff = 2   

uint8 event 
```
