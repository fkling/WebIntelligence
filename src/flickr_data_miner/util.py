'''
Created on Apr 26, 2010

'''

class ProgressBar(object):
    """ This class returns a string that can be used to simulate a progress bar.
       
        INPUT:
            - total: The end value of the progress bar.
            - width: The width of the progress bar.
    
        EXAMPLE:
        >>> p = ProgressBar(200, 10)
        >>> p.add(100)
        >>> p
        [====>     ]
        
        >>> p = ProgressBar(10, 30)
        >>> p.add(5)
        >>> p
        [==============>               ]
        
    """
    
    def __init__(self, total, width = 100):
        self.total = total
        self.step = (1/float(self.total)) * width
        self.width = width
        self.progress = 0.0
        
    def add(self, steps=1):
        """ Advance the progress bar by <steps> of steps.
            
            INPUT:
                - steps: Number of steps.
            
            EXAMPLE:
            >>> p = ProgressBar(10, 10); p
            [          ]
            
            >>> p.add();p
            [>         ]
            
            >>> p.add(8);p
            [========> ]
            
            >>> p.add();p
            [=========>]
            
        """
        
        self.progress += steps * self.step;
        
    def __repr__(self):
        s = (int(round(self.progress))-1) * "="
        if self.progress > 0:
            s += '>'
        return ''.join(('[',s.ljust(self.width),']'))
        
def get_class( kls ):
    """ Loads a class given by a string. """
    
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m


import collections

KEY, PREV, NEXT = range(3)

class OrderedSet(collections.MutableSet):

    def __init__(self, iterable=None):
        self.end = end = [] 
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[PREV]
            curr[NEXT] = end[PREV] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:        
            key, prev, next = self.map.pop(key)
            prev[NEXT] = next
            next[PREV] = prev

    def __iter__(self):
        end = self.end
        curr = end[NEXT]
        while curr is not end:
            yield curr[KEY]
            curr = curr[NEXT]

    def __reversed__(self):
        end = self.end
        curr = end[PREV]
        while curr is not end:
            yield curr[KEY]
            curr = curr[PREV]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = next(reversed(self)) if last else next(iter(self))
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return not self.isdisjoint(other)

    def __del__(self):
        self.clear()                    # remove circular references

