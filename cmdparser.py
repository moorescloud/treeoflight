#!/usr/bin/python
#
"""Darling Harbour Tree-of-Light Command Parser Module

This module parses commands received, translating them into renderings

It has two queues, an inbound from the Twitter listener, an outbound to the Renderer.

Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""
__author__ = "Mark Pesce"
__version__ = "1.0a1"
__license__ = "MIT"

import time, logging
from multiprocessing import Queue

parse_queue = None
rend_queue = None

# The shape names as defined by Roger Foley-Fogg
# Mapping them onto some sort of something that means something to the rendering bit
# These mappings will change when we get on-site
#
shapes = { "crown": [ "crown", (0, 1, 2) ], "ho": [ "ho", (3, 4, 5) ], "eye": [ "eye", (6, 7, 8)], 
"heart": [ "heart", (9, 10, 11) ], "x": [ "x", (12, 13, 14) ], "cross": [ "cross", (15, 16, 17) ], 
"cloud": [ "cloud", (18, 19, 20) ], "u": [ "u", (21, 22, 23) ], "star": [ "star", (24, 25, 26) ] }

# Start with these and add more later
#
colordict = { "red": 0xff0000, "green": 0x00ff00, "blue": 0x0000ff, "orange": 0xff8000, "yellow": 0xffff00, 
"cyan": 0x00ffff, "purple": 0xFF00FF, "pink": 0xFF3030, "white": 0xffffff }


def parse(queue_object):
	"""Run the parser on the object that"s been received from the command parser queue"""
	global rend_queue

	(user, msg) = queue_object

	# Ugh.  A parser.  How long I"ve avoided this crap. And now we meet again.
	# The basic line is "@DarlingHabourTree <shape> <color>"
	# Let"s get this parsing, then we can get fancier later.

	# Ok let"s split the line into a list of lower-case elements
	elements = msg.lower().split(" ")
	logging.debug(elements)
	if elements[0] != "@darlingxmastree":
		logging.debug("Rejected, not addressed to us")
		return False

	if elements[1] in shapes:
		logging.debug("We have a shape match of %s" % shapes[elements[1]])
	else:
		logging.debug("No shape match")
		return False

	# Now is this a colour name or a hex color value?
	if elements[2] in colordict:
		logging.debug("We got colour %s" % colordict[elements[2]])
		cv = int(colordict[elements[2]])
		logging.debug(cv) 
	else:
		if elements[2][0] == "#":
			try:
				logging.debug("We got a hex colour value")
				logging.debug( elements[2][1:] )
				cv = int(elements[2][1:], 16)
				logging.debug(cv)
			except:
				logging.error("Some weird conversion error, ignoring")
				return False
		else:
			logging.debug("No colour match")
			return False

	# At this point we should have correctly parsed the shape and color values. We hope.
	# Now we need to do something with them.
	rend_queue.put([shapes[elements[1]], cv, user])
	return True


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

if __name__ == "__main__":	
	logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
	logging.debug('Logging initialized')
	logging.debug("Running cmdparser module from the command line for unit tests and stuff.")
	rend_queue = Queue()			# We don't do this if we're running as a module

	parse(("test", "@DarlingXmasTree crown green"))
