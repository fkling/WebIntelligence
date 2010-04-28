'''
Created on Apr 26, 2010

@author: kling
'''

from math import floor

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
        return '[' + s.ljust(self.width) + ']'
        
def get_class( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m