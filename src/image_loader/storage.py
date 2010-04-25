'''
Created on Apr 17, 2010

@author: kling
'''

import os, sqlite3
from datetime import date

class Repository(object):
    
    def __init__(self, path, new=False):
        self.path = os.path.abspath(path)
        db_path = os.path.join(self.path, 'data.sqlite')
        if new:
            if not os.path.isdir(self.path):
                os.makedirs(self.path)        
        if not new and not os.path.isfile(db_path):
            raise Exception("Repository seems to be broken!")
        self.db_conn = sqlite3.connect(db_path)
        self._cursor = self.db_conn.cursor()
    
    @property
    def db(self):
        return self._cursor
            
            



class FileStorage(object):
    
    def __init__(self, path):
        today = date.today()
        self.dir = os.path.join(os.path.expanduser('~'), path, today.isoformat())
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
            
    def save(self, tag):
        curdir = os.getcwd()
        os.chdir(self.dir)
        if not os.path.isdir(tag.name): os.mkdir(tag.name)
        for photo in tag.get_thumbs():
            f = open(os.path.join(tag.name, photo.id + '.jpg'), 'wb')
            f.write(photo.get_image())
            f.close()
            f = open(os.path.join(tag.name, photo.id + '.html'), 'w')
            f.write(photo.get_page())
            f.close
        os.chdir(curdir)
            
            