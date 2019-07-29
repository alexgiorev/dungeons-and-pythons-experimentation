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
