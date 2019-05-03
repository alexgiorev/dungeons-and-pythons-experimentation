import actors
import treasures
import utils
from matrix import Matrix


class Dunmap(Matrix):
    '''
a Dunmap is a Matrix. Each position in a Dunmap is either walkable or contains
an entity.

An entity is one of the following:
- the hero
- an enemy
- a treasure chest
- an obstacle

Positions which are walkable contain the object Dunmap.WALKABLE.
Positions at which there is an obstacle contain the object Dunmap.OBSTACLE.

One of the walkable positions may be considered the gateway position. If there
is a gateway position, self.gateway_pos will store that position. Otherwise,
self.gateway_pos will be None.

attributes: self.data, self.gateway_pos
    '''

    
    WALKABLE = '.'
    OBSTACLE = '#'

    @classmethod
    def create_empty(cls, nrows, ncols):
        # Returns a Dunmap with @nrows rows and @ncols columns where every
        # position is walkable. The gateway_pos will be None.
        result = cls.from_lists([[cls.WALKABLE for c in range(ncols)]
                                 for r in range(nrows)])
        result.gateway_pos = None
        return result
        
    
    def is_walkable(self, pos):
        return self[pos] is self.WALKABLE
    
    def make_walkable(self, pos):
        self[pos] = self.WALKABLE

    def is_obstacle(self, pos):
        return self[pos] is self.OBSTACLE
        
    def can_move_to(self, pos):
        # returns True if pos is within @self and if there is nothing
        # at that position that prevents you from moving there.
        return (self.pos_is_valid(pos)
                and (isinstance(self[pos], treasures.TreasureChest)
                     or self[pos] is self.WALKABLE))
    
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
            
        return Matrix.from_lists([[to_char((row, col)) for col in range(self.ncols)]
                                  for row in range(self.nrows)])
    
