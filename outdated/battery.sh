#!/bin/bash
charge_level="$(cat /sys/class/power_supply/BAT0/capacity)"
ac_adapter="$(cat /sys/class/power_supply/ADP1/online)"
bat_level=$((($charge_level * 100) / 83))
if [[ ac_adapter -eq 0 ]];
then
	if [[ bat_level < 20 ]];
	then
		echo "LOW_BAT = " $bat_level "/ 100%"
	else
		echo "BAT =" $bat_level "/ 100%"
	fi
else
	echo "PWR_BAT =" $bat_level "/ 100%"
fi
