#!/usr/bin/env python
'''
Created on Apr 16, 2010

@author: kling
'''
import threading, os, sys, urllib2, cmd
from datetime import datetime
from Queue import Queue

import settings
from storage import Repository
from net import FileGetter
from util import ProgressBar, get_class
import lxml.html



def get_urls(tags=None, pages=1):
    if not tags:
        return
    
    result = dict()
    for tag in tags:
        l = list()
        for page in range(1,pages+1):
            source = urllib2.urlopen(settings.SEARCH_URL.format(tags=tag, page=page)).read()
            dom = lxml.html.document_fromstring(source)
            for link in dom.cssselect(settings.THUMBNAIL_LINK_SELECTOR):
                # get and fetch page_url
                page_link = settings.BASE_URL + link.get('href')
                name = page_link.split('/')[-2]
                image_link = link.find('img').get('src')
                l.append((name, page_link, image_link))
        result[tag] = l
    return result
                


def fetch_data(dir, tags=None, print_progress=False):
    if not tags:
        return
    
    repository = Repository(dir, new=True)
    
    def producer(q, tags):
        for tag in tags:
            for name, page_url, image_url in tags[tag]:
                thread = FileGetter(name, tag, page_url, image_url)
                thread.start()
                q.put(thread, True)
    
    def consumer(q, rep, total_files, print_progress):
        if print_progress:
            bar = ProgressBar(total_files)
                
        counter = 0
        while counter < total_files:
            thread = q.get(True)
            thread.join()
            if thread.has_result:
                rep.add_site(thread.tag, thread.id, thread.page)
                rep.add_image(thread.tag, thread.id, thread.image)
            counter += 1;
            bar.add()
            if print_progress:
                sys.stdout.write("%i%% %r fetched %i of %i \r" %( counter*100/total_files, bar, counter, total_files))
                sys.stdout.flush()
            
    q = Queue(20)
    prod_thread = threading.Thread(target=producer, args=(q, tags))
    total = reduce(lambda x,y: x+y, [len(tags[tag]) for tag in tags])
    cons_thread = threading.Thread(target=consumer, args=(q, repository, total, print_progress))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    

def parse_options():
    
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
    group.add_option('-d', '--dir', action='store', type='string', dest='directory',
                      default=os.path.join(os.path.expanduser('~'), 'flickr-analysis', now.strftime('%Y-%m-%d_%H-%M')), metavar='DIR',
                      help='the destination directory [default: %default]')
    
    parser.add_option_group(group)
    
    
    (options, args) = parser.parse_args()
    
    
    if not options.fetch and not options.analyze:
        parser.error("See usage...")
    
    
    if options.fetch and not args:
        parser.error("At least one tag is required")
    elif options.analyze and not args:
        parser.error("A path to a valid repository is reqired")
        
    
    return (options, args)

def main():
    options, args = parse_options()
    
    if options.fetch:
        directory = os.path.abspath(options.directory)
        if os.path.exists(directory) and os.listdir(directory):
            sys.exit("The target directoy must be empty.")
            
        print "Determine number of images to fetch..."
        urls = get_urls(args, options.pages)
        number_of_images = [(tag, len(urls[tag])) for tag in urls]
        total = reduce(lambda x,y: x+y, [t[1] for t in number_of_images])
        print "Fetching %i images (%s) into %s..." % \
        (total, ', '.join(["%s: %i" % (tag, number) for tag, number in number_of_images]), directory)
        fetch_data(os.path.abspath(options.directory), urls, True)
        print "\nAll images fetched."
        
    elif options.analyze:
        directory = os.path.abspath(args[0])
        if not os.path.exists(directory):
            sys.exit("The target directoy must exist.")
        rep = Repository(directory)
        
        analyser = [get_class(m)(rep) for m in settings.ANALYZERS]
        
        _cmd = AnalyzerCmd(analyser)
        _cmd.cmdloop("here we go...")
        

class AnalyzerCmd(cmd.Cmd, object):
    def __init__(self, analyzers, completekey='Tab'):
        self.analyzers = dict()
        for a in analyzers:
            self.analyzers[a.NAME] = a
        self.context = None
        cmd.Cmd.__init__(self, completekey)
        self.prompt = '> '
        
    def do_exit(self, line):
        """ Exits the programm."""
        return True
    
    def precmd(self, line):
        if line in self.analyzers:
            line = 'a ' + line
        return line
    
    def default(self, line):
        if self.context:
            self.context.onecmd(line)
        else:
            print "**ERROR** no such command"
    
    def do_a(self, line):
        """ Usage: a <analyzer>. Load analyzer <analyzer>."""
        
        if line in self.analyzers:
            self.context = self.analyzers[line]
            if self.context.needs_init():
                init = ''
                while init.lower() != 'no' and init.lower() != 'yes':
                    init = raw_input("The analyzer %s is not yet initialized\nInitialize now? (yes/no)")
                if init.lower() == 'yes':
                    self.context.initialize()
                    self.prompt = ('(a:%s)> ' % self.context.NAME)
                else:
                    self.context = None
            else:
                self.prompt = ('(a:%s)> ' % self.context.NAME)
        else:
            print "**ERROR** Analyzer %s is not available" % line
            
    def do_alist(self, line):
        """ List all available analyzer. """
        
        print '\nAvailable analyzers:\n'
        for a in self.analyzers:
            print " - %s\t\t %s" %(a, self.analyzers[a].__doc__.splitlines()[0])
        print ''
            
    def do_help(self, line):
        """ Prints the help. """
        
        if self.context:
            self.context.do_help(line)
        else:
            super(AnalyzerCmd, self).do_help(line)
            
    def do_return(self, line):
        """ Return from analyzer. """
        
        if self.context:
            self.context = None
            self.prompt = '> '

if __name__ == '__main__':
    from optparse import OptionParser, OptionGroup
    main()