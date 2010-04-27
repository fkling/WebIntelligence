#!/usr/bin/env python
'''
Created on Apr 16, 2010

@author: kling
'''
import threading, os, sys, urllib2
import settings
from storage import Repository
from net import FileGetter
from util import ProgressBar
from optparse import OptionParser, OptionGroup
import lxml.html
from Queue import Queue


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
            print "Fetching %i images..." % total_files
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
    pass

def main():
    pass
        


if __name__ == '__main__':
    print "Determine nubmer of images to fetch..."
    urls = get_urls(('sexy',), 1)
    fetch_data('/Users/kling/test2', urls, True)
    print "\n All images fetched."