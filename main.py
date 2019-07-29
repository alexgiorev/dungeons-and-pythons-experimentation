import sys
import utils
import curses

import globvars

from game import Game

def main(stdscr):
    globvars.stdscr = stdscr
    game = Game(sys.argv[1])
    game.play()    

curses.wrapper(main)

"""
old code

games = [Game(path) for path in sys.argv[1:]]

def start():
    for game in games:
        games = current_dungeon.games
        for i, game in enumerate(games):
            status = game.play()
            if status is game.KILLED:
                if i == len(games) - 1: # if game is the last one
                    return 'lost'
                else:
                    # start the next game
                    continue
            elif status is game.WON:
                # start the next dungeon
                break
            elif status is game.QUIT:
                return 'quit'
            else:
                raise ValueError('invalid game status')
    return 'won'

def play_again():
    # used to determine if the user want to play again after
    # the whole game is over (i.e. when he wins or loses)
    
    print('press space to play again or "q" to quit')
    while True:
        answer = utils.get_char()
        if answer == ' ':
            return True
        elif answer == 'q':
            return False
        

while True:
    status = start()
    if status == 'quit':
        break
    else:
        if status == 'won':
            print('you win')
        else:
            print('you lose')
            
        if not play_again():
            break
        
"""
