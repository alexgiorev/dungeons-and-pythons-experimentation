import sys
import random
import itertools

import utils
import treasures


class Actor:
    
    @property
    def is_alive(self):
        return self.health != 0

    def heal(self, healing_points):
        if not self.is_alive:
            raise ValueError('cannot heal a dead actor')
        else:
            self.health = min(self.max_health, self.health + healing_points)
            return True

    def damage(self, damage_points):
        self.health = max(0, self.health - damage_points)
        if not self.is_alive:
            self.dunmap.make_walkable(self.pos)
    
    @property
    def can_cast(self):
        return self.mana != 0
        
    def add_mana(self, mana_points):
        self.mana = min(self.max_mana, self.mana + mana_points)

    def take_mana(self, mana_points):
        self.mana = max(0, self.mana - mana_points)
                
    def equip(self, weapon):
        self.weapon = weapon

    def learn(self, spell):
        self.spell = spell

    def take_turn(self):
        self.turn_logic()
        self.add_mana(self.mana_regeneration_rate)
        # self.display.update()
        
    def move(self, direction):
        # @direction must be one of {'up', 'down', 'left', 'right'}
        new_pos = utils.move_pos(self.pos, direction)
        if not self.dunmap.can_move_to(new_pos):
            return
        if type(self.dunmap[new_pos]) is treasures.TreasureChest:
            self.dunmap[new_pos].open().give_to_actor(self)
            self.dunmap.make_walkable(new_pos)
        self.dunmap.make_walkable(self.pos)
        self.dunmap[new_pos] = self
        self.pos = new_pos

    def attack(self, by, direction):
        # @by must be in {'weapon', 'spell', 'fist'}
        # @direction must be in {'up', 'down', 'left', 'right'}
        
        if by == 'spell':
            spell = self.spell
            if self.mana < spell.mana_cost:
                return
            self.take_mana(spell.mana_cost)
            anim_posns = []
            for pos in itertools.islice(self.dunmap.relative_posns(self.pos, direction), spell.cast_range):
                anim_posns.append(pos)
                entity = self.dunmap[pos]
                if isinstance(entity, Actor):
                    entity.damage(spell.damage)
                    self.display.animate_spell(direction, anim_posns, end='actor')
                    break
                elif entity is not self.dunmap.WALKABLE:
                    self.display.animate_spell(direction, anim_posns, 'inanimate')
                    break
            else:
                self.display.animate_spell(direction, anim_posns, 'evaporate')
        else:
            # by is in {'weapon', 'fist'}
            victim_pos = next(self.dunmap.relative_posns(self.pos, direction), None)            
            if victim_pos is None:
                return            
            victim = self.dunmap[victim_pos]            
            if not isinstance(victim, Actor):
                return
            damage = self.weapon.damage if by == 'weapon' else self.fist_damage
            victim.damage(damage)
            self.display.animate_melee(victim_pos)
            
                            
class Hero(Actor):
    # a Hero has the following additional attributes:
    # - name
    # - title
    
    @property
    def known_as(self):
        return f"{self.name} the {self.title}"

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

            
    def turn_logic(self):
        command = self.read_command()
        if type(command) is str:
            # command is one of {'up', 'down', 'left', 'right'}
            self.move(command)
        else:
            # command has the form (<kind of attack>, <direction>)
            self.attack(*command)

        
class Enemy(Actor):
    # additional attributes:
    #  - last_seen: the position the hero was last seen in.
    #  - hero_direction: always equal to utils.relative_direction(self.pos, self.last_seen);
    #                    it is included only for convenience.
    
    def friendly_turn(self):
        hero_pos, hero_direction = self.search_for_hero()
        if hero_pos is None:
            self.move_to_last_seen()
        else:
            self.last_seen, self.hero_direction = hero_pos, hero_direction
            self.move_to_last_seen()

            
    def aggressive_turn(self):
        hero_pos, hero_direction = self.search_for_hero()
        if hero_pos is None:
            self.move_to_last_seen()
        else:
            self.last_seen, self.hero_direction = hero_pos, hero_direction
            if self.hero_is_in_vicinity():
                self.near_attack()
            else:
                if not self.far_attack():
                    self.move_to_last_seen()

                    
    def rabid_turn(self):
        hero_pos, hero_direction = self.search_for_hero()
        if hero_pos is None:
            if self.last_seen is None:
                self.move(random.choice(('up', 'down', 'left', 'right')))
            else:
                self.move_to_last_seen()
        else:
            self.last_seen, self.hero_direction = hero_pos, hero_direction
            if self.hero_is_in_vicinity():
                self.near_attack()
            else:
                if not self.far_attack():
                    self.move_to_last_seen()

                    
    def search_for_hero(self):
        # Returns (position, direction) of the hero,
        # or (None, None) if he can't be seen.
        # @self will only look up, down, left and right

        def try_direction(direction):
            # looks for the hero in the direction @direction
            # returns None if @enemy can't see him in that direction

            for pos in self.dunmap.relative_posns(self.pos, direction):
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
                return pos, direction

        return None, None
        

    def move_to_last_seen(self):
        if self.last_seen is None:
            return

        if self.pos == self.last_seen:
            self.last_seen = None
            self.hero_direction = None
            return

        self.move(self.hero_direction)


    def hero_is_in_vicinity(self):
        # Returns True if hero is directly above, below, to the right
        # or to the left of @self.
        pos_row, pos_col = self.pos
        hero_row, hero_col = self.last_seen
        return abs(pos_row - hero_row) <= 1 and abs(pos_col - hero_col) <= 1

    
    def near_attack(self):
        # Call only when the hero is next to @self!
        # The enemy determines the attack type dealing the most
        # damage and inflicts it on the hero.

        if self.weapon.damage >= self.spell.damage:
            if self.weapon.damage > self.fist_damage:
                by = 'weapon'
            else:
                by = 'fist'
        else:
            if (self.fist_damage >= self.spell.damage
                or self.spell.mana_cost > self.mana):
                by = 'fist'
            else:
                by = 'spell'
        self.attack(by, self.hero_direction)


    def far_attack(self):
        # Call when the hero is seen, but not immediately near @self.
        # If it is possible to cast a spell that will damage the hero,
        # this function casts the spell and returns True. Otherwise, it returns False.

        enemy_row, enemy_col = self.pos
        hero_row, hero_col = self.last_seen
        distance = abs((enemy_row - hero_row) + (enemy_col - hero_col))
        if distance <= self.spell.cast_range and self.spell.mana_cost <= self.mana:
            self.attack(by='spell', direction=self.hero_direction)
            return True
        return False


    def turn_logic(self):
        behavior_handler = getattr(self, f'{self.behavior}_turn')
        return behavior_handler()
