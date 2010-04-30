'''
Created on Apr 26, 2010

@author: kling
'''

import threading, urllib2
from contextlib import closing

class FileGetter(threading.Thread):
    def __init__(self, id, tag, page, image):
        self.page_url = page
        self.image_url = image
        self.tag = tag
        self.id = id
        self.page = None
        self.image = None
        self.has_result = False
        threading.Thread.__init__(self)

 
    def run(self):
        try:
            with closing(urllib2.urlopen(self.page_url)) as page:
                self.page = page.read()

            with closing(urllib2.urlopen(self.image_url)) as image:
                self.image = image.read()

            self.has_result = True
        except IOError:
            print "Could not open URL: %s" % self.page_url
