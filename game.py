import json
import copy
import os
import itertools
import sys
import time
import random
import signal
import curses

import treasures
import utils
import globvars


class Matrix:
    """
    A matrix class. Internally, it is represented as a list of lists. It's only
    attribute is (self.data)."""

    def __init__(self, ioi):
        """(ioi) must be an iterable of iterables. The inner iterables must all
        have the same length, otherwise a ValueError is raised."""
        
        self.data = [list(iterable) for iterable in ioi]
        if len(set(map(len, self.data))) != 1:
            raise ValueError('Not all iterables havet the same length.')

        self.nrows = len(self.data)
        self.ncols = len(self.data[0])

        
    def pos_is_valid(self, pos):
        row, col = pos
        return row >= 0 and row < self.nrows and col >= 0 and col < self.ncols

    
    def __getitem__(self, pos):
        """(pos) must be a pair (<row-index>, <column-index>)."""
        row, col = pos
        return self.data[row][col]

    
    def __setitem__(self, pos, value):
        """(pos) must be a pair (<row-index>, <column-index>)."""
        row, col = pos
        self.data[row][col] = value

        
    def relative_posns(self, pos, direction):
        while True:
            pos = utils.move_pos(pos, direction)
            if self.pos_is_valid(pos):
                yield pos
            else:
                break


    @property
    def posns_lrtb(self):
        """lrtb stands for left right top bottom.  Returns an iterator of the
        positions of self in the order left to right, top to bottom."""
        for rowi in range(self.nrows):
            for coli in range(self.ncols):
                yield (rowi, coli)


    @property
    def rows(self):
        # returns an iterator of lists representing @self's rows
        return (sublist[:] for sublist in self.data)

    
    def enumerate_lrtb(self):
        return ((pos, self[pos]) for pos in self.posns_lrtb)

    
class Dunmap(Matrix):
    """
    A Dunmap is a Matrix representing the state of a dungeon. Each position in a
    Dunmap is either walkable or contains an entity.

    An entity is one of the following:
    - the hero
    - an enemy
    - a treasure chest
    - an obstacle

    Positions which are walkable contain the object Dunmap.WALKABLE.  Positions
    at which there is an obstacle contain the object Dunmap.OBSTACLE.

    One of the walkable positions may be considered the gateway position. If
    there is a gateway position, self.gateway_pos will store that
    position. Otherwise, self.gateway_pos will be None.

    Apart from the attributes coming from Matrix, a Dunmap has one additional
    attribute: (self.gateway_pos) which indicates the position of the
    gateway. If there is no gateway, (self.gateway_pos is None).
    """
    
    WALKABLE = '.'
    OBSTACLE = '#'

    def __init__(self, nrows, ncols):
        """Returns a Dunmap with @nrows rows and @ncols columns where every
        position is walkable. The gateway_pos of the result will be None."""

        super().__init__([[self.WALKABLE for c in range(ncols)]
                          for r in range(nrows)])
        self.gateway_pos = None
        
    
    def is_walkable(self, pos):
        return self[pos] is self.WALKABLE

    
    def make_walkable(self, pos):
        self[pos] = self.WALKABLE

        
    def is_obstacle(self, pos):
        return self[pos] is self.OBSTACLE

    
    def can_move_to(self, pos):
        """Returns True if pos is within @self and if there is nothing at that
        position that prevents you from moving there."""
        
        return (self.pos_is_valid(pos)
                and (isinstance(self[pos], treasures.TreasureChest)
                     or self[pos] is self.WALKABLE))

    
    @property
    def chars(self):
        """Returns a Matrix, which is the character representation of (self)."""
        return [''.join(self.chat(row, col) for col in range(self.ncols))
                for row in range(self.nrows)]


    def chat(self, r, c):
        """Returns the character code of the entity at the position (pos)."""

        WALKABLE = '.'
        OBSTACLE = '#'
        GATEWAY = 'G'
        HERO = 'H'
        ENEMY = 'E'
        TREASURE_CHEST = 'T'

        pos = (r, c)
        entity = self[pos]
        if self.is_obstacle(pos):
            return OBSTACLE                
        elif type(entity) is Hero:
            return HERO
        elif type(entity) is Enemy:
            return ENEMY
        elif pos == self.gateway_pos:
            return GATEWAY
        elif self.is_walkable(pos):
            return WALKABLE
        elif type(entity) is treasures.TreasureChest:
            return TREASURE_CHEST
        else:
            raise ValueError(f'invalid entity at {pos}: {entity}')

    
class Actor:
    """
    All actors have the following attributes:
    * health
    * max_health
    * mana
    * max_mana
    * mana_regen: the amount of mana restored at each turn
    * fist_damage
    * weapon
    * spell
    * pos: the coordinates (row, column) of the actor in the dunmap
    """
    
    @property
    def is_alive(self):
        return self.health != 0

    def heal(self, healing_points):
        if not self.is_alive:
            raise ValueError('cannot heal a dead actor')
        else:
            self.health = min(self.max_health, self.health + healing_points)

    def damage(self, damage_points):
        self.health = max(0, self.health - damage_points)        
            
    def add_mana(self, mana_points):
        self.mana = min(self.max_mana, self.mana + mana_points)

    def reduce_mana(self, mana_points):
        self.mana = max(0, self.mana - mana_points)

        
class Hero(Actor):
    pass


class Enemy(Actor):
    """
    Additional attributes:
    - last_seen: the position the hero was last seen in.
    - behavior
    """

    @property
    def hero_direction(self):
        if self.last_seen is None:
            return None
        return utils.relative_direction(self.pos, self.last_seen)


class Game:
    WON = object()
    KILLED = object()
    QUIT = object()

    class Exc(Exception):
        pass
    
    ########################################
    # constructor
    
    def __init__(self, filename):
        with open(filename) as f:
            dct = json.load(f)
    
        self.validate(dct)

        # needed for eventual state resets (see Game.reset())
        self.prows, self.pcols = dct['dims']
        self.phero = dct['hero']
        self.penemies = dct['enemies']
        self.ptreasures = dct['treasures']
        self.pobposns = dct['obstacles']
        self.ptcposns = dct['treasure-chests']
        self.pgatepos = dct['gateway']

        self.reset()

        
    def validate(self, dct):
        # hero, enemies, dunmap, treasures
        pass

    
    def reset(self):
        """Returns (self) back to it's initial state. The state is represented
        by the attributes {hero enemies dunmap}."""
        
        self.dunmap = Dunmap(self.prows, self.pcols)
        
        # Initialize the hero
        hero, phero = Hero(), self.phero
        hero.health = hero.max_health = phero['max_health']
        hero.mana = hero.max_mana = phero['max_mana']
        hero.mana_regen = phero['mana_regen']
        hero.fist_damage = phero['fist_damage']
        hero.weapon, hero.spell = treasures.defaults
        hero.pos = phero['pos']
        self.hero = hero
        self.dunmap[hero.pos] = hero

        # Initialize the enemies
        self.enemies = []
        for penemy in self.penemies:
            enemy = Enemy()
            enemy.health = enemy.max_health = penemy['max_health']
            enemy.mana = enemy.max_mana = penemy['max_mana']
            enemy.mana_regen = penemy['mana_regen']
            enemy.fist_damage = penemy['fist_damage']
            enemy.weapon, enemy.spell = treasures.defaults
            enemy.behavior = penemy['behavior']
            enemy.pos = penemy['pos']
            enemy.last_seen = None
            self.enemies.append(enemy)
            self.dunmap[enemy.pos] = enemy

        treasure_col = [treasures.parse_dict(dct) for dct in self.ptreasures]
            
        for tcpos in self.ptcposns:
            self.dunmap[tcpos] = treasures.TreasureChest(treasure_col)

        for obpos in self.pobposns:
            self.dunmap[obpos] = self.dunmap.OBSTACLE

        self.dunmap.gateway_pos = tuple(self.pgatepos)

        
    ########################################
    # hero functions
    
    def hero_turn(self, command):
        hero = self.hero
        if type(command) is str:
            # command is one of {'up', 'down', 'left', 'right'}
            self.actor_move(hero, command)
        else:
            # command has the form (<kind of attack>, <direction>)
            self.actor_attack(hero, *command)
        hero.add_mana(hero.mana_regen)

    ########################################
    # enemy turn
    
    def enemy_friendly_turn(self, enemy):
        hero_pos = self.find_hero(enemy)
        if hero_pos is None:
            self.move_to_last_seen(enemy)
        else:
            enemy.last_seen = hero_pos
            self.move_to_last_seen(enemy)


    def enemy_aggressive_turn(self, enemy):
        hero_pos  = self.find_hero(enemy)
        if hero_pos is None:
            self.move_to_last_seen(enemy)
        else:
            enemy.last_seen = hero_pos
            if self.hero_in_vicinity(enemy):
                self.enemy_near_attack(enemy)
            else:
                if not self.enemy_far_attack(enemy):
                    self.move_to_last_seen(enemy)


    def enemy_rabid_turn(self, enemy):
        hero_pos = self.find_hero(enemy)
        if hero_pos is None:
            if enemy.last_seen is None:
                direction = random.choice(('up', 'down', 'left', 'right'))
                self.actor_move(enemy, direction)
            else:
                self.move_to_last_seen(enemy)
        else:
            enemy.last_seen = hero_pos
            if self.hero_in_vicinity(enemy):
                self.enemy_near_attack(enemy)
            else:
                if not self.enemy_far_attack(enemy):
                    self.move_to_last_seen(enemy)


    def find_hero(self, enemy):
        """Returns the the hero position if he can be seen by (enemy), otherwise
        None."""

        def try_direction(direction):
            """Looks in (direction) for the hero. Returns None if (enemy) can't
            see him in that direction."""

            for pos in self.dunmap.relative_posns(enemy.pos, direction):
                entity = self.dunmap[pos]
                if type(entity) is Hero:
                    return pos
                elif entity is not self.dunmap.WALKABLE:
                    # something blocks @self's view
                    return None
            return None

        for direction in ('up', 'down', 'left', 'right'):
            pos = try_direction(direction)
            if pos is not None:
                return pos

        return None


    def move_to_last_seen(self, enemy):
        if enemy.last_seen is None:
            return

        if enemy.pos == enemy.last_seen:
            enemy.last_seen = None
        else:
            self.actor_move(enemy, enemy.hero_direction)


    def hero_in_vicinity(self, enemy):
        """Returns True if hero is directly above, below, to the right or to the
        left of (enemy)."""
        pos_row, pos_col = enemy.pos
        hero_row, hero_col = self.hero.pos
        return abs(pos_row - hero_row) <= 1 and abs(pos_col - hero_col) <= 1


    def enemy_near_attack(self, enemy):
        """Call only when the hero is next to (enemy). The enemy determines the
        attack type dealing the most damage and inflicts it on the hero."""

        if enemy.weapon.damage >= enemy.spell.damage:
            if enemy.weapon.damage > enemy.fist_damage:
                by = 'weapon'
            else:
                by = 'fist'
        else:
            if (enemy.fist_damage >= enemy.spell.damage
                or enemy.spell.mana_cost > enemy.mana):
                by = 'fist'
            else:
                by = 'spell'
        self.actor_attack(enemy, by, enemy.hero_direction)


    def enemy_far_attack(self, enemy):
        """Call when the hero is seen, but not immediately near (enemy).  If it is
         possible to cast a spell that will damage the hero, this function casts
         the spell and returns True. Otherwise, it returns False."""

        enemy_row, enemy_col = enemy.pos
        hero_row, hero_col = enemy.last_seen
        distance = abs((enemy_row - hero_row) + (enemy_col - hero_col))
        if (distance <= enemy.spell.cast_range and
                enemy.spell.mana_cost <= enemy.mana):
            self.actor_attack(enemy, by='spell', direction=enemy.hero_direction)
            return True
        return False

    
    def enemy_turn(self, enemy):
        behavior = getattr(self, f'enemy_{enemy.behavior}_turn')
        behavior(enemy)
        enemy.add_mana(enemy.mana_regen)
        
    ########################################
    # general actor functions
    
    def actor_move(self, actor, direction):
        new_pos = utils.move_pos(actor.pos, direction)        
        if not self.dunmap.can_move_to(new_pos):
            return
        entity = self.dunmap[new_pos]        
        if type(entity) is treasures.TreasureChest: 
            entity.open().give_to_actor(actor)
            self.dunmap.make_walkable(new_pos)
        self.dunmap.make_walkable(actor.pos)
        self.dunmap[new_pos] = actor
        actor.pos = new_pos


    def actor_attack(self, actor, by, direction):
        """(by) must be in {'weapon', 'spell', 'fist'}. (direction) must be in
        {'up', 'down', 'left', 'right'}."""

        if by not in {'weapon', 'spell', 'fist'}:
            raise ValueError(f'Invalid attack method: {by}')
        
        victim = None # needed later to clean up if dead
        
        if by == 'spell':
            spell = actor.spell
            if actor.mana < spell.mana_cost:
                return
            actor.reduce_mana(spell.mana_cost)
            anim_posns = []
            for pos in itertools.islice(self.dunmap.relative_posns(actor.pos, direction), spell.cast_range):
                anim_posns.append(pos)
                entity = self.dunmap[pos]
                if isinstance(entity, Actor):
                    victim = entity
                    victim.damage(spell.damage)
                    self.animate_spell(direction, anim_posns, end='hit-actor')
                    break
                elif entity is not self.dunmap.WALKABLE:
                    self.animate_spell(direction, anim_posns, end='hit-inanimate')
                    break
            else:
                self.animate_spell(direction, anim_posns, end='evaporate')
        else:
            # by is in {'weapon', 'fist'}
            damage = actor.weapon.damage if by == 'weapon' else actor.fist_damage
            victim_pos = next(self.dunmap.relative_posns(actor.pos, direction), None)            
            if victim_pos is None:
                return            
            victim = self.dunmap[victim_pos]
            if not isinstance(victim, Actor):
                return            
            victim.damage(damage)
            self.animate_melee(victim_pos)
            
        if victim is not None and not victim.is_alive:
            self.dunmap.make_walkable(victim.pos)

    ########################################
    # command reader
    
    def read_command(self):
        """Returns one of:
        {'up', 'down', 'left', 'right',
         ('weapon', 'up'), ..., ('weapon', 'right'),
         ('fist', 'up'), ..., ('fist', 'right'),
         ('spell', 'up'), ..., ('spell', 'right'), 'start-console'}"""

        directions = {key: key[4:] for key in
                      ('key_up', 'key_down', 'key_left', 'key_right')}
        
        while True:
            first_key = self.dunmap_scr.getkey().lower()
            if first_key in directions:
                return directions[first_key]
            elif first_key == '`':
                return 'start-console'
            elif first_key in 'wsf':
                by = {'w': 'weapon', 's': 'spell', 'f': 'fist'}[first_key]
                second_key = self.dunmap_scr.getkey().lower()
                if second_key not in directions:
                    continue
                return by, directions[second_key]

    ########################################
    # console
            
    def console(self):
        """Handles console commands."""
        raise NotImplementedError

    ########################################
    # initialization
    
    def init_screens(self):
        """Assumes curses has already been initialized at this
        point. Initializes the attributes (self.hero_scr, self.dunmap_scr,
        self.console_scr)"""
        
        globvars.stdscr.clear()

        curses.curs_set(False)
        
        self.hero_scr = curses.newwin(5, curses.COLS, 0, 0)
        self.hero_scr.keypad(True)

        row = self.hero_scr.getbegyx()[0] + self.hero_scr.getmaxyx()[0]
        self.dunmap_scr = curses.newwin(self.dunmap.nrows, curses.COLS, row, 0)
        self.dunmap_scr.keypad(True)

        row = self.dunmap_scr.getbegyx()[0] + self.dunmap_scr.getmaxyx()[0]
        self.console_scr = curses.newwin(1, curses.COLS, row, 0)
        self.console_scr.keypad(True)


    def deinit_screens(self):        
        for scr in (self.hero_scr, self.dunmap_scr, self.console_scr):
            scr.keypad(False)
        curses.curs_set(True)


    ########################################
    # display functions
    
    def draw(self):
        """Assumes the screens have been initialized. Updates the screens'
        contents to reflect (self)'s state."""

        for scr in (self.hero_scr, self.dunmap_scr, self.console_scr):
            scr.clear()
            
        self.hero_scr.addstr(0, 0, f'health: {self.hero.health}')
        self.hero_scr.addstr(1, 0, f'mana: {self.hero.mana}')
        self.hero_scr.addstr(2, 0, f'weapon: {self.hero.weapon}')
        self.hero_scr.addstr(3, 0, f'spell: {self.hero.spell}')
        self.hero_scr.noutrefresh()
        
        for i, row in enumerate(self.dunmap.chars):
            self.dunmap_scr.addstr(i, 0, row)
        self.dunmap_scr.noutrefresh()

        self.console_scr.clear()
        
        curses.doupdate()
    
        
    def animate_spell(self, direction, posns, end):
        """(end) must be in {'hit-actor', 'hit-inanimate', 'evaporate'}. All
        (posns) until the last one must be walkable."""

        HIT = '*'
        
        symbol = {'up': '^', 'down': 'v', 'left': '<', 'right': '>'}[direction]
        for r, c in posns[:-1]:
            self._flash(r, c, symbol)
            
        r, c = posns[-1]
        endsym = HIT if end == 'hit-actor' else symbol
        self._flash(r, c, endsym)


    def _flash(self, r, c, symbol):
        SECS = 0.075
        oldch = self.dunmap.chat(r, c)
        self.dunmap_scr.addstr(r, c, symbol)
        self.dunmap_scr.refresh()
        time.sleep(SECS)
        self.dunmap_scr.addstr(r, c, oldch)
        self.dunmap_scr.refresh()

        
    def animate_melee(self, pos):
        HIT = '*'
        self._flash(*pos, HIT)

        
    ########################################
    # play
    
    def play(self):
        try:
            self.init_screens()
            self.draw()
            return self._main_loop()
        finally:
            self.deinit_screens()


    def _main_loop(self):
        while True:
            try:
                utils.log(f'the health is {self.hero.health}')
                command = self.read_command()
                if command == 'start-console':
                    self.console()
                else:
                    self.hero_turn(command)
                # after the hero's turn, update the display
                self.draw()
                if self.hero.pos == self.dunmap.gateway_pos:
                    return self.WON
                # after the hero's turn, some enemies may be dead, so stop
                # tracking them
                self.enemies = [enemy for enemy in self.enemies if enemy.is_alive]
                if not self.enemies:
                    return self.WON
                for enemy in self.enemies:
                    self.enemy_turn(enemy)
                # after enemies' turns, update the display
                self.draw()
                # after the enemies' turn, the hero may have died
                if not self.hero.is_alive:
                    return self.KILLED
            except Game.Exc:
                raise NotImplementedError
