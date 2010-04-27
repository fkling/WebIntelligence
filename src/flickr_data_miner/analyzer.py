'''
Created on Apr 19, 2010

@author: kling
'''
import cmd, lxml, sys, datetime

class Analyzer(cmd.Cmd, object):
    '''
    No documentation available.
    '''
    CREATE_TABLES = None
    TABLES = None
    
    def __init__(self, repository):
        '''
        Constructor
        '''
        self.init()
        self.repository = repository
        self.name = 'Unnamed analyzer'
        cmd.Cmd.__init__(self)
        
    def init(self):
        pass
    
    
    def create_table(self):
        if not self.CREATE_TABLES or not self.TABLES:
            raise NotImplementedError('A CREATE_TABLES attribute must be implemented')
        for create in self.CREATE_TABLES:
            self.repository.execute_statement(create, autocommit=False)
    
    def parse_file(self, id, tag, data):
        pass
    
    def initialize(self):
        self.create_table()
        counter = 0
        total = self.repository.total_images
        for id, tag, data in self.repository.get_sites():
            self.parse_file(id, tag, data)
            counter +=1;
            sys.stdout.write("%i of %i images processed \r" % (counter, total))
            sys.stdout.flush()
        print '\nDone.'
        self.repository.commit()
            
    def remove(self):
        for table in self.TABLES:
            self.repository.execute_statement('DROP TABLE ' + table, autocommit=False)
        self.repository.commit()
            
    def recreate(self):
        self.remove()
        self.initialize()
        
    def needs_init(self):
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name IN (%s)" % ", ".join("%r" % s for s in self.TABLES)
        result = self.repository.execute_statement(query).fetchall()
        return len(result) != len(self.TABLES)
    
    def do_recreate(self, line):
        self.recreate()
        
    def do_help(self, line):
        if not line:
            print "\n", self.__doc__       
        super(Analyzer, self).do_help(line)
        

class BasicImageAnalyzer(Analyzer):
    """ Providing information about basic data (id, search tag, date).
    """
    TABLES = ("images",)
    CREATE_TABLES = ("CREATE TABLE images (id text PRIMARY KEY, tag text, date text)",)
    NAME = 'basic'
    
    def init(self):
        self._count = 0
    
    def parse_file(self, id, tag, data):
        doc = lxml.html.document_fromstring(data)
        try:
            date = doc.cssselect(".RHS .Widget .Plain[property='dc:date']")[0].text
            date = datetime.datetime.strptime(date, '%B %d, %Y').strftime('%Y-%m-%d')
        except IndexError:
            date = ''
        
        self.repository.execute_statement('INSERT INTO images (id, tag, date) VALUES (?,?,?)', (id, tag, date))
        
    def do_imagecount(self, line):
        """ Get number of images in the database."""
        if not self._count:
            self._count = self.repository.execute_statement('SELECT COUNT(id) FROM images').fetchone()[0]
        print "There are %i images in the database." % self._count
        
    def do_oldest(self, line):
        """ Get ID and date of oldest uploaded photo."""
        info = self.repository.execute_statement('SELECT id, date FROM images ORDER BY date ASC').fetchone()      
        print "Image %s was uploaded on %s" % info
    
    def do_newest(self, line):
        """ Get ID and date of newest uploaded photo."""
        info = self.repository.execute_statement('SELECT id, date FROM images ORDER BY date DESC').fetchone()      
        print "Image %s was uploaded on %s" % info
    
    def do_tags(self, line):
        """ Get a list of the tags that have been looked for."""
        
        for tag in self.repository.execute_statement('SELECT DISTINCT tag FROM images ORDER BY tag ASC'):
            print '-', tag[0]
    
    
        