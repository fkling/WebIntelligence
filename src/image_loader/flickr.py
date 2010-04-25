'''
Created on Apr 16, 2010

@author: kling
'''
tag_url = 'http://www.flickr.com/photos/tags/%s/?page=%i'
page_url = 'http://flickr.com/%s'



import urllib2, sys
from lxml import etree
from lxml.cssselect import CSSSelector

class Tag(object):
    sel = CSSSelector('#GoodStuff .photo_container a')
    
    def __init__(self, tag):
        self.name = tag
        self.photos = []
        
    def get_thumbs(self, pages=1):
        if not self.photos:
            for i in range(1,pages+1):
                source = urllib2.urlopen(self.get_url(i)).read()
                html = etree.HTML(source)
                for e in self.sel(html):
                    page = e.get('href')
                    src = e.find('img').get('src')
                    self.photos.append(Photo(page, src))
        return self.photos
            
        
    def get_url(self, page=1):
        return tag_url % (self.name, page)


class Photo(object):
     
    def __init__(self, page_url, src):
        self.page_url = page_url.strip(' /')
        self.src = src
        self.id = self.page_url.split('/')[-1]
    
    def get_image(self):
        image = ''
        try:
            sys.stdout.write('Getting image %s...' % self.src)
            image = urllib2.urlopen(self.src).read()
            sys.stdout.write('done.\n')
        except urllib2.HTTPError:
            sys.stdout.write('failed!.\n')
        return image
    
    def get_page(self):
        page = ''
        try:
            sys.stdout.write('Getting page %s...' % self.get_page_url())
            page = urllib2.urlopen(self.get_page_url()).read()
            sys.stdout.write('done.\n')
        except urllib2.HTTPError:
            sys.stdout.write('failed!.\n')
        return page
    
    def get_page_url(self):
        return page_url % self.page_url