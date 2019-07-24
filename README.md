To read more about this game, see [this](https://github.com/HackBulgaria/Programming-101-Python-2019/tree/master/week07/02.Dungeons-and-Pythons)

# How to start the game

The general way to start is `py main.py <dungeon-file>+`

For example: `py main.py dungeons/dun1 dungeons/dun2 dungeons/dun3` or equivalently `py main.py dungeons/dun[1-3]` starts the game with three dungeons.

# Console commands

You can start the console by pressing backquote (the key below ESC), at which point a prompt `>>>` will appear. Just type some characters and press ENTER.

The 'q' command is used to exit the game. The 'r' command is used to restart the current dungeon.

# Controls

You can move around using the numpad keys: `8` for up, `2` for down, `4` for left, `6` for right.

To use your fists to do damage, press `f` followed by the desired direction. For example, pressing `f` followed by `2` uses the hero's fists to hit downwards. Similarly, `4` hits to the left. Attacking with spells and weapons is similar, except that the keys 's' and 'w' are used, respectively. So to cast a spell upwards, type `s` followed by `8`. To use the weapon downwards, type `w` followed by `2`.

# Example Levels

I have made some example dungeons which you can try out. They are in the `dungeons` directory. For example, you can try Dungeon3 by typing `py main.py dungeons/dun3`.

## Dungeon1

This is copied from the HackBulgaria problem description linked above.

## Dungeon2

This one is tricky because it only takes a single hit to kill you.

## Dungeon3

In this dungeon, the enemies are "friendly". This means they will not hit you, but they will still follow you if they see you. The goal is to not get suffocated. If you do become suffocated, and wish to retry the level, just enter the console by pressing backquote, and enter the restart command 'r'.

## Dungeon4

You, aswell as the enemies, have a treasure chest infront of you, which will give you a spell called 'awp', which has a relatively long range and deals 100 damage. Try to kill all of the enemies before reaching the gateway.
