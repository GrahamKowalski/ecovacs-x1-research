# topic /map/AppControlMap, md5 df23594301761c176aaeecfa8a1f2748
ManipulateMap controlMap


================================================================================
MSG: map/ManipulateMap
uint32 manipulateId
# ManipulateMapType
uint8 manipulateType
# saveMapType
uint8 mapType
# ManipulateMapType , all , slammap etc.
uint8 subMapType
# map is or not complete
uint8 isComplete
# rename mapname by user 
string name
# curmap clean count
uint8 cleancount
# copy or save from memory
uint8 savemode
