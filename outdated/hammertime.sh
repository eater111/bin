#!/bin/bash
victim=''
echo ""
read -p "Drop The Hammer!: " -r victim
sudo ipset add blacklist $victim
sudo iptables -A OUTPUT -d $victim -j DROP
sudo ipset save > /etc/ipset.conf
echo "Have a great day $victim"!
