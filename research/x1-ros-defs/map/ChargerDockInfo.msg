# topic /map/ChargerDockInfo, md5 1822602d70e60c7c106329c9490914be
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
