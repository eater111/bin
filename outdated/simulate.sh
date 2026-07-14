#!/bin/bash
echo ""
echo "[ - - - - ]"
ls /usr/lib/xscreensaver
echo "[ - - - - ]"
echo ""
read -p "File to Simulate: " -r REPLY
exec /usr/lib/xscreensaver/$REPLY
