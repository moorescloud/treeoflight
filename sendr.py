#!/usr/bin/python
#
"""This module sends packets to the named pipe /run/multicastr.pipe 
   The data must be *precisely* 4320 bytes in length.  
   If it isn't, forget it.

   Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""
__author__ = 'Mark Pesce'
__version__ = '1.0a1'
__license__ = 'MIT'

import os, sys, stat, socket, logging, errno, time, random
import tolholiday

class TxDataPipe(object):
	"""Class to handle writing to a named pipe sitting in /run"""

	pipename = '/run/multicastr.pipe'
	BUFFER_SIZE = 4320

	def __init__(self):
		"""Open the named pipe."""

		try:
			self.pipedesc = os.open(self.pipename, os.O_WRONLY)
		except OSError, e:
			logging.critical("Could not open named pipe. Reason: %s" % e)
			self.pipedesc = None
		return			

	def close(self):
		"""Closes the named pipe"""

		try:
			os.close(self.pipedesc)
			self.pipedesc = None
		except OSError, e:
			logging.critical("Could not close named pipe. Reason: %s" % e)
			sys.exit(1)	
		return

	def write(self, buffer):
		"""Write to the named pipe."""

		if (len(buffer) == self.BUFFER_SIZE):	# Only if it's the right lenght, precisely
			try:
				count = os.write(self.pipedesc, buffer)
				#printme("Wrote %d bytes to pipe" % count)
			except OSError as e:
				logging.critical("Could not write to named pipe. Reason: %s" % e)

		return

def printme(str):
	"""A print function that can switch quickly to logging"""
	#print(str)
	logging.debug(str)

if __name__ == '__main__':
	logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	printme('Logging initialized')
	printme("Running sendr module from the command line.")

	thePipe = TxDataPipe()
	hol = tolholiday.tolHoliday()

	# At this point we're free to do whatever tests our heart desires.  Sorta.
	while(True):
		for i in range(27):
			hol.fill(i, random.randint(0,255),random.randint(0,255),random.randint(0,255))
		pkt = hol.render()
		thePipe.write(pkt)
		time.sleep(0.02)
	printme("Should be clear now.")

