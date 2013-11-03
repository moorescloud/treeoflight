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

import time, 
from multiprocessing import Queue

rend_queue = None

def render(queue_object):
	"""Rendering routine.  What it does, I have no clue yet."""
	return

def run(render_queue):
	"""So this can be loaded as a module and run via multiprocessing"""
	global rend_queue
	rend_queue = render_queue

	while True:
		# Check the command parser queue for messages
		if rend_queue.empty() == False:
			render(rend_queue.get())
		time.sleep(.025)

if __name__ == '__main__':	
	print "Running renderer module from the command line."