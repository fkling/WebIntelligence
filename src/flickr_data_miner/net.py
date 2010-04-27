'''
Created on Apr 26, 2010

@author: kling
'''

import threading, urllib2

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
            f = urllib2.urlopen(self.page_url)
            self.page = f.read()
            f.close()
            f = urllib2.urlopen(self.image_url)
            self.image = f.read()
            f.close()
            self.has_result = True
        except IOError:
            print "Could not open document: %s" % self.url
