import os
import time
from matrix import Matrix

class Display:
    '''

    attributes: dunmap, hero, chars

    chars is a Matrix of characters

    '''

    def update(self):
        # updates @self's information and refreshes the display
        
        self.chars = self.dunmap.chars
        self.refresh()

        
    def refresh(self):
        def display_hero():
            print(f'health: {self.hero.health}')
            print(f'mana: {self.hero.mana}')
            print(f'weapon: {self.hero.weapon.name}')
            print(f'spell: {self.hero.spell.name}')
            print()

        def display_map():
            lines = (''.join(line) for line in self.chars.rows)
            print('\n'.join(lines))
            print()
        
        os.system('clear')
        display_hero()
        display_map()
        
        
    def animate_spell(self, direction, posns, end):        
        # end must be in {'actor', 'inanimate', 'evaporate'}
        # all posns until the last one must be walkable
        
        HIT = '*'
        SECS = 0.075
        
        symbol = {'up': '^', 'down': 'v', 'left': '<', 'right': '>'}[direction]
        for pos in posns[:-1]:
            oldchar = self.chars[pos]
            self.chars[pos] = symbol
            self.refresh()
            time.sleep(SECS)
            self.chars[pos] = oldchar
            self.refresh()

        pos = posns[-1]
        oldchar = self.chars[pos]
        if end == 'actor':
            self.chars[pos] = HIT
        elif end == 'evaporate':
            print('evaporate')
            self.chars[pos] = symbol
        else:
            pass
        self.refresh()
        time.sleep(SECS)
        self.chars[pos] = oldchar
        self.refresh()


    def animate_melee(self, victim_pos):
        # call only if weapon or fist attack was actually made
        HIT = '*'
        SECS = 0.075

        oldchar = self.chars[victim_pos]
        self.chars[victim_pos] = HIT
        self.refresh()
        time.sleep(SECS)
        self.chars[victim_pos] = oldchar
        self.refresh()
