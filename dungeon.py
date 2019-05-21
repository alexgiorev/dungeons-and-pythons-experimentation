import json
import copy
import os
import itertools
import sys
import time
import random
import signal

import treasures
import actors
import utils

from display import Display
from matrix import Matrix
from dunmap import Dunmap

class Game:
    WON = object()
    KILLED = object()
    QUIT = object()

    @staticmethod
    def read_command():
        # returns one of:
        # {'up', 'down', 'left', 'right',
        #  ('weapon', 'up'), ..., ('weapon', 'right'),
        #  ('fist', 'up'), ..., ('fist', 'right'),
        #  ('spell', 'up', ...', ('spell', 'right'),
        #  'start-console'}
        # THIS FUNCTION DETERMINES THE USER CONTROL KEYS

        while True:
            first_char = utils.get_char()
            if first_char in '2468':
                return {'2': 'down', '4': 'left', '6': 'right', '8': 'up'}[first_char]
            elif first_char == '`':
                return 'start-console'
            elif first_char in 'wsf':
                by = {'w': 'weapon', 's': 'spell', 'f': 'fist'}[first_char]
                second_char = utils.get_char()
                if second_char not in '2468':
                    continue
                direction = {'2': 'down', '4': 'left', '6': 'right', '8': 'up'}[second_char]
                return by, direction

    
    def reinitialize(self):
        self.dungeon.init_game(self, self.reset_data)

        
    def play(self):
        def prepare():
            self.display.display()
        
        prepare()
        
        while True:
            command = self.read_command()

            if command == 'start-console':
                code = input('>>> ')
                if code == 'r':
                    self.reinitialize()
                    prepare()
                    continue
                elif code == 'q':
                    return self.QUIT
                else:
                    self.display.display()
                    continue
            else:
                self.hero.take_turn(command)
            
            # after the hero's turn, update the display
            self.display.update()
            
            if self.hero.pos == self.dunmap.gateway_pos:
                return self.WON
            
            # after the hero's turn, some enemies may be dead,
            # so stop tracking them
            self.enemies = [enemy for enemy in self.enemies if enemy.is_alive]

            for enemy in self.enemies:
                enemy.take_turn(command)

            # after enemies' turns, update the display
            self.display.update()
                
            # after the enemies' turn, the hero may have died
            if not self.hero.is_alive:
                return self.KILLED


class Dungeon:    
    @staticmethod
    def from_file(path):
        with open(path) as f:
            text = f.read()
        return Dungeon.from_dict(json.loads(text))
    
    @staticmethod
    def from_dict(dct):
        result = object.__new__(Dungeon)
        result.partial_hero_dict = dct['hero']
        result.partial_enemies_data = dct['enemies']
        result.dunmap_template = Matrix.from_lists(dct['dunmap_template'])
        result.treasures = [treasures.parse_dict(tdict)
                            for tdict in dct['treasures']]
        return result

    @property
    def partial_hero(self):
        # takes care of the attributes
        # {title, name, health, max_health, mana, max_mana, weapon, spell,
        #  fist_damage, mana_regeneration_rate}        
        # the attributes left to initialize are {pos, dunmap, display}

        dct = self.partial_hero_dict
        hero = object.__new__(actors.Hero)
        hero.name = dct['name']
        hero.title = dct['title']
        hero.health = hero.max_health = dct['health']
        hero.mana = hero.max_mana = dct['mana']
        hero.weapon = treasures.default_weapon
        hero.spell = treasures.default_spell
        hero.fist_damage = dct['fist_damage']
        hero.mana_regeneration_rate = dct['mana_regeneration_rate']
        return hero
    
    @property
    def partial_enemies(self):
        def partial_enemy(dct):
            # takes care of the attributes
            # {health, max_health, mana, max_mana, weapon, spell, fist_damage,
            #  mana_regeneration_rate, behavior, last_seen, hero_direction}
            # the attributes left to initialize are {pos, dunmap, display}

            enemy = object.__new__(actors.Enemy)
            enemy.health = enemy.max_health = dct['health']
            enemy.mana = enemy.max_mana = dct['mana']
            enemy.weapon = treasures.default_weapon
            enemy.spell = treasures.default_spell
            enemy.fist_damage = dct['fist_damage']
            enemy.mana_regeneration_rate = dct['mana_regeneration_rate']
            enemy.behavior = dct['behavior']
            enemy.last_seen = enemy.hero_direction = None
            return enemy
        
        if type(self.partial_enemies_data) is list:
            # self.partial_enemies_data is a list of enemy partial dicts
            return map(partial_enemy, self.partial_enemies_data)
        else:
            # self.partial_enemies_data is a dict of the form
            # {'all': <enemy dict>}
            dct = self.partial_enemies_data['all']
            return (partial_enemy(dct) for _ in itertools.repeat(None))


    
    @property
    def spawn_posns(self):
        # returns an iterator of @self's spawn positions
        return filter(lambda pos: self.dunmap_template[pos] == 'S',
                      self.dunmap_template.posns_lrtb)

    @property
    def games(self):
        return [self.create_game(spawn_pos) for spawn_pos in self.spawn_posns]

    def init_game(self, game, spawn_pos):
        # this function must create {hero, enemies_list, dunmap, display}
        
        # for the hero and enemies the uninitialized attributes are
        # {pos, dunmap, display}

        # for the display, we must initialize the attributes
        # {hero, dunmap, chars}

        # the dunmap must contain valid entities in it's positions and
        # must have a gateway_pos attribute (which may be None)
        
        hero = self.partial_hero
        
        partial_enemies_iter = self.partial_enemies
        enemies_list = []
        
        dunmap_template = self.dunmap_template
        dunmap = Dunmap.create_empty(nrows=dunmap_template.nrows,
                                     ncols=dunmap_template.ncols)
        
        display = object.__new__(Display)
        display.hero, display.dunmap = hero, dunmap
        
        for pos, char in dunmap_template.enumerate_lrtb():
            if char == 'S':
                if pos == spawn_pos:
                    hero.pos = pos
                    hero.dunmap = dunmap
                    hero.display = display

                    dunmap[pos] = hero
                    display.hero = hero
            elif char == 'T':
                chest = treasures.TreasureChest(pos, self.treasures)
                dunmap[pos] = chest
            elif char == 'E':
                enemy = next(partial_enemies_iter)
                enemy.pos = pos
                enemy.dunmap = dunmap
                enemy.display = display
                
                enemies_list.append(enemy)
                dunmap[pos] = enemy
            elif char == 'G':
                dunmap.gateway_pos = pos
            elif char == '#':
                dunmap[pos] = Dunmap.OBSTACLE
            elif char == '.':
                pass # dunmap already is walkable at pos because of create_empty
            else:
                raise ValueError(f'invalid character in map template: "{char}"')

        display.chars = dunmap.chars

        game.hero = hero
        game.enemies = enemies_list
        game.dunmap = dunmap
        game.display = display
        game.dungeon = self
        game.reset_data = spawn_pos
        
        
    def create_game(self, spawn_pos):
        # @spawn_pos must be one of @self's spawn positions.
        # Returns the Game instance with the hero at @spawn_pos.

        game = object.__new__(Game)
        self.init_game(game, spawn_pos)
        return game
