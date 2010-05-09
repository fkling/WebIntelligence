'''
Created on May 9, 2010

@author: kling
'''

import itertools

from lxml import etree
from lxml.cssselect import CSSSelector

from flickr_data_miner.analyzer import  Analyzer

class TagAnalyzer(Analyzer):
    """ Provides various information about tags. """
    
    TABLES = ("image_tag", "tag")
    CREATE_TABLES = (
                    "CREATE TABLE tag (id integer PRIMARY KEY, name text UNIQUE)",
                    "CREATE TABLE image_tag (image_id integer REFERENCES images(id) ON DELETE CASCADE, tag_id integer REFERENCES tag(id) ON DELETE CASCADE, PRIMARY KEY (image_id, tag_id))"
                    )
    NAME = 'tags'
    
    def init(self):
        self._tags = dict()
        self._temp_initialized = False
        self.sel = CSSSelector("#thetags > div > a.Plain")
        
    def parse_file(self, id, tag, data):
        doc = etree.HTML(data)
        tags = set(tagel.text.strip().lower() for tagel in self.sel(doc))
        values = list()
        for tagname in tags:
            if tagname not in self._tags:
                tagid = self.repository.db_conn.execute('INSERT INTO tag (name) VALUES (?)', (tagname, )).lastrowid
                self._tags[tagname] = tagid
            else:
                tagid = self._tags[tagname]
            values.append((tagid, id))
        
        self.repository.db_conn.executemany('INSERT INTO image_tag (tag_id, image_id) VALUES (?,?)', values)
            
    def do_count_unique_tags(self, line):
        """ Returns the number of unique tags. """
        
        number = self.repository.db_conn.execute('SELECT COUNT(id) FROM tag').fetchone()
        print 'There are %i unique tags assigned to images.' % number
        
    def do_count_tags(self, line):
        """ Returns the number of all assigned tags. """
        
        number = self.repository.db_conn.execute('SELECT COUNT(tag_id) FROM image_tag').fetchone()
        print 'There are %i tags assigned to images.' % number
        
    def do_list_unique_tags(self, line):
        """ Lists all unique tags. """
        
        tags = self.repository.db_conn.execute('SELECT name FROM tag ORDER BY name').fetchall()
        print ', '.join(tag[0] for tag in tags)
        
    def do_list_most_used(self, line):
        """ List the most used tags. """
        
        max = 10
        if line:
            try:
                max = int(line)
            except ValueError:
                pass
        
        self.create_temporary_tables()
        tags = self.repository.db_conn.execute('SELECT name, count FROM tag_count ORDER BY count DESC, name ASC')
        
        print '\nThese are the %i most used tags:\n' % max
        for ((name, count),i) in zip(tags, xrange(1,max+1)):
            print '%i. %s %i' % (i, name, count)
        print ''
            
    def do_list_less_used(self, line):
        """ List tags that are most used. """
        
        max = 10
        if line:
            try:
                max = int(line)
            except ValueError:
                pass
        
        self.create_temporary_tables()
        tags = self.repository.db_conn.execute('SELECT name, count FROM tag_count ORDER BY count ASC')
        
        print '\nThese are the %i less used tags:\n' % max
        for ((name, count),i) in zip(tags, xrange(1,max+1)):
            print '%i. %s %i' % (i, name, count)
        print ''
            
    def do_count_less_used(self, line):
        """ Count tags that are most used. """
        
        self.create_temporary_tables()
        min = self.repository.db_conn.execute('SELECT MIN(count) FROM tag_count').fetchone()
        number = self.repository.db_conn.execute('SELECT COUNT(tag_id) FROM tag_count WHERE count = ?', min).fetchone()[0]
        
        print 'Number of unique tags used only %i time(s): %i' % (min[0], number)
        
    def do_list_most_tagged(self, line):
        """ List images with the most tags. """
        
        max = 10
        if line:
            try:
                max = int(line)
            except ValueError:
                pass
        
        self.create_temporary_tables()
        images = self.repository.db_conn.execute('SELECT image_id, count FROM tags_per_image ORDER BY count DESC, image_id ASC')
        
        print '\nThese are the %i most tagged images:\n' % max
        for ((id, count),i) in zip(images, xrange(1,max+1)):
            print '%i. %i %i' % (i, id, count)
        print ''
        
    def do_list_searched_tags(self, line):
        """ List the count of the searched tags. """
        
        self.create_temporary_tables()
        tags = self.repository.db_conn.execute('SELECT name, count FROM tag_count WHERE name in (SELECT DISTINCT tag FROM images) ORDER BY count DESC, name ASC')
        
        for el in tags:
            print '- %s %i' % el
    
    def do_ranked_list(self, list):
        self.create_temporary_tables()
        tags = self.repository.db_conn.execute('SELECT name, count FROM tag_count ORDER BY count DESC')
        
        print '\nRanked list:\n'
        
        
        def filter(t, last=[0]):
            name, count = t
            if count != last[0]:
                last[0] = count
                return True
            return False
        
        
        for i, (name, count) in enumerate(itertools.ifilter(filter, tags), start=1):
            print '%i. %i' % (i, count)
        print ''
        
        
    def create_temporary_tables(self):
        if not self._temp_initialized:
            self.repository.db_conn.execute("CREATE TEMP TABLE IF NOT EXISTS tags_per_image AS SELECT image_id, COUNT(tag_id) as count FROM image_tag GROUP BY image_id")
            self.repository.db_conn.execute("CREATE TEMP TABLE IF NOT EXISTS tag_count AS SELECT tag_id, name, COUNT(image_id) as count FROM image_tag LEFT JOIN tag on tag_id = id GROUP BY tag_id, name")
 