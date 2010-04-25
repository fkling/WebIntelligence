'''
Created on Apr 19, 2010

@author: kling
'''

class Analyzer(object):
    '''
    classdocs
    '''
    def __init__(self, repository):
        '''
        Constructor
        '''
        self.repository = repository
    
    def _setup(self):
        raise NotImplementedError('This method must be implemented')
    
    def _create_table(self):
        raise NotImplementedError('This method must be implemented')
    
    def parse_file(self, file):
        pass
    
    def parse_files(self, files):
        for file in files:
            self.parse_file(file)
            
    @property
    def actions(self):
        pass

class BasicImageAnalyzer(Analyzer):
    
    def _setup(self):
        conn = 
        connection = sqlite3.connect(db_path)
            c = connection.cursor()
            c.execute("CREATE TABLE images (id text PRIMARY KEY, src text, \
                        tag text, date text)");
            
            connection.commit()
            connection.close()