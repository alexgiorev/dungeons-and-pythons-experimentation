import json
import itertools
import os
import copy
import sys
import time

import random
import treasures
import actors
import utils

class Map:
    # attributes:
    #   - self.matrix: a list of lists representing the map.
    #     Each entry in self.matrix is one of:
    #         - an Actor or TreasureChest instance
    #         - Map.WALKABLE or Map.OBSTACLE
    #   - self.gateway_pos: the coordinates of the gateway in the map

    # COMPARE THESE WITH THE == OPERATOR NOT WITH is
    # is MAY NOT WORK WHEN RESTARTING THE GAME AND COPYING THE MAP
    WALKABLE = 'w'
    OBSTACLE = 'o'
        
    @property
    def nrows(self):
        return len(self.matrix)

    @property
    def ncols(self):
        return len(self.matrix[0])

    def cleanup_at(self, pos):
        self[pos] = self.WALKABLE

    def pos_is_valid(self, pos):
        row, col = pos
        return row >= 0 and row < self.nrows and col >= 0 and col < self.ncols
        
    def can_move_to(self, pos):
        # returns True if pos is within @self and if there is nothing
        # at that position that prevents you from moving there.
        return (self.pos_is_valid(pos)
                and (isinstance(self[pos], treasures.TreasureChest)
                     or self[pos] is self.WALKABLE))

    def is_walkable(self, pos):
        return self[pos] == self.WALKABLE

    def make_walkable(self, pos):
        self[pos] = self.WALKABLE

    def is_obstacle(self, pos):
        return self[pos] == self.OBSTACLE
    
    @property
    def chars(self):
        # returns a character matrix represented as a list of lists
        WALKABLE = '.'
        OBSTACLE = '#'        
        GATEWAY = 'G'
        HERO = 'H'
        ENEMY = 'E'
        TREASURE_CHEST = 'T'

        def to_char(pos):
            entity = self[pos]
            if self.is_obstacle(pos):
                return OBSTACLE                
            elif type(entity) is actors.Hero:
                return HERO
            elif type(entity) is actors.Enemy:
                return ENEMY
            elif pos == self.gateway_pos:
                return GATEWAY
            elif self.is_walkable(pos):
                return WALKABLE
            elif type(entity) is treasures.TreasureChest:
                return TREASURE_CHEST
            else:
                raise ValueError(f'invalid entity at {pos}: {entity}')            
            
        return [[to_char((row, col)) for col in range(self.ncols)]
                for row in range(self.nrows)]

    def __getitem__(self, pos):
        # pos must be a pair (<row-index>, <column-index>)
        row, col = pos
        return self.matrix[row][col]

    def __setitem__(self, pos, value):
        # pos must be a pair (<row-index>, <column-index>)
        row, col = pos
        self.matrix[row][col] = value
    
    def relative_posns(self, pos, direction):
        while True:
            pos = utils.move_pos(pos, direction)
            if self.pos_is_valid(pos):
                yield pos
            else:
                break

    @property
    def posns_lrtb(self):
        # lrtb stands for left right top bottom.
        # returns an iterator of the positions of self in the order left to right, top to bottom
        for rowi in range(self.nrows):
            for coli in range(self.ncols):
                yield (rowi, coli)
    
class Game:
    WON = object()
    KILLED = object()
    QUIT = object()
    
    def __init__(self, hero, enemies, map):
        self.hero = hero
        self.enemies = enemies
        self.map = map
        self.map_chars = map.chars

        # needed for restarting the game
        self.initial_state = copy.deepcopy(self.__dict__)

    @staticmethod
    def read_command():
        # returns one of:
        # {'up', 'down', 'left', 'right',
        #  ('weapon', 'up'), ..., ('weapon', 'right'),
        #  ('fist', 'up'), ..., ('fist', 'right'),
        #  ('spell', 'up', ...', ('spell', 'right')}
        # THIS FUNCTION DETERMINES THE USER CONTROL KEYS

        while True:
            first_char = utils.get_char()
            if first_char in '2468':
                return {'2': 'down', '4': 'left', '6': 'right', '8': 'up'}[first_char]
            elif first_char in 'wsf':
                by = {'w': 'weapon', 's': 'spell', 'f': 'fist'}[first_char]
                second_char = utils.get_char()
                if second_char not in '2468':
                    continue
                direction = {'2': 'down', '4': 'left', '6': 'right', '8': 'up'}[second_char]
                return by, direction


    def actor_move(self, actor, direction):
        # @direction must be one of {'up', 'down', 'left', 'right'}
    
        new_pos = utils.move_pos(actor.pos, direction)
        if not self.map.can_move_to(new_pos):
            return
        if type(self.map[new_pos]) is treasures.TreasureChest:
            self.map[new_pos].open().give_to_actor(actor)
            self.map.cleanup_at(new_pos)
        self.map.make_walkable(actor.pos)
        self.map[new_pos] = actor
        actor.pos = new_pos

    def actor_attack(self, actor, by, direction):
        # @by must be in {'weapon', 'spell', 'fist'}
        # @direction must be in {'up', 'down', 'left', 'right'}

        SECS = 0.075 # needed for animation
        HIT = '*'
        
        def animate_spell_cast(posns, end):
            # end must be in {'actor', 'inanimate', 'evaporate'}
            # all posns until the last one must be walkable
            symbol = {'up': '^', 'down': 'v', 'left': '<', 'right': '>'}[direction]
            for pos in posns[:-1]:
                r, c = pos
                old_char = self.map_chars[r][c]
                self.map_chars[r][c] = symbol
                self.display()
                time.sleep(SECS)
                self.map_chars[r][c] = old_char
                
            r, c = posns[-1]
            if end == 'actor':
                self.map_chars[r][c] = HIT
            elif end == 'evaporate':
                print('evaporate')
                self.map_chars[r][c] = symbol
            else:
                pass
            self.display()
            time.sleep(SECS)

        def animate_melee(victim_pos):
            # call only if weapon or fist attack was actually made
            r, c = victim_pos
            self.map_chars[r][c] = HIT
            self.display()
            time.sleep(SECS)
        
        if by == 'spell':
            spell = actor.spell            
            if actor.mana < spell.mana_cost:
                return
            actor.take_mana(spell.mana_cost)
            anim_posns = []
            for pos in itertools.islice(self.map.relative_posns(actor.pos, direction), spell.cast_range):
                anim_posns.append(pos)
                entity = self.map[pos]
                if isinstance(entity, actors.Actor):
                    entity.damage(spell.damage)
                    self.remove_body_if_dead(entity)
                    animate_spell_cast(anim_posns, end='actor')
                    break
                elif not self.map.is_walkable(pos):
                    animate_spell_cast(anim_posns, 'other')
                    break
            else:
                animate_spell_cast(anim_posns, 'evaporate')
        else:
            # by is in {'weapon', 'fist'}
            victim_pos = next(self.map.relative_posns(actor.pos, direction), None)
            
            if victim_pos is None:
                return
            
            victim = self.map[victim_pos]
            
            if not isinstance(victim, actors.Actor):
                return

            damage = actor.weapon.damage if by == 'weapon' else actor.fist_damage
            victim.damage(damage)
            self.remove_body_if_dead(victim)
            animate_melee(victim_pos)

    def remove_body_if_dead(self, actor):
        if not actor.is_alive:
            self.map.cleanup_at(actor.pos)

    def hero_turn(self):
        hero = self.hero
        command = self.read_command()
        if type(command) is str:
            # command is one of {'up', 'down', 'left', 'right'}
            self.actor_move(hero, command)
        else:
            # command has the form (<kind of attack>, <direction>)
            self.actor_attack(hero, *command)
        # at end of every turn, regenerate some mana
        hero.give_mana(hero.mana_regeneration_rate)


    def enemy_turn(self, enemy):
        def search_for_hero():
            # returns the position of the hero, or None if he can't be seen
            # @enemy will only look up, down, left and right

            def try_direction(direction):
                # looks for the hero in the direction @direction
                # returns None if @enemy can't see him in that direction

                for pos in self.map.relative_posns(enemy.pos, direction):
                    if type(self.map[pos]) is actors.Hero:
                        return pos
                    elif not self.map.is_walkable(pos):
                        # something blocks @self's view
                        return None
                return None

            for direction in ('up', 'down', 'left', 'right'):
                pos = try_direction(direction)
                if pos is not None:
                    return pos, direction

            return None, None

        def move_to_last_seen():
            if enemy.last_seen is None:
                return

            if enemy.pos == enemy.last_seen:
                enemy.last_seen = None
                enemy.hero_direction = None
                return

            self.actor_move(enemy, enemy.hero_direction)
            
        def hero_is_in_vicinity():
            # Returns True if hero is directly above, below, to the right
            # or to the left of @enemy.
            pos_row, pos_col = enemy.pos
            hero_row, hero_col = enemy.last_seen
            return abs(pos_row - hero_row) <= 1 and abs(pos_col - hero_col) <= 1

        def near_attack():
            # Call only when the hero is next to @enemy!
            # The enemy determines the attack type dealing the most
            # damage and inflicts it on the hero.
            
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

        def far_attack():
            # Call when the hero is seen, but no immediately near @enemy.
            # If it is possible to cast a spell that will damage the hero,
            # this function casts the spell and returns True. Otherwise, it returns False.
            
            enemy_row, enemy_col = enemy.pos
            hero_row, hero_col = enemy.last_seen
            distance = abs((enemy_row - hero_row) + (enemy_col - hero_col))
            if distance <= enemy.spell.cast_range and enemy.spell.mana_cost <= enemy.mana:
                self.actor_attack(enemy, by='spell', direction=enemy.hero_direction)
                return True
            return False

        behavior_handlers = {}
        
        def behavior(name):
            def decorator(func):
                behavior_handlers[name] = func
                return func
            return decorator

        @behavior("friendly")
        def handler():
            hero_pos, hero_direction = search_for_hero()
            if hero_pos is None:
                move_to_last_seen()
            else:
                enemy.last_seen, enemy.hero_direction = hero_pos, hero_direction
                move_to_last_seen()

        @behavior("aggresive")
        def handler():
            hero_pos, hero_direction = search_for_hero()
            if hero_pos is None:
                move_to_last_seen()
            else:
                enemy.last_seen = hero_pos
                enemy.hero_direction = hero_direction
                if hero_is_in_vicinity():
                    near_attack()
                else:
                    if not far_attack():
                        move_to_last_seen()

        @behavior("rabid")
        def handler():
            hero_pos, hero_direction = search_for_hero()
            if hero_pos is None:
                if enemy.last_seen is None:
                    self.actor_move(enemy, random.choice(('up', 'down', 'left', 'right')))
                else:
                    move_to_last_seen()
            else:
                enemy.last_seen = hero_pos
                enemy.hero_direction = hero_direction
                if hero_is_in_vicinity():
                    near_attack()
                else:
                    if not far_attack():
                        move_to_last_seen()


        behavior_handler = behavior_handlers.get(enemy.behavior)
        if behavior_handler is None:
            raise ValueError(f'enemy has invalid behavior: "{enemy.behavior}"')

        behavior_handler()
                    
    def reset(self):
        # resets the state of @self to what it was at the beginning
        cpy = copy.deepcopy(self.initial_state)
        self.__dict__.update(cpy)

    def display(self):
        def display_hero():
            print(f'health: {self.hero.health}')
            print(f'mana: {self.hero.mana}')
            print(f'weapon: {self.hero.weapon.name}')
            print(f'spell: {self.hero.spell.name}')
            print()

        def display_map():
            lines = (''.join(line) for line in self.map_chars)
            print('\n'.join(lines))
            print()
        
        os.system('clear')
        display_hero()
        display_map()

    def refresh_display(self):
        self.map_chars = self.map.chars
        self.display()
        
    def play(self):
        while True:
            try:
                self.refresh_display()
                self.hero_turn()
                self.refresh_display()

                if self.hero.pos == self.map.gateway_pos:
                    return self.WON

                # after the hero's turn, some enemies may be dead, so stop tracking them
                self.enemies = [enemy for enemy in self.enemies if enemy.is_alive]

                if not self.enemies:
                    return self.WON

                for enemy in self.enemies:
                    self.enemy_turn(enemy)

                # after the enemies' turn, the hero may have died
                if not self.hero.is_alive:
                    return self.KILLED
                
            except KeyboardInterrupt:
                command = input('>>> ')
                if command == 'q':
                    return self.QUIT
                elif command == 'r':
                    self.reset()
                    continue
                else:
                    # unknown command
                    continue

class Dungeon:
    # attributes:
    #  - hero_partial_dict
    #  - enemies_data: used to create the enemy_partial_dicts iterator
    #  - map_template
    #  - treasures
    
    @staticmethod
    def from_file(path):
        with open(path) as f:
            text = f.read()
        return Dungeon.from_dict(json.loads(text))
    
    @staticmethod
    def from_dict(dct):
        result = object.__new__(Dungeon)
        result.hero_partial_dict = dct['hero']
        result.enemy_data = dct['enemies']
        result.map_template = dct['map_template']
        result.treasures = [treasures.parse_dict(tdict) for tdict in dct['treasures']]
        return result

    @property
    def spawn_posns(self):
        # returns an iterator of @self's spawn positions
        nrows = len(self.map_template)
        ncols = len(self.map_template[0])
        for rowi in range(nrows):
            for coli in range(ncols):
                if self.map_template[rowi][coli] == 'S':
                    yield (rowi, coli)

    @property
    def games(self):
        return [self.create_game(spawn_pos) for spawn_pos in self.spawn_posns]

    @property
    def enemy_partial_dicts(self):        
        if type(self.enemy_data) is list:
            return iter(self.enemy_data)
        return itertools.repeat(self.enemy_data['all'])
    
    def create_game(self, spawn_pos):
        # @spawn_pos must be one of @self's spawn positions.
        # Returns the Game instance with the hero at @spawn_pos

        enemy_partial_dicts = self.enemy_partial_dicts
        hero = None
        enemies = []
        
        # map initialization
        the_map = object.__new__(Map)
        the_map.matrix = [list(row) for row in self.map_template]
        the_map.gateway_pos = None

        # replace characters in the_map with the correct objects
        for pos in the_map.posns_lrtb:
            char = the_map[pos]
            if char == 'S':
                if pos == spawn_pos:
                    hero_dict = copy.deepcopy(self.hero_partial_dict)
                    hero_dict['pos'] = pos
                    hero = actors.Hero.from_dict(hero_dict)
                    the_map[pos] = hero
                else:
                    the_map[pos] = Map.WALKABLE
            elif char == 'T':
                chest = treasures.TreasureChest(pos, self.treasures)
                the_map[pos] = chest
            elif char == 'E':
                enemy_dict = next(enemy_partial_dicts)
                enemy_dict['pos'] = pos
                enemy = actors.Enemy.from_dict(enemy_dict)
                enemies.append(enemy)
                the_map[pos] = enemy
            elif char == 'G':
                the_map.gateway_pos = pos
                the_map[pos] = Map.WALKABLE
            elif char == '#':
                the_map[pos] = Map.OBSTACLE
            elif char == '.':
                the_map[pos] = Map.WALKABLE
            else:
                raise ValueError(f'invalid character in map template: "{char}"')
        return Game(hero, enemies, the_map)
