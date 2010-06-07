'''
Created on Jun 7, 2010

@author: kling
'''

import itertools, re
import numpy as np
from time import time

from flickr_data_miner.analyzer import  Analyzer
from flickr_data_miner.lexicon import wordlist
import matplotlib.pyplot as plt

from data_analyzer.lsi import TDMBuilder, compute_pca

class PCAAnalyzer(Analyzer):
    """ Provides various information about tags. """
    
    TABLES = []
    CREATE_TABLES = []
    NAME = 'pca'
    
    TAGS = 1
    COMMENTS =2
    
    def init(self):        
        self.pca = []
        self.tdm = []
        
    def parse_file(self, id, tag, data):
        pass
    
    def do_recreate(self):
        print "This analyzer as no setup."
        
    def needs_init(self):
        return False
     
    def do_build(self, line):
        """ This function creates the term document matrix for the current 
            repository and computes the PCA.
            
            The lexicon consists of the 6000 most used words in the English 
            language.
            
            Pass "list" as parameter to see a list of already built TDMs.
        """
        
        TF = None
        
        if(line.strip() == 'list'):
            if not self.tdm:
                print 'No TDMs computed yet.'
                return
            else:
                print '\nSelect a TDM:\n'
                selected = False
                while not selected:
                    print 'Index'.center(15), '#Words'.center(15), 'Comments'.center(15)
                    for i, (num_words, comments, _) in enumerate(self.tdm):
                        print str(i).center(15), str(num_words).center(15), \
                                '{0}'.format('Yes' if comments else 'NO').center(15)
                                
                    print '\n-1: New'
                                    
                    option = raw_input('Select: ')                 
                    try:
                        option = int(option)
                        if option == -1:
                            selected = True
                            break
                        elif 0 <= option <= len(self.tdm):
                            selected = True
                            num_words, with_comments, TF = self.tdm[option]
                    except:
                        pass 
        
        if TF is None: # build new matrix if none selected
            num_words = raw_input('How many words from the lexicon (default: 2500) ? ')
            try:
                num_words = int(num_words)
            except:
                num_words = 2500       
            with_comments = raw_input('Include comments? (yes/NO) ')
            with_comments = with_comments and with_comments.lower() != 'no'
            
            
            
        localw = raw_input('Local weight function (0=bin, 1=tf, 2=log, 3=augnorm; default: bin): ')
        try:
            localw = int(localw) % 4
        except:
            localw = TDMBuilder.LOCAL_BINARY
            
        globalw = raw_input('Global weight function (0=bin, 1=norm, 2=gfldf, 3=ldf, 4=entropy; default: bin): ')
        try:
            globalw = int(globalw) % 5
        except:
            globalw = TDMBuilder.GLOBAL_BINARY
        
        
        print 'Computing...'
        now = time()
        
        # Create temporary table for fast access 
        self.repository.db_conn.execute("""
            CREATE TEMP TABLE IF NOT EXISTS named_tag_list AS 
                SELECT image_id, name as tag 
                FROM image_tag 
                LEFT JOIN tag 
                ON tag_id = tag.id""")
        
        # get images
        ordered_images = list(itertools.chain(*self.repository.db_conn.execute('SELECT id FROM images ORDER BY id').fetchall()))
        
        # create builder
        builder = TDMBuilder(wordlist(num_words), ordered_images)
        
        
        if TF is None: # build new matrix if none selected
            # create document vectors
            for image_id, tag_name in self.repository.db_conn.execute('SELECT * FROM named_tag_list'):
                builder.add_document_term(image_id, tag_name)
                    
            if with_comments:
                # just traversing the table is much as getting all comments and tags 
                # for an image beforehand (~ 7 times faster)
                for image_id, comment in self.repository.db_conn.execute('SELECT image_id, content FROM image_comment'):
                    # get the substring up to 'Posted' and split it by all non word characters
                    builder.add_document_terms(image_id, re.split("[^\w']+", comment.lower()[:comment.rfind('Posted')]))
        
            self.tdm.append((num_words, with_comments, builder.getTF()))  
                                
        M = builder.build_matrix(localw=localw, globalw=globalw, matrix=TF)
        U = compute_pca(M)
        print 'Finished. Time elapsed: %f' % (time()-now)
        
        self.pca.append((num_words, with_comments, localw, globalw, U))
     
    def do_plot(self, line):
        """ Plots the chosen term document matrix."""
        
        if not self.pca:
            print "Create a term document matrix with 'build_tdm' first."
            return
        
        print "\nSelect one of the matricies to plot:\n"
        
        option = self.print_matrix_select_list()
        
        tags_to_plot = raw_input('Which tags to plot (default: all) ? ')
        
        # get tags for grouping and coloring the plot
        tags = self.repository.db_conn.execute('SELECT DISTINCT tag FROM images ORDER BY tag').fetchall()
        tags = list(itertools.chain(*tags)) # make a flat list
        
        # vectors  
        Us = self.pca[option][-1].transpose().tolist()
             
        # image documents is of form
        # [((image_id, tag), u_i), ...]
        # i.e. image_id with corresponding tag and document vector
        image_documents = itertools.izip(self.repository.db_conn.execute('SELECT id, tag FROM images ORDER BY id'), Us)
              
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
    
    def print_matrix_select_list(self):
        selected = False
        while not selected:
            print 'Index'.center(15), '#Words'.center(15), 'Comments'.center(15), 'Local Weight'.center(15), 'Global Weight'.center(15)
            for i, (num_words, comments, localw, globalw, _) in enumerate(self.pca):
                print str(i).center(15), str(num_words).center(15), \
                        '{0}'.format('Yes' if comments else 'NO').center(15), \
                        str(localw).center(15), str(globalw).center(15)
                        
            print '\n-1: List weight function code'
            
            option = raw_input('Select: ')
            
            try:
                option = int(option)
                if option == -1: 
                    print TDMBuilder.__doc__
                elif 0 <= option <= len(self.pca):
                    selected = True
            except:
                pass          
        return option