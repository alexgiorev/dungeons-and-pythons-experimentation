import utils

class Matrix:
    # attributes: self.data is a list of lists
    
    @classmethod
    def from_lists(cls, lists):
        # @lists must be a list of lists, all with the same number of elements
        result = object.__new__(cls)
        result.data = [sublist[:] for sublist in lists]
        return result

    
    @property
    def nrows(self):
        return len(self.data)

    
    @property
    def ncols(self):
        return len(self.data[0])

    
    def pos_is_valid(self, pos):
        row, col = pos
        return row >= 0 and row < self.nrows and col >= 0 and col < self.ncols

    
    def __getitem__(self, pos):
        # pos must be a pair (<row-index>, <column-index>)
        row, col = pos
        return self.data[row][col]

    
    def __setitem__(self, pos, value):
        # pos must be a pair (<row-index>, <column-index>)
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
        # lrtb stands for left right top bottom.
        # returns an iterator of the positions of self in the order left to right, top to bottom
        for rowi in range(self.nrows):
            for coli in range(self.ncols):
                yield (rowi, coli)


    @property
    def rows(self):
        # returns an iterator of lists representing @self's rows
        return (sublist[:] for sublist in self.data)

    def enumerate_lrtb(self):
        return ((pos, self[pos]) for pos in self.posns_lrtb)
