#!/usr/bin/python
#
"""Darling Harbour Tree-of-Light Command Parser Module

This module parses commands received, translating them into renderings

It has two queues, an inbound from the Twitter listener, an outbound to the Renderer.

Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""
__author__ = 'Mark Pesce'
__version__ = '1.0a1'
__license__ = 'MIT'

import time 
from multiprocessing import Queue

parse_queue = None
rend_queue = None

def parse(queue_object):
	"""Run the parser on the object that's been received from the command parser queue"""
	(user, msg) = queue_object

	# Ugh.  A parser.  How long I've avoided this crap. And now we meet again.

	return


def run(parser_queue,render_queue):
	"""So this can be loaded as a module and run"""
	global parse_queue, rend_queue
	parse_queue = parser_queue
	rend_queue = render_queue

	while True:
		# Check the command parser queue for messages
		if parse_queue.empty() == False:
			parse(parse_queue.get())
		time.sleep(.025)

if __name__ == '__main__':	
	print "Running cmdparser module from the command line."
