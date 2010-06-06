'''
Created on May 9, 2010

This already includes code for the second project.

'''

import itertools, re
import numpy as np
from time import time

from lxml import etree
from lxml.cssselect import CSSSelector

from flickr_data_miner.analyzer import  Analyzer
from flickr_data_miner.lexicon import wordlist
from flickr_data_miner.util import OrderedSet
import matplotlib.pyplot as plt

from data_analyzer.lsi import TDMBuilder

class TagAnalyzer(Analyzer):
    """ Provides various information about tags. """
    
    TABLES = ("image_tag", "tag")
    CREATE_TABLES = (
                    "CREATE TABLE tag (id integer PRIMARY KEY, name text UNIQUE)",
                    "CREATE TABLE image_tag (image_id integer REFERENCES images(id) ON DELETE CASCADE, tag_id integer REFERENCES tag(id) ON DELETE CASCADE, PRIMARY KEY (image_id, tag_id))"
                    )
    NAME = 'tags'
    
    TAGS = 1
    COMMENTS =2
    
    def init(self):
        self._tags = dict()
        self._temp_initialized = False
        self.sel = CSSSelector("#thetags > div > a.Plain")
        
        self.pca = {}
        
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
    
    def do_plot_ranked_list(self, list):
        """ Plots the ranked list of all tags. """
        
        self.create_temporary_tables()
        tags = self.repository.db_conn.execute('SELECT name, count FROM tag_count ORDER BY count DESC')
        
        print '\nRanked list:\n'
        
        prev_count = 0
        prev_rank = 1
        
        x = []
        y = []
        for rank, (name, count) in enumerate(tags, start=1):
            if count != prev_count:
                prev_rank = rank
                prev_count = count
                x.append(prev_rank)
                y.append(count)
                
            print '%i. %s %i' % (prev_rank, name, count)
        print ''
        
        
        plt.plot(x,y,'r-')
        plt.ylabel('frequencies of tags')
        plt.xlabel('rank of tags')
        plt.grid(True)
        #plt.vlines((2,), 0, data[-1])
        #plt.xlim(0,100)
        #plt.xticks(range(0,100,10))
        plt.show()
     
    def compute_pca(self, num_words=2500, with_comments=False):
        
        u_i = self.pca.get((num_words, with_comments))
        if u_i:
            return (self.pca.get('ordered_images'),  u_i)
        
        self.repository.db_conn.execute("CREATE TEMP TABLE IF NOT EXISTS named_tag_list AS SELECT image_id, name as tag FROM image_tag LEFT JOIN tag ON tag_id = tag.id")
        
        ordered_images = list(itertools.chain(*self.repository.db_conn.execute('SELECT id FROM images ORDER BY id').fetchall()))
        self.pca['ordered_images'] = ordered_images
        
        builder = TDMBuilder(wordlist(num_words), ordered_images, TDMBuilder.LOCAL_BINARY, TDMBuilder.GLOBAL_BINARY)
           
        # create document vectors
        for image_id, tag_name in self.repository.db_conn.execute('SELECT * FROM named_tag_list'):
            builder.add_document_term(image_id, tag_name)
                
        if with_comments:
            for image_id, comment in self.repository.db_conn.execute('SELECT image_id, content FROM image_comment'):
                # get the substring up to 'Posted' and split it by all non word characters
                builder.add_document_terms(image_id, re.split("[^\w']+", comment.lower()[:comment.rfind('Posted')]))
                  
        M = builder.built_matrix()
     
        m = np.mean(M, axis=1)                          # 1. compute the mean          
        Xs = M - m                                        # 2. substract the mean
        S = np.cov(M)                                     # 3. compute the covariance matrix
        w,V = np.linalg.eig(S)                            # 4. compute the eigenvalues,-vectors

        # go through some conversion hassel to sort the vectors by the values   
        # generate a list of columns  
        Va = V.transpose().tolist() #vectors are now lists
        Va = map(tuple, Va)
        dVa = dict(itertools.izip(Va, w)) #associate eigenvectors and eigenvalues             
        V = sorted(Va, key=dVa.get, reverse=True)                              # 5. sort by eigenvalues
           
        V2 = np.matrix(V[0:2]).astype(np.float64)  # eigenvectors contain complex values -> transorm to reals
        
        U = V2*Xs                      # 6. compute u_is
        u = U.transpose().tolist()
        self.pca[(num_words, with_comments)] = u
        
        return u
     
    def do_pca(self, line):
        
        num_words = raw_input('How many words from the dictionary (default: 2500) ? ')
        try:
            num_words = int(num_words)
        except:
            num_words = 2500
        
        with_comments = raw_input('With comments (much slower)? (yes/NO) ')
        with_comments = with_comments and with_comments.lower() != 'no'
        tags_to_plot = raw_input('Which tags to plot (default: all) ? ')
        
        tags = self.repository.db_conn.execute('SELECT DISTINCT tag FROM images ORDER BY tag').fetchall()
        tags = list(itertools.chain(*tags)) # make a flat list

        now = time()
        # image documents is of form
        # [((image_id, tag), u_i), ...]
        # i.e. image_id with corresponding tag and document vector
        image_documents = itertools.izip(self.repository.db_conn.execute('SELECT id, tag FROM images ORDER BY id'), self.compute_pca(num_words, with_comments))
        print 'Time elapsed for computation: %f' % (time()-now)
        
        if tags_to_plot: # only keep elements to plot
            tags_to_plot = tags_to_plot.split()
            image_documents = itertools.ifilter(lambda x: x[0][1] in tags_to_plot, image_documents)
            
        cmap= ('#000000', '#6600FF', '#FF9933', '#0033FF', '#00FFFF', '#FFFF33', '#006600', '#666666', '#666600', '#FF00CC')
        
        
        # plots is of form
        # plots = {'tagname': (x_coords_list, y_coords_list, color),...}   
        plots = dict()     
        for (_, tag), doc in image_documents:
            p = plots.setdefault(tag, ([], [], cmap[tags.index(tag) % len(tags)]))
            p[0].append(doc[0])
            p[1].append(doc[1])
        
        # to differentiate the tags per color
        for tag, (x, y, color) in plots.iteritems():
            plt.scatter(x,y, c=color, s=20, marker='o')
            
        plt.legend(plots.keys(), scatterpoints=1, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        plt.grid(True)
        plt.show()
        
    def create_temporary_tables(self):
        if not self._temp_initialized:
            self.repository.db_conn.execute("CREATE TEMP TABLE IF NOT EXISTS tags_per_image AS SELECT image_id, COUNT(tag_id) as count FROM image_tag GROUP BY image_id")
            self.repository.db_conn.execute("CREATE TEMP TABLE IF NOT EXISTS tag_count AS SELECT tag_id, name, COUNT(image_id) as count FROM image_tag LEFT JOIN tag on tag_id = id GROUP BY tag_id, name")