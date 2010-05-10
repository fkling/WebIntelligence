'''
Created on Apr 17, 2010

@author: kling
'''

import os, sqlite3, itertools

class Repository(object):
    """ This class represents a collection of images and HTML pages. 
    
        INPUT:
            - dir: Directoy to load.
            - new: Indicate whether a new repository should be created.
    """
    
    
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
        
        with open(self.LAST_FILE, 'w') as f:
            f.write(self.path)
    
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
        with open(os.path.join(tag_dir, str(id) + '.jpg'), 'wb') as file:
            file.write(data)
        
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
        file = open(os.path.join(tag_dir, str(id) + '.html'), 'w')
        file.write(data)
        file.close()
        
    def get_sites(self):
        """ Iterator over all HTML pages in the repository.
               
            OUPUT:
                A tuple of format (id, tag, content) where id is the id of
                the page, tag is corresponding tag of the page and content
                is the actual HTML data.

        """
        
        l = lambda x: x.endswith('.html')
        # traverse through the tag folders
        for root, dirs, files in itertools.ifilterfalse(lambda x: x[1], os.walk(self.path)):
            tag = root.split('/')[-1]
            for file in itertools.ifilter(l,  files):
                id = file[:-5]
                with open(os.path.join(root, file)) as f:
                    content = f.read()

                yield (long(id), tag, content)
        
    @property
    def total_images(self):
        """ Total amount of images (and therefore HTML pages too). """
        
        if not self._total_images:
            self._total_images = (reduce(lambda x,y: x+y, 
                                         [len(files)/2 for root, dir, files in itertools.ifilterfalse(lambda x: x[1], os.walk(self.path))]))
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
            
            