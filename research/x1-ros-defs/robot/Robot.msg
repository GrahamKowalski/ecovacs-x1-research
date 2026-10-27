# topic /robot/Robot, md5 5cfb7b142ed6323fe50812ffb59c30d4
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
