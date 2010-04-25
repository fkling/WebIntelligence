#!/usr/bin/env python
'''
Created on Apr 16, 2010

@author: kling
'''
import threading
from image_loader import flickr, storage
from optparse import OptionParser


usage = """usage: %prog [options] tag1 [tag2, ...]"""

parser = OptionParser(usage=usage)

parser.add_option('-d', '--dir', action='store', type='string', dest='directory',
                  default='flickr-analysis', metavar='DIR',
                  help='the destination directory [default: ~/%default]')

parser.add_option('-p','--pages', action='store', type='int', dest='pages',
                  default=1,
                  help='number of pages to get the images from [default: %default]')


(options, args) = parser.parse_args()

if not args:
    parser.error("at least one tag is required")

total = 0
storage.FileStorage(options.directory)

class Mythread(threading.Thread):
    
    def __init__(self, tag):
        self.tag = tag
        
        threading.Thread.__init__(self)
        
    def run(self):
        from image_loader import storage
        storage = storage.FileStorage(options.directory)
        print 'Fetching information for tag %r...' % name
        tag = flickr.Tag(self.tag)
        photos = tag.get_thumbs(options.pages)
        print '%s: %i images fetched.' % (self.tag, len(photos))
        print '%s : saving to: %s' % (self.tag, storage.dir)
        storage.save(tag)
        print '%s: done.' % self.tag

for name in args:
    Mythread(name).start()



    