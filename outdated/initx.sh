#!/bin/bash
files="$(ls $HOME/xinitrc/)"
REPLY=""
PS3="Select your File: "
echo "-XORG STARTUP SCRIPT v1.0-"
echo ""
echo "Choose your XINITRC File (Xconfig)"
select filename in ${files};
do
    echo ""
    echo "You selected [$filename]"
    sleep 3
    echo "Initializing $HOME/xinitrc/$filename. . ."
    sleep 1
    $(XINITRC=$HOME/xinitrc/$filename startx)
    break
done
