'''
Created on Apr 26, 2010

@author: kling
'''

from math import floor

class ProgressBar(object):
    def __init__(self, total):
        self.total = total
        self.step = (1/float(self.total)) * 100.0
        self.width = 100
        self.progress = 0.0
        
    def add(self, steps=1):
        self.progress += steps * self.step;
        
    def __repr__(self):
        s = '[' + (int(floor(self.progress)) * "=") + '>'
        return s.ljust(self.width+1) + ']'
        