#!/usr/bin/python
#
"""Darling Harbour Tree-of-Light

Main project file, this is what gets invoked
It uses Python multiprocessing to spawn three proccesses

	a) Twitter listener
	b) Command parser
	c) Renderer

Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""
__author__ = 'Mark Pesce'
__version__ = '1.0a1'
__license__ = 'MIT'

import sys, time
import ConfigParser

# Multiprocessing requires Python 2.6 or better
v = sys.version_info
if v[0] != 2 or v[1] < 6:
	print("holideck requires Python 2.6.x or Python 2.7.x -- aborting")
	sys.exit(0)

from multiprocessing import Process, Queue

import listener
import cmdparser
import renderer

if __name__ == '__main__':

	# Create a Queue instance so the processes can share the datas
	parser_queue = Queue()

	# Start the twitter listener Process
	tlp = Process(name='listener', target=listener.run, kwargs={ 'parser_queue': parser_queue})
	tlp.start()

	render_queue = Queue()

	# Start the parser Process 
	cpp = Process(name='parser', target=cmdparser.run, kwargs={ 'parser_queue': parser_queue, 'render_queue': render_queue })
	cpp.start()

	# Start the renderer Process 
	rnp = Process(name='renderer', target=renderer.run, kwargs={'render_queue': render_queue })
	rnp.start()


	print "Everything should be starting up now..."

	# Now we wait.  When we get a control-C, we exit -- hopefully.
	while True:
		try:
			time.sleep(.1)
		except KeyboardInterrupt:
			print("\nTerminating simulator...")
			tlp.terminate()
			cpp.terminate()
			rnp.terminate()
			print("Exiting.")
			sys.exit(0)

