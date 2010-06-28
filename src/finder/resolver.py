'''
Created on Jun 27, 2010

'''
import os, re, itertools, urllib2, nltk
from util import upload_file, wordlist

from lxml import etree
from lxml.cssselect import CSSSelector

class TEResolver(object):
    """ Tries to identify images via tineye.com """
    
    
    SEARCH_URL = "http://www.tineye.com/search"
    SEARCH_FIELD_NAME = 'image'
    SEARCH_SUFFIX = "/?page={page}&sort=score&order=desc"
    
    
    def get_names(self, image, max_pages=1, min_score=2):
    
        if image and os.path.exists(os.path.abspath(image)):
            image = os.path.abspath(image)
            raw_html = upload_file(image, self.SEARCH_URL, self.SEARCH_FIELD_NAME)
        
            # get base link
            html = etree.HTML(raw_html)
            links = html.xpath("//link[@rel='icon']")
            for link in links:
                result_url = link.get('href').replace('query', 'search')
                if link.get('href').startswith('http:'):
                    break
            if result_url:
                return list(self._name_resolver(self._name_extractor(result_url, max_pages, raw_html), min_score))
               
            # if some error occurs, return empty list
            return list()
        
    
    def _name_resolver(self, filenames, min_score=2):
        """ Tries to extract proper words from filnames.
            
            INPUT:
                - filenames: A list of filenames
                - min_score: Minimal occurances a term must have to be returned
                
            OUPUT:
                A generator, iterating over all names, yielding a tuple of the form
                (name, score)
            
            EXAMPLES:
            
            >>> files = ['cheese-1.png', 'Megacheese.jpg', 'gauda.gif', 'cheese1245.gif',
            ... 'my_favourite_cheese.jpg', 'cheesefactory-1.png', 'cheesefactory-2.png',
            ... 'cheesefactory3.png', 'cAs412FDV.png', 'best_cheese_ever1.png']
            >>> r = TEREsolver()
            >>> list(r._name_resolver(files))
            [('cheese', 3), ('cheesefactory', 2)]
            
        """
        
        names = {}
        # remove those links that don't belong to an image
        for name in itertools.ifilter(lambda x: not x.startswith('view all'), filenames):
            name = os.path.splitext(name)[0].lower() # remove file extension and normalize
            for part in re.split(r'[%_\s+.-]+', name): # extract word parts
                # only add words that have a least 3 characters and don't contain a number
                if part and len(part) > 2 and not re.match(r'.*\d.*', part): 
                    counter = names.get(part, 0)
                    counter += 1
                    names[part] = counter
                    
        for name in itertools.ifilter(lambda x: names[x] >= min_score, sorted(names, key=names.get, reverse=True)):
            yield (name, names[name])
            
            
    def _name_extractor(self, result_url, max_pages=1, raw_html=None):
        """ Extracts the image file names from a tineye.com result page.
        
            INPUT:
                - result_url: The URL of the result
                - max_pages: The number of result pages to follow
                - raw_html: Source of the first result page
            
            OUTPUT:
                A generator, iterating over all file names.
                
        """
        
        sel=CSSSelector('div.search-content-results-body div.location-match p')
        
        if not raw_html:
            raw_html = urllib2.urlopen(result_url).read()
        
        html = etree.HTML(raw_html)
        
        try:
            pages = int(html.xpath('//div[@id="pag_bottom"]/a[@class="next"]/preceding-sibling::a/text()')[-1])
        except IndexError:
            pages = 1 
        max_pages = min(pages, max_pages)   
        
        for ele in sel(html):
            try:
                yield ele[0].text
            except IndexError:
                pass
        
        if max_pages > 1:
            for i in range(2, max_pages+1):
                url = result_url + self.SEARCH_SUFFIX.format(page=i)
                raw_html = urllib2.urlopen(url).read()
                html = etree.HTML(raw_html)
                for ele in sel(html):
                    try:
                        yield ele[0].text
                    except IndexError:
                        pass
                    
class TEContentResolver(object):
    """ Tries to identify images via tineye.com """
    
    
    SEARCH_URL = "http://www.tineye.com/search"
    SEARCH_FIELD_NAME = 'image'
    SEARCH_SUFFIX = "/?page={page}&sort=score&order=desc"
    
    
    def __init__(self, filter=3000):
        self.commons= wordlist(filter, False)
    
    def get_names(self, image, max_pages=1, min_score=2):
    
        if image and os.path.exists(os.path.abspath(image)):
            image = os.path.abspath(image)
            raw_html = upload_file(image, self.SEARCH_URL, self.SEARCH_FIELD_NAME)
        
            # get base link
            html = etree.HTML(raw_html)
            links = html.xpath("//link[@rel='icon']")
            for link in links:
                result_url = link.get('href').replace('query', 'search')
                if link.get('href').startswith('http:'):
                    break
            if result_url:
                return list(self._name_resolver(self._name_extractor(result_url, max_pages, raw_html), min_score))
               
            # if some error occurs, return empty list
            return list()
        
    
    def _name_resolver(self, filenames, min_score=2):
        """ Tries to extract proper words from filnames.
            
            INPUT:
                - filenames: A list of filenames
                - min_score: Minimal occurances a term must have to be returned
                
            OUPUT:
                A generator, iterating over all names, yielding a tuple of the form
                (name, score)
            
            EXAMPLES:
            
            >>> files = ['cheese-1.png', 'Megacheese.jpg', 'gauda.gif', 'cheese1245.gif',
            ... 'my_favourite_cheese.jpg', 'cheesefactory-1.png', 'cheesefactory-2.png',
            ... 'cheesefactory3.png', 'cAs412FDV.png', 'best_cheese_ever1.png']
            >>> r = TEREsolver()
            >>> list(r._name_resolver(files))
            [('cheese', 3), ('cheesefactory', 2)]
            
        """
        pattern = re.compile(r'^[a-z]{3,}$')
        names = {}
        # remove those links that don't belong to an image
        for token in filenames:
            token = token.lower().strip()
            if token not in self.commons and pattern.match(token):
                counter = names.get(token, 0)
                counter += 1
                names[token] = counter
                    
        for name in itertools.ifilter(lambda x: names[x] >= min_score, sorted(names, key=names.get, reverse=True)):
            yield (name, names[name])
            
            
    def _name_extractor(self, result_url, max_pages=1, raw_html=None):
        """ Extracts the image file names from a tineye.com result page.
        
            INPUT:
                - result_url: The URL of the result
                - max_pages: The number of result pages to follow
                - raw_html: Source of the first result page
            
            OUTPUT:
                A generator, iterating over all file names.
                
        """
        
        sel=CSSSelector('div.search-content-results-body div.location-match p')
        
        if not raw_html:
            raw_html = urllib2.urlopen(result_url).read()
        
        html = etree.HTML(raw_html)
        
        try:
            pages = int(html.xpath('//div[@id="pag_bottom"]/a[@class="next"]/preceding-sibling::a/text()')[-1])
        except IndexError:
            pages = 1 
        max_pages = min(pages, max_pages)   
        
        for ele in sel(html):
            try:
                link = ele[2].get('href')
                source = urllib2.urlopen(link).read()
                source = nltk.clean_html(source)
                tokens = nltk.word_tokenize(source)
                for token in tokens:
                    yield token
            except (IndexError, urllib2.URLError, urllib2.HTTPError):
                pass
        
        if max_pages > 1:
            for i in range(2, max_pages+1):
                url = result_url + self.SEARCH_SUFFIX.format(page=i)
                raw_html = urllib2.urlopen(url).read()
                html = etree.HTML(raw_html)
                for ele in sel(html):
                    try:
                        link = ele[2].get('href')
                        source = urllib2.urlopen(link).read()
                        source = nltk.clean_html(source)
                        tokens = nltk.word_tokenize(source)
                        for token in tokens:
                            yield token
                    except (IndexError, urllib2.URLError, urllib2.HTTPError):
                        pass