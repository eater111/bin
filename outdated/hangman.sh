#!/bin/bash
guesses=""
possible="8"
letter=""
word=""
echo ""
read -p "Word? (Keep Hidden!): " -r word
clear
echo "[HANGMAN v1.0]"
echo "Guesses left:" $guesses / $possible
count=${#word}
#echo $test
for i in $(seq $count); do
    echo -n "_ "
done
read -p "Guess?: " -r letter
test="$(sed 's/[^$letter]//g' ${#word} | awk '{ print length }')"
echo "_ _ _ _ _" | sed s/./$letter/$test
echo ""
