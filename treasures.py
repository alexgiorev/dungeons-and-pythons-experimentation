import random

class TreasureChest:
    def __init__(self, treasures):
        self.treasures = treasures

    def open(self):
        # returns a random treasure from self.treasures
        treasure = random.choice(self.treasures)
        return treasure

class Treasure:
    # base class for all treasures
    def give_to_actor(self, actor):
        raise NotImplementedError
    
class HealthPotion(Treasure):
    def __init__(self, amount):
        self.amount = amount

    def give_to_actor(self, actor):
        actor.heal(self.amount)

class ManaPotion(Treasure):
    def __init__(self, amount):
        self.amount = amount

    def give_to_actor(self, actor):
        actor.add_mana(self.amount)

class Weapon(Treasure):
    def __init__(self, name, damage):
        self.name = name
        self.damage = damage

    def give_to_actor(self, actor):
        actor.weapon = self
        
    def __str__(self):
        return self.name

class Spell:
    def __init__(self, name, damage, mana_cost, cast_range):
        self.name = name
        self.damage = damage
        self.mana_cost = mana_cost
        self.cast_range = cast_range

    def give_to_actor(self, actor):
        actor.spell = self

    def __str__(self):
        return self.name
        
def parse_dict(dct):
    """Returns the treasure corresponding to (dct)."""
    treasure_type = dct['type']
    if treasure_type == 'weapon':
        return Weapon(dct['name'], dct['damage'])
    elif treasure_type == 'spell':
        return Spell(*(dct[attr] for attr in
                       ('name', 'damage', 'mana_cost', 'cast_range')))
    elif treasure_type == 'health_potion':
        return HealthPotion(dct['amount'])
    elif treasure_type == 'mana_potion':
        return ManaPotion(dct['amount'])
    else:
        raise ValueError(f'invalid treasure type: {treasure_type}')

default_weapon = Weapon('nil', 0)
default_spell = Spell('nil', 0, 0, 1)
defaults = (default_weapon, default_spell)
