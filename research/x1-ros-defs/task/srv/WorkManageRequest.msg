uint8 managetype
uint8 workType
WorkData data
================================================================================
MSG: task/WorkData
CleanWorkData cleanData
ExtraWorkData extraWorkData

================================================================================
MSG: task/CleanWorkData
uint8[] ids			# areaids or ai point ids 
map/Dot[] customAreas   # two dots forms one area.  spot clean
uint8[] cycles
float32 theta       # wakeup and clean theta
uint8[] states		# state of the clean procedure.
uint8[] types       # type of furniture




================================================================================
MSG: map/Dot
float32 x
float32 y

================================================================================
MSG: task/ExtraWorkData
uint8[] ids					# checkpoint ids or patrol point ids. ai guide types.
prediction/Pose[] poses		# goto poses
RemoteMove remotes    # remote control info
uint32 tasktime       # aroma time
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
