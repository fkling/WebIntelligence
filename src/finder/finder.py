'''
Created on Jun 27, 2010

@author: kling
'''

import os, sys
from optparse import OptionParser

from fetcher import WAFetcher
from resolver import TEResolver
 
    

def get_names(image, max_pages=1, min_score=2, resolver = None):
    """ Tries to find out, what object is in an image.
        
        INPUT:
            - image: The path to the image
            - max_pages: The number of result pages to follow
            - min_score: Minimal occurances a term must have to be returned
            - resolver: Resolver to use for getting the names
        
        OUPUT:
            Returns a list of (name, score) tuples.
    """
    
    if not resolver:
        resolver = TEResolver()
    return resolver.get_names(image, max_pages, min_score)
    

def get_weight_for(name, fetcher=None):
    """ Tries to get the weight for an object with name <name>.
    
        INPUT:
         - name: The name to search for
         - fetcher: Fetcher to get the weight
    """
    
    if not fetcher:
        fetcher = WAFetcher()  
    return fetcher.get_weight(name)

def parse_options():
    parser = OptionParser(usage="usage: python %prog [options] image")
    parser.add_option("-p", "--max_pages", dest="max_pages", type="int", default=1,
                      help="examin MAX_PAGES result pages (default: 1)")
    parser.add_option("-s", "--min_score", type="int", dest="min_score", default=2,
                      help="select only terms that occure more then MIN_SCORE times (default: 2)")
    parser.add_option("-f", "--fetch_weight", type="int", default=0, dest="fetch",
                      help="get weight for the first N terms (0 = no fetch, default: 0)",
                      metavar="N")
    

    options, args = parser.parse_args()
    
    if not len(args) > 0:
        print "Error: You have to provide an image as input."
        parser.print_help()
        sys.exit(1)
    if not os.path.exists(os.path.abspath(args[0])):
        print "Error: The file %s does not exist." % os.path.abspath(args[0])
        parser.print_help()
        sys.exit(1)
        
    return options, args


if __name__ == "__main__":
    options, args = parse_options()
    file = args[0]
    print "Getting names for image %s..." % file
    names = get_names(file, options.max_pages, options.min_score)
    print "done:\n"
    
    for i, (name, score) in enumerate(names, start=1):
        print '%i. %s\t\t%i' % (i, name, score)
    print ""
    
    if options.fetch:
        terms = [n for n,_ in names[:options.fetch]]
        print "Calculate weight for %s:" % ', '.join(terms)
        
        for name in terms:
            weight = get_weight_for(name)
            if not weight:
                print "No weight found for %s" % name
            else:
                print "%s weights %s" % (name, weight)
        print ""