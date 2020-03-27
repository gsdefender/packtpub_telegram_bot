# -*- coding: utf-8 -*-
#
# packtfree_telegram_bot - Receive Packt Publishing Ltd. Free Learning updates in Telegram each day
# Copyright (c) 2016-2020 Emanuele Cipolla <emanuele@emanuelecipolla.net>

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),.
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,.
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,.
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER.
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from selenium import webdriver
import html2text
import pickle
import os.path
# This URL can (will?) change:
_FREE_LEARNING_PAGE = "https://packtpub.com/free-learning"
_BOOK_INFO_PICKLE_FILE = 'book_info.pickle'

def get_book_info(force=False):
	if not os.path.isfile(_BOOK_INFO_PICKLE_FILE) or force is True:
		driver = webdriver.Chrome()
		driver.get( _FREE_LEARNING_PAGE )

		product_img = driver.find_element_by_class_name("product__img")
		image_url = product_img.get_attribute('src')
		title = product_img.get_attribute('alt')
		product_info = driver.find_element_by_class_name("product__info")

		description = html2text.html2text(product_info.get_attribute('innerHTML').replace("\n","").replace("\r",""))

		book_info_dict = dict(error=False,title=title,image=image_url,description=description)

		with open(_BOOK_INFO_PICKLE_FILE, 'wb') as handle:
			pickle.dump(book_info_dict, handle)
	else:
		with open(_BOOK_INFO_PICKLE_FILE, 'rb') as handle:
			book_info_dict = pickle.load(handle)

	return book_info_dict
