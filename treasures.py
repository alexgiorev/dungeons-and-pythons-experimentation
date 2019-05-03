import random

class TreasureChest:
    def __init__(self, pos, treasures):
        self.pos = pos
        self.treasures = treasures

    def open(self):
        # returns a random treasure from self.treasures
        treasure = random.choice(self.treasures)
        return treasure

class Treasure:
    # base class for all treasures
    def give_to_actor(self, actor):
        raise NotImplementedError
    
class HealthPotion:
    def __init__(self, amount):
        self.amount = amount

    def give_to_actor(self, actor):
        actor.heal(self.amount)

class ManaPotion:
    def __init__(self, amount):
        self.amount = amount

    def give_to_actor(self, actor):
        actor.add_mana(self.amount)

class Weapon:
    def __init__(self, name, damage):
        self.name = name
        self.damage = damage

    def give_to_actor(self, actor):
        actor.equip(self)

class Spell:
    def __init__(self, name, damage, mana_cost, cast_range):
        self.name = name
        self.damage = damage
        self.mana_cost = mana_cost
        self.cast_range = cast_range

    def give_to_actor(self, actor):
        actor.learn(self)
        
def parse_dict(dct):
    # returns the treasure corresponding to @dct
    treasure_type = dct['type']
    if treasure_type == 'weapon':
        return Weapon(dct['name'], dct['damage'])
    elif treasure_type == 'spell':
        return Spell(*(dct[attr] for attr in ('name', 'damage', 'mana_cost', 'cast_range')))
    elif treasure_type == 'health_potion':
        return HealthPotion(dct['amount'])
    elif treasure_type == 'mana_potion':
        return ManaPotion(dct['amount'])
    else:
        raise ValueError(f'invalid treasure type: {treasure_type}')

default_weapon = Weapon('nil', 0)
default_spell = Spell('nil', 0, 0, 1)
