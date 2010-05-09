'''
Created on May 9, 2010

@author: agarja
'''

import string

from lxml import etree
from lxml.cssselect import CSSSelector

from flickr_data_miner.analyzer import  Analyzer


class RatingAnalyzer(Analyzer):
    """ Provides various information about ratings. """
    
    TABLES = ("image_rating",  )
    CREATE_TABLES = (
                    "CREATE TABLE IF NOT EXISTS image_rating (image_id integer REFERENCES images(id) ON DELETE CASCADE, rating integer)", 
                    )
    NAME = 'ratings'
    
    def init(self):
        self._tags = dict()
        self._temp_initialized = False
        self.sel = CSSSelector("#fave_countSpan");
    
    def parse_file(self, id, tag, data):
        doc = etree.HTML(data)
        try:
            counts = int(string.replace(self.sel(doc)[0].text.split()[0], ',', ''))
        except IndexError:
            counts = 0
        self.repository.db_conn.execute('INSERT INTO image_rating (image_id, rating) VALUES (?,?)', (id, counts))
        
    def do_average_rating(self, line):
        number = self.repository.db_conn.execute('SELECT AVG(rating) FROM image_rating').fetchone()
        print "In average, %i people call each photo as their favorite." % number
        
    def do_total_rating(self, line):
        number = self.repository.db_conn.execute('SELECT SUM(rating) FROM image_rating').fetchone()
        print "In total, all images are marked as favorite %i times." % number
    
    def do_max_rating(self, line):
        number = self.repository.db_conn.execute('SELECT rating, image_id FROM image_rating WHERE rating = (SELECT MAX(rating) FROM image_rating)').fetchone()
        print "The most liked image is liked by %i people (image %i)." % number
