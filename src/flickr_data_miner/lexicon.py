'''
Created on Jun 2, 2010

@author: kling
'''

import os, urllib2
from lxml import etree

WORDLIST_URL = 'http://www.insightin.com/esl/%d.php'
STOPLIST_URL = 'http://ir.dcs.gla.ac.uk/resources/linguistic_utils/stop_words'

PATH = os.path.expanduser('~/.wordlist-lexicon')
WORDLIST = 'wordlist.txt'
STOPLIST = 'stoplist.txt'

def wordlist(amount, remove_stop_words=True):
    """ Gets the most used words in the English language.
    
        INPUT:
            - amount: Number of words to fetch (max: 6000)
            - remove_stop_words: Don't return stop words (default: True)
        
        OUTPUT:
            A list of words.
    """
    
    amount = amount % 6001;
    fetch_data = True
    words = list()   
    if not os.path.exists(PATH):
        os.mkdir(PATH)
    
    if os.path.exists(os.path.join(PATH, WORDLIST)):
        with open(os.path.join(PATH, WORDLIST), 'r') as f:
            contained_words = int(f.readline())
            if contained_words >= amount: 
                fetch_data = False
                words.extend([w.strip().lower() for w in f])
        
    if fetch_data:
        l = [1000,2000] + range(2100, 6100, 100)
        

        fetched = 0
        for i in l:
            if i - amount >= 100:
                break
            data = urllib2.urlopen(WORDLIST_URL % i).read()
            html = etree.HTML(data)
            fetched = i
            if i > 2000:
                # words are contained in links
                # NOTE: lxml creates valid XHTML therefore the XPath differs from what might be expected
                words.extend(map(lambda x: x.strip(),  html.xpath("/html/body/center/table/tr[2]/td[2]/table//a/text()")))
            else:
                # splits the text into parts and takes out the words
                words.extend(html.xpath("//pre/text()")[0].split()[1::2])
                
        words = map(str.lower, words)
        
        f = open(os.path.join(PATH, WORDLIST), 'w')
        f.write('%d\n' % fetched)
        f.write('\n'.join(words))
        f.close()
    
    #words = words[:amount]
    
    if remove_stop_words:
        stops = []
        if not os.path.exists(os.path.join(PATH, STOPLIST)):
            data = urllib2.urlopen(STOPLIST_URL).read()
            with open(os.path.join(PATH, STOPLIST), 'w') as f:
                f.write(data)
            stops = data.split()
        else:
            with open(os.path.join(PATH, STOPLIST), 'r') as f:
                stops = [w.strip() for w in f]
        return filter(lambda x: x not in stops, words)[:amount]
    
    return words[:amount]
                
if __name__ == '__main__':
    print len(wordlist(100))