#!bin/bash
date="$(date +"%Y.%m.%d_@%kh%Mm%Ss")"
oldmot="$(cat /etc/motd)"
echo ""
echo "-----"
echo "Today's date : " $date
echo "Last login @ : " $oldmot
echo "-----"
echo $date [$USER] > /etc/motd
echo ""
echo "Greetings," [$USER]
echo ""

exit

