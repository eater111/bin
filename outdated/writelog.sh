#!bin/bash
current_time="$(date +"%Y.%m.%d_@%kh%Mm%Ss")"
current_bat="$($HOME/bin/battery.sh)"
current_text=""
year="$(date +"%Y")"
month="$(date +"%m")"
day="$(date +"%d")"
hour="$(date +"%H")"
minute="$(date +"%M")"
REPLY=""

# determine filename
sudo mkdir -p /etc/logfiles/$USER/$year/$month/
sudo touch /etc/logfiles/$USER/$year/$month/$day-$hour:$minute.log
current_log="/etc/logfiles/$USER/$year/$month/$day-$hour:$minute.log"
sudo chmod a+rw $current_log

# initial info and variables stored
echo $current_time
echo $current_bat
echo [$USER]
echo ""
echo "Writing to:" $current_log
read -p "Input: " -r current_text
echo ""
read -p "Write log? [Y/n]: " -r REPLY

# responsible for writing the data into the file
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "---START OF TRANSMISSION---" >> $current_log
    echo "" >> $current_log
    echo $current_time >> $current_log
    echo $current_bat >> $current_log
    echo "User:" [$USER] >> $current_log
    echo "" >> $current_log
    echo ">" $current_text >> $current_log
    echo "" >> $current_log
    echo "---END OF TRANSMISSION---" >> $current_log
    echo "" >> $current_log
    echo "Log successfully written @" $current_log
    echo ""
fi

# responsible for exitting the process when replied "N"
if [[ $REPLY =~ ^[Nn]$ ]]
then
    echo ""
    echo "Exiting..."
    echo ""
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1
fi
