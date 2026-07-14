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

for i in $(seq $count); do
    echo -n "_ "
done
echo ""
read -p "Guess: " -r letter
echo "$word" | tr $letter _
