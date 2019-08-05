import sys
import curses
import os

import globvars
import utils

from game import Game


def dunscreen():
    dungeons = sorted(os.listdir(globvars.DUNDIR))
    while True:
        choice = utils.List.get(dungeons)
        if choice is None:
            break
        path = f'{globvars.DUNDIR}/{choice}'
        play(path)


def play(path):
    game = Game(path)
    outcome = game.play()
    pass


def main(stdscr):
    globvars.stdscr = stdscr

    while True:
        choice = utils.List.get(['start', 'exit'])
        if choice is None or choice == 'exit':
            return
        elif choice == 'start':
            dunscreen()
        else:
            raise ValueError(f'Invalid choice: "{choice}"')


curses.wrapper(main)

