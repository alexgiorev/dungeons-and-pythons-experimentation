import sys
import curses

import globvars


def relative_direction(pos1, pos2):
    """Returns the direction in which one would have to go from (pos1) to get to
     (pos2) the possible return values are 'up', 'down', 'left' and 'right'.  If
     (pos1) and (pos2) are not on the same horizontal or vertical line or if
     (pos1 == pos2), None is returned."""

    if pos1 == pos2:
        return None
    
    row1, col1 = pos1
    row2, col2 = pos2
    
    if row1 == row2:
        return 'left' if col1 - col2 > 0 else 'right'
    elif col1 == col2:
        return 'up' if row1 - row2 > 0 else 'down'
    else:
        return None

    
def move_pos(pos, direction):
    if direction not in {'up', 'down', 'left', 'right'}:
        raise ValueError(f'Invalid direction: direction')
    
    dx_dy = {'up': (-1, 0),
             'down': (1, 0),
             'left': (0, -1),
             'right': (0, 1)}[direction]
    
    return (pos[0] + dx_dy[0], pos[1] + dx_dy[1])


logfile = 'log'
def log(text):
    with open(logfile, 'a') as f:
        print(text, file=f)
        
# truncate 
with open(logfile, 'w'):
    pass

####################
"""
Attributes used:
- items: the list of strings which are the item names
- base
"""

class List:
    # A non-empty list of item names (strings)
    items = None
    
    # The index of item that is at the top of the displayed list
    base = None
    
    # The index of the currently selected item on the screen. The index of the
    # actual item is (List.items) is (List.base + List.index)
    index = None
    
    # The screen where the list will be displayed.
    # Important: scr.keypad must be True.
    scr = None


    def get(items, scr=None):
        curses.curs_set(False)
        
        if not items:
            raise ValueError(f'(items) cannot be empty. Given {items}')
        
        List.scr = globvars.stdscr if scr is None else scr
        List.items = items
        List.base = 0
        List.index = 0

        # helper attributes
        List.nrows, List.ncols = List.scr.getmaxyx()
        
        return List.main()
        

    def main():
        List.show()
        while True:
            key = List.scr.getkey().lower()
            if key == 'q':
                return None
            elif key == 'key_up':
                List.move('up')
            elif key == 'key_down':
                List.move('down')
            elif key == '\n':
                item = List.items[List.base + List.index]
                List.end()
                return item
            List.show()


    def move(direc):
        rindex = List.index + List.base
        if direc == 'down':
            if rindex == len(List.items) - 1:
                curses.beep()
            else:
                if List.index == List.nrows - 1:
                    List.base += 1
                else:
                    List.index += 1
        elif direc == 'up':
            if rindex == 0:
                curses.beep()
            else:
                if List.index == 0:
                    List.base -= 1
                else:
                    List.index -= 1
        else:
            raise ValueError(f'Invalid direction: "{direc}"')


    def end():
        List.scr.clear(); List.scr.refresh()
        List.scr = List.items = List.base = List.index = None


    def at(index):
        return List.items[List.base + index]

    
    def show():
        List.scr.clear()
        for r in range(min(List.nrows, len(List.items))):
            if r == List.index:
                List.scr.addstr(r, 0, List.at(r), curses.A_REVERSE)
            else:
                List.scr.addstr(r, 0, List.at(r))
        List.scr.refresh()


if __name__ == '__main__':
    def main(scr):
        curses.curs_set(False)
        return List.get([f'choice{k}' for k in range(80)], scr)
    print(curses.wrapper(main))
