#!/usr/bin/env python
'''
Created on Apr 16, 2010

'''
import threading, os, sys, urllib2, lxml.html
from datetime import datetime
from Queue import Queue
from lxml import etree
from lxml.cssselect import CSSSelector


import settings
from storage import Repository
from net import FileGetter
from util import ProgressBar, get_class
from analyzer import AnalyzerCmd



def get_urls(tags=None, pages=1):
    """ Fetches the URLs of the thumbnails and HTML pages of flickr images.
    
        INPUT:
            - tags: A sequence of tags to search for.
            - pages: The number of pages to examine per tag
            
        OUTPUT:
            A dictionary that contains the tags as keys and a for each tag a list
            of tuples of the form (image-id, page_url, thumbnail_url)
            
    """
    
    if not tags:
        return dict()
    
    ids = set()
    result = dict()
    for tag in tags:
        l = list()
        for page in range(1,pages+1):
            source = urllib2.urlopen(settings.SEARCH_URL.format(tags=tag, page=page)).read()
            dom = lxml.html.document_fromstring(source)
            for link in dom.cssselect(settings.THUMBNAIL_LINK_SELECTOR):
                # get and fetch page_url
                page_link = settings.BASE_URL + link.get('href')
                id = long(page_link.split('/')[-2])
                if id not in ids:
                    ids.add(id)
                    image_link = link.find('img').get('src')
                    l.append((id, page_link, image_link))
        result[tag] = l
    return result
                


def fetch_data(dir, tags=None, print_progress=False, threads=50):
    """ Fetches the content of the URLs provided via tags into the directory
        specified by dir.
        
        INPUT:
            - dir: The directory to store the data
            - tags: A dictionary of tags, each containing a list of tuples.
                    See 'get_urls'.
            - print_progress: Show a progress bar
            - threads: The maximum amount of threads that are started to fetch
                       the data.
        OUTPUT:
            None
    """
    
    if not tags:
        return
    
    repository = Repository(dir, new=True)
    repository.set_last()
    
    # Function to be executed by the producer thread. Creates a new thread
    # for each URL and puts it into a queue
    def producer(queue, tags):
        try:
            for tag in tags:
                for id, page_url, image_url in tags[tag]:
                    thread = FileGetter(id, tag, page_url, image_url)
                    thread.start()
                    queue.put(thread, True)
        except KeyboardInterrupt:
            raise
    
    # Function to be executed by the consumer thread. Gets every thread in the
    # queue, joins it to terminate it properly and stores the data in a repository.
    def consumer(queue, rep, total_files, print_progress):
        if print_progress:
            bar = ProgressBar(total_files, width=50)
                
        counter = 0
        try:
            while counter < total_files: # run until all images are fetched
                thread = queue.get(True)
                thread.join()
                if thread.has_result:
                    rep.add_site(thread.tag, thread.id, thread.page)
                    rep.add_image(thread.tag, thread.id, thread.image)
                    counter += 1
                    if print_progress:
                        bar.add()
                else:
                    total_files -= 1
                    if print_progress:
                        bar = ProgressBar(total_files, width=50)
                        bar.add(counter)
    
                if print_progress:
                    sys.stdout.write("%i%% %r fetched %i of %i \r" %( counter*100/total_files, bar, counter, total_files))
                    sys.stdout.flush()
        except KeyboardInterrupt:
            raise
    
    
    q = Queue(threads)
    prod_thread = threading.Thread(target=producer, args=(q, tags))
    total = reduce(lambda x,y: x+y, [len(tags[tag]) for tag in tags])
    cons_thread = threading.Thread(target=consumer, args=(q, repository, total, print_progress))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    

def parse_options():
    """ Encapsulate option parsing. Only used if this file is run as script. """
    
    usage = """usage: %prog -f [-d DIR] [-p PAGES] tag1 [tag2 ...]    fetch images for tag1, tag2,...
   or: %prog -a REPOSITORY                             enter analyzer mode for repository"""

    parser = OptionParser(usage=usage)
    
    parser.add_option('-f', '--fetch', action='store_true', dest='fetch'
                      , help='mine images corresponding to the tags')
    
    parser.add_option('-a', '--analyze', action='store_true', dest='analyze', 
                      help='analyze the data in specified repository')
    
    group = OptionGroup(parser, 'Fetch options', 'These options are valid in combination with the fetch option:')
    group.add_option('-p','--pages', action='store', type='int', dest='pages',
                      default=1,
                      help='number of pages to get the images from [default: %default]')
    now = datetime.now()
    group.add_option('-d', '--dir', dest='directory',
                      default=os.path.join(os.path.expanduser('~'), 'flickr-analysis', now.strftime('%Y-%m-%d_%H-%M')), metavar='DIR',
                      help='the destination directory [default: %default]')
    
    parser.add_option_group(group)
    
    
    (options, args) = parser.parse_args()
    
    
    if not options.fetch and not options.analyze:
        parser.error("See usage...")
    
    
    if options.fetch and not args:
        parser.error("At least one tag is required")
        
    
    return (options, args)

def main():
    """ Method to run if executed as script. """
    
    options, args = parse_options()
    
    if options.fetch: # get URLs and data
        directory = os.path.abspath(options.directory)
        
        if os.path.exists(directory) and os.listdir(directory):
            sys.exit("The target directory must be empty.")
            
        print "Determine number of images to fetch..."
        
        urls = get_urls(args, options.pages)
        number_of_images = [(tag, len(urls[tag])) for tag in urls]
        total = reduce(lambda x,y: x+y, [t[1] for t in number_of_images])
        
        print "Fetching %i images (%s) into %s..." % (total, 
                                                      ', '.join(["%s: %i" % (tag, number) for tag, number in number_of_images]), 
                                                      directory)
        fetch_data(os.path.abspath(options.directory), urls, True)
        
        print "\nAll images fetched."
        
    elif options.analyze: # go to analyzer mode
        if not args:
            path = Repository.get_last() # open last fetched data
        else:
            path = args[0]
        directory = os.path.abspath(path)
        if not os.path.exists(directory):
            sys.exit("The target directoy must exist.")
        rep = Repository(directory)
        
        # load analyzer
        analyser = [get_class(m)(rep) for m in settings.ANALYZERS]
        
        _cmd = AnalyzerCmd(rep, analyser)
        try:
            _cmd.cmdloop("here we go...")
        except KeyboardInterrupt:
            print "uh uh"

if __name__ == '__main__':
    from optparse import OptionParser, OptionGroup
    main()