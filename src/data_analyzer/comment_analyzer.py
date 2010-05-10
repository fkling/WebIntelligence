'''
Created on May 9, 2010

'''

from lxml import etree
from lxml.cssselect import CSSSelector

from flickr_data_miner.analyzer import  Analyzer


class CommentAnalyzer(Analyzer):
    """ Provides various information about comments. """
    
    TABLES = ("image_comment",  )
    CREATE_TABLES = (
                    "CREATE TABLE IF NOT EXISTS  image_comment (image_id integer REFERENCES images(id) ON DELETE CASCADE,commenter_id text,commentdate text,content text)", 
                    )
    NAME = 'comments'
    
    def init(self):
        self._count=0
        self._temp_initialized = False
        self._cs = CSSSelector('#DiscussPhoto .comment-block')
        self._commenters = CSSSelector('h4 > a')
        self._comments = CSSSelector('.comment-content > p')
        self._dates = CSSSelector('.comment-content > p > small')
        
    def parse_file(self, id, tag, data):
        doc = etree.HTML(data)
        comments = self._cs(doc)
        values = list()
        for i, c in zip(xrange(10),comments):
            try:
                commenter=self._commenters(c)[0].text
                comment=' '.join(self._comments(c)[0].itertext())
#                  print 'c:',  comment
                date=' '.join(self._dates(c)[0].itertext())
            except IndexError:
                commenter=""
                comment=""
                date=""  
            values.append((id, commenter,date, comment))
            
        self.repository.db_conn.executemany('INSERT INTO image_comment (image_id, commenter_id,commentdate,content) VALUES (?,?,?,?)', values)
        
    def do_count_all(self, line):
        """ Returns the number of all assigned comments. """

        number = self.repository.db_conn.execute('SELECT COUNT(content) FROM image_comment').fetchone()
        print 'There are %i comments assigned to images.' % number
    
    def do_count_single(self, line):
        """ Returns the number of single assigned comments. """
        imageid = str(raw_input('Enter the image id you want to search(e.g. 12345678):'))
        number =self.repository.db_conn.execute("SELECT COUNT(content) FROM image_comment WHERE image_id = '%s'"%imageid).fetchone()
        print 'There are %i comments assigned to image %i' %(number[0],imageid)
        
    
    def do_list_all(self, line):
        """ Lists all comments. """
        
        comments = self.repository.db_conn.execute('SELECT content FROM image_comment ORDER BY image_id')
        for comment, in comments:
            print comment
    
    def do_list_single(self, line):
        """ Lists choosed comments. """
        imageid = str(raw_input('Enter the image id you want to search(e.g. 12345678):'))
        comments = self.repository.db_conn.execute("SELECT content FROM image_comment WHERE image_id = '%s'"%imageid)
        for comment, in comments:
            print comment