'''
Created on Jun 27, 2010

'''
import urllib2

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

def upload_file(file, url, fieldname):
    """ Uploads a file to an URL.
    
        INPUT:
            - file: The path to the file
            - url: The URL to upload the file to
            - fieldname: The name of the corresponding formfield
            
        OUPUT:
            The source of the response page
    """
    
    # Register the streaming http handlers with urllib2
    register_openers()

    # Start the multipart/form-data encoding of the file
    # "image" is the name of the parameter, which is normally set
    # via the "name" parameter of the HTML <input> tag.
    #
    # headers contains the necessary Content-Type and Content-Length
    # datagen is a generator object that yields the encoded parameters
    datagen, headers = multipart_encode({fieldname: open(file, "rb")})
    
    
    # Create the Request object
    request = urllib2.Request(url, datagen, headers)
    
    # Actually do the request, and get the response
    response = urllib2.urlopen(request).read()
    
    return response