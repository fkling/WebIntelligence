'''
Created on Jun 27, 2010

'''

import urllib2

from lxml import etree

class WAFetcher(object):
    """ Tries to get the weight for an object from 
    
            http://www.wolframalpha.com
            
        EXAMPLES:
        >>> f = WAFetcher()
        >>> print f.get_weight('apple')
        182 grams
        
        >>> print f.get_weight('hamburger')
        161 grams
        
        >>> print f.get_weight('pizza')
        140 grams
    """
    
    BASE_URL = 'http://www.wolframalpha.com/'
    SEARCH_URL = BASE_URL + '/input/?i={term}&asynchronous=false&equal=Submit'


    def get_weight(self, name):
        terms = '+'.join((name, 'weight'))
        try:
            source = urllib2.urlopen(self.SEARCH_URL.format(term=terms)).read()
            html = etree.HTML(source)
            try:
                weight = html.xpath("//div[contains(@class,'pod') and .//h2[contains(text(), 'Result:')]]//div[contains(@class, 'output')]/img")[0].get('alt')
            except:
                weight = ''
        except:
            weight = ''

        return weight
    
if __name__ == '__main__':
    import doctest
    doctest.testmod()