# -*- coding: utf-8 -*-
#
# packtfree_telegram_bot - Receive Packt Publishing Ltd. Free Learning updates in Telegram each day
# Copyright (c) 2016 Emanuele Cipolla <emanuele@emanuelecipolla.net>

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),.
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,.
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,.
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER.
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import httplib2
from PIL import Image
from StringIO import StringIO
from bs4 import BeautifulSoup
import re
import html2text
import cPickle as pickle
from datetime import datetime
import delorean
import urllib
# This URL can (will?) change:
free_learning_page = "https://www.packtpub.com/packt/offers/free-learning"

def get_book_info(base_page=free_learning_page):
	epoch = delorean.Delorean(datetime.utcnow(), timezone="UTC").truncate('day').epoch
	http = httplib2.Http('.freelearning_cache')
	
	try:
		book_info_response, book_info_html = http.request( base_page )
		book_info_soup = BeautifulSoup(book_info_html,"lxml")
		
		image_url = 'http:'+book_info_soup.find("img", {"class":"bookimage"})['src']
		# 1. Value types

		title = re.sub('\n', '', re.sub('\t', '',  book_info_soup.find("div", {"class":"dotd-title"}).find("h2").text)) 
	
		image_filename = '.freelearning_cache/book_image_'+str(epoch)+'.jpg'
		
		if book_info_response.fromcache is False:
    		    urllib.urlretrieve(image_url, image_filename) # why can't httplib2 fetch this?
			
		description_haystack =  book_info_soup.find("div", {"class":"dotd-main-book-summary"}).findAll("div")
		description = ''
		
		for description_needle in description_haystack:
			if not description_needle.has_attr("class"):
				description += html2text.html2text(description_needle.text)
			
		book_info_dict = dict(error=False,title=title,image=image_filename,description=re.sub("\n",' ',description))	
		return book_info_dict
	except httplib2.ServerNotFoundError:
		return dict(error=True,title="Error",image="",description="Unable to open URL: "+base_page)