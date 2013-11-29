#!/usr/bin/python
#
"""This module listens to the named pipe /run/multicastr.pipe 
   and sends data to the Holidays at 224.0.0.249:9393
   if the data is *precisely* 4320 bytes in length.  
   If it isn't, forget it.

   Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""
__author__ = 'Mark Pesce'
__version__ = '1.0a1'
__license__ = 'MIT'

import os, sys, stat, socket, logging, errno, time

class DataPipe(object):
	"""Class to handle reading of a named pipe sitting in /run"""

	pipename = '/run/multicastr.pipe'
	BUFFER_SIZE = 4320

	def __init__(self):
		"""Create and open the named pipe, set the permissions, etc"""

		try:
			os.mkfifo(self.pipename)
		except OSError, e:
			logging.critical("Could not create named pipe. Reason: %s" % e)
			if e.errno == errno.EEXIST:
				logging.critical("File exists, so we'll skip creating it.")
			else:
				sys.exit(1)

		try:
			os.chmod(self.pipename, stat.S_IREAD|stat.S_IWRITE|stat.S_IRGRP|stat.S_IWGRP|stat.S_IROTH|stat.S_IWOTH)
		except OSError, e:
			logging.critical("Could not change permissions on named pipe. Reason: %s" % e)
			sys.exit(1)		

		try:
			self.pipedesc = os.open(self.pipename, os.O_RDONLY|os.O_NONBLOCK)
		except OSError, e:
			logging.critical("Could not open named pipe. Reason: %s" % e)
			sys.exit(1)			

	def close(self):
		"""Closes the named pipe"""

		try:
			os.close(self.pipedesc)
			self.pipedesc = None
		except OSError, e:
			logging.critical("Could not close named pipe. Reason: %s" % e)
			sys.exit(1)	

	def read(self):
		"""Read the named pipe, try to do this non-blockingly"""

		try:
			buffer = os.read(self.pipedesc, self.BUFFER_SIZE)
			#printme("Read %d bytes from pipe" % len(buffer))
		except OSError as err:
			if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
				buffer = None
			else:
				raise  # something else has happened -- better reraise

		return buffer

class McastSocket(object):
	"""Class to handle transmission of data frame to the mulitcast address that all the Holidays listen to"""

	MCAST_GRP = '224.0.0.249'
	MCAST_PORT = 9393
	MCAST_PKT_SIZE = 4320			# That's 27 frames of 160 bytes

	def __init__(self):
		"""Try and open the socket we'll use for mulitcast comms"""

		try:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		except socket.error as e:
			logging.critical("Could not create socket. Reason: %s" % e)
			sys.exit(1)

	def transmit(self, pkt):
		"""Transmit the packet to the mulitcast address"""

		if len(pkt) != self.MCAST_PKT_SIZE:
			logging.error("Bad multicast packet size! Ignoring.")
			return

		try:
			self.sock.sendto(pkt, (self.MCAST_GRP, self.MCAST_PORT))
		except socket.error as e:
			logging.error("Could not transmit multicast frame. Reason: %s" % e)
		return		

def run():
	"""In case we happen to put this in a thread or multiprocessing or something?"""

	thePipe = DataPipe()
	theSocket = McastSocket()

	# While forever, check the data pipe, if there's stuffs in it, send it out.
	while (True):
		pkt = thePipe.read()
		if (pkt != None):
			if (len(pkt) > 0):
				theSocket.transmit(pkt)
			else:
				time.sleep(0.01)
		else:
			time.sleep(0.01)			# Scan at 100hz otherwise

def printme(str):
	"""A print function that can switch quickly to logging"""
	#print(str)
	logging.debug(str)

if __name__ == '__main__':
	logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	printme('Logging initialized')
	printme("Running multicastr module from the command line.")
	run()





