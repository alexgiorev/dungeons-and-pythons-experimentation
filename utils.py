# this module contains utility functions

def get_char():
    # got this from here: https://stackoverflow.com/a/36974338/4180854
    # for POSIX-based systems (with termios & tty support)
    
    import tty, sys, termios

    fd = sys.stdin.fileno()
    oldSettings = termios.tcgetattr(fd)

    try:
        tty.setcbreak(fd)
        answer = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)

    return answer

def relative_direction(pos1, pos2):
    # returns the direction in which one would have to go from @pos1 to get to @pos2
    # the possible return values are 'up', 'down', 'left' and 'right'.
    # if @pos1 and @pos2 are not on the same horizontal or vertical line
    # or if pos1 == pos2, a ValueError is raised

    if pos1 == pos2:
        raise ValueError(f'given equal positions: {pos1}')
    
    row1, col1 = pos1
    row2, col2 = pos2

    if row1 == row2:
        return 'left' if col1 - col2 > 0 else 'right'
    elif col1 == col2:
        return 'up' if row1 - row2 > 0 else 'down'
    else:
        raise ValueError('self.pos and self.last_pos are not on '
                         'the same vertical nor horizontal line')

def move_pos(pos, direction):
    # direction should be in {'up', 'down', 'left', 'right'}
    dx_dy = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}[direction]
    return (pos[0] + dx_dy[0], pos[1] + dx_dy[1])
