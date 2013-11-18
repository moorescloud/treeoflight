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

import sys, time, os.path

# setup the logging which will eventually be quite sophisticated
#
import logging
logfilename = os.path.join("log", "tol-%s.txt" % str(int(time.time())))
#logging.basicConfig(filename=logfilename, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.DEBUG)
logging.debug('Logging initialized')

# Multiprocessing requires Python 2.6 or better
v = sys.version_info
if v[0] != 2 or v[1] < 6:
	logging.critical("tol requires Python 2.6.x or Python 2.7.x -- aborting")
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


	logging.debug("Everything should be starting up now...")

	# Now we wait.  When we get a control-C, we exit -- hopefully.
	while True:
		try:
			time.sleep(.1)
		except KeyboardInterrupt:
			logging.debug("\nTerminating simulator...")
			tlp.terminate()
			cpp.terminate()
			rnp.terminate()
			logging.debug("Exiting.")
			sys.exit(0)

