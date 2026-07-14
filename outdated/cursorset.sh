#!/bin/bash
cursorname=""
echo ""
echo "-SET XCURSOR-"
echo ""
echo "["
find /usr/share/icons ~/.local/share/icons ~/.icons -type d -name "cursors"
echo "]"
echo ""
read -p "What's the cursor's name?: " -r cursorname
read -p "!WARNING! THIS WILL OVERWRITE! Confirm? [Y/n]: " -r REPLY

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo ""
    echo "-WRITTEN-"
    echo ""
    echo "# written to ~/.icons/default/index.theme"
   echo "[icon theme]" | sudo tee ~/.icons/default/index.theme
   echo "Inherits=$cursorname" | sudo tee -a ~/.icons/default/index.theme
   echo ""
   echo "# written to ~/.config/gtk-3.0/settings.ini"
   echo "[Settings]" | sudo tee ~/.config/gtk-3.0/settings.ini
   echo "gtk-cursor-theme-name=$cursorname" | sudo tee -a ~/.config/gtk-3.0/settings.ini
   echo ""
   echo "-WRITTEN-"
   echo ""
fi

if [[ $REPLY =~ ^[Nn]$ ]]
then
    echo ""
    echo "Exiting. . ."
    echo ""
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1
fi
