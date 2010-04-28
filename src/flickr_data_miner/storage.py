'''
Created on Apr 17, 2010

@author: kling
'''

import os, sqlite3
from datetime import date

class Repository(object):
    """ This class represents a collection of images and HTML pages. """
    
    
    LAST_FILE = os.path.expanduser("~/.flickr_analyzer_last_rep")
    
    def __init__(self, dir, new=False):
        self.path = os.path.abspath(dir)
        db_path = os.path.join(self.path, 'data.sqlite')
        if new:
            if not os.path.isdir(self.path):
                os.makedirs(self.path)        
        if not new and not os.listdir(self.path):
            raise Exception("Repository is empty!")
        self.db_conn = sqlite3.connect(db_path)
        self._total_images = 0
        
    def set_last(self):
        """ Set the current repository as last accessed repository. """
        
        f = open(self.LAST_FILE, 'w')
        f.write(self.path)
        f.close()
    
    @classmethod
    def get_last(cls):
        """ Get the last accessed repository path. """
        
        f = open(Repository.LAST_FILE)
        result = f.read()
        f.close()
        return result
        
    def add_image(self, tag, id, data):
        """ Add an image to the repository.
        
            INPUT:
                - tag: The tag the image was fetched for.
                - id: The id of the image.
                - data: Image data.       
        """
        
        tag_dir = os.path.join(self.path, tag)
        if not os.path.isdir(tag_dir):
            os.mkdir(tag_dir)
        file = open(os.path.join(tag_dir, id + '.jpg'), 'wb')
        file.write(data)
        file.close()
        
    def add_site(self, tag, id, data):
        """ Add a HTML page to the repository.
        
            INPUT:
                - tag: The tag the page was fetched for.
                - id: The id of the page.
                - data: HTML data.       
        """
        
        tag_dir = os.path.join(self.path, tag)
        if not os.path.isdir(tag_dir):
            os.mkdir(tag_dir)
        file = open(os.path.join(tag_dir, id + '.html'), 'w')
        file.write(data)
        file.close()
        
    def get_sites(self):
        """ Iterator over all HTML pages in the repository.
               
            OUPUT:
                A tuple of format (id, tag, content) where id is the id of
                the page, tag is corresponding tag of the page and content
                is the actuall HTML data.

        """
        
        current = os.getcwd()
        os.chdir(self.path)
        for tag in [d for d in os.listdir(self.path) if os.path.isdir(d)]:
            for site in [f for f in os.listdir(tag) if f.endswith('.html')]:
                id = site[:-5]
                f = open(os.path.join(tag, site))
                content = f.read()
                f.close()
                yield (long(id), tag, content)
        os.chdir(current)
        
    @property
    def total_images(self):
        """ Total amount of images (and therefor HTML pages too). """
        
        current = os.getcwd()
        os.chdir(self.path)
        if not self._total_images:
            self._total_images = (reduce(lambda x,y: x+y, 
                                         [len(os.listdir(os.path.join(self.path, tag)))/2 
                                          for tag in os.listdir(self.path) 
                                          if os.path.isdir(os.path.join(self.path, tag))]))
        os.chdir(current)
        return self._total_images
    
    def begin_transaction(self):
        """ Begins a database transaction. 
            Tweaks some settings to increase performance. 
        
        """
        
        self.db_conn.execute('PRAGMA synchronous = OFF')
        self.db_conn.execute('PRAGMA journal_mode = MEMORY')
        self.db_conn.execute('BEGIN')
        
    def commit(self):
        """ Commits the current DB transaction. """
        
        self.db_conn.commit()
        self.db_conn.execute('PRAGMA synchronous = FULL')
        self.db_conn.execute('PRAGMA journal_mode = 0')
    
    def close(self):
        """ Closes the current DB connection. """
        
        self.db_conn.commit()
        self.db_conn.close()
            
            