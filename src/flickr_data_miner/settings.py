'''
Created on Apr 26, 2010

@author: kling
'''

BASE_URL = 'http://flickr.com'
SEARCH_URL = BASE_URL + '/search/?q={tags}&m=tags&s=int&page={page}'

THUMBNAIL_LINK_SELECTOR = '#ResultsThumbsDiv .photo_container a'

ANALYZERS = (
"flickr_data_miner.analyzer.BasicImageAnalyzer",   # <- never remove this one!
"data_analyzer.tag_analyzer.TagAnalyzer",
"data_analyzer.comment_analyzer.CommentAnalyzer",
"data_analyzer.rating_analyzer.RatingAnalyzer",
)
