# topic /power/ChargeState, md5 3f40efefe99d0b54d25afc2ed5523fc0
# 0 not on charger , 1 on charger , 3 on 3d charger
uint8 isOnCharger
#enum
uint8 CHARGE_STATE_NOT_CHARGING = 0
uint8 CHARGE_STATE_NORMAL_CHARGING = 1
uint8 CHARGE_STATE_CHARGE_FULL = 2
uint8 CHARGE_STATE_CHARGE_ERROR = 3
uint8 CHARGE_STATE_CHARGE_ERROR_SWITCH_OFF = 4
uint8 chargeState
