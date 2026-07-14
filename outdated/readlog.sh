#!bin/bash
year="$(date +"%Y")"
month="$(date +"%m")"
day="$(date +"%d")"
chosen=""

echo ""
read -p "Today or Earlier? [1/2/Q]: " -r REPLY

if [[ $REPLY = "1" ]]
then
    echo ""
    echo "Logs from today:"
    ls --format=long /etc/logfiles/$USER/$year/$month/$day*
    read -p "Time? (H:M): " -r CHOSEN
    echo ""
    cat /etc/logfiles/$USER/$year/$month/$day-$CHOSEN.log
fi

if [[ $REPLY = "2" ]]
then
   echo ""
   ls /etc/logfiles/$USER/
   read -p "Which year?: " -r year
   echo""
   ls /etc/logfiles/$USER/$year/
   read -p "Which month?: " -r month
   echo""
   ls /etc/logfiles/$USER/$year/$month/
   read -p "Log? (D-H:M): " -r chosen
   echo""
   cat /etc/logfiles/$USER/$year/$month/$chosen.log
fi

if [[ $REPLY =~ ^[Qq]$ ]]
then
    echo "Exiting..."
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1
fi
