#!/usr/bin/python
#
"""Darling Harbour Tree-of-Light Light Tester

This module lights individual strings for testing

Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""
__author__ = 'Mark Pesce'
__version__ = '1.0a1'
__license__ = 'MIT'

import time, socket, sys
import logging
import tolholiday

hol = None
api = None

class tolAPI:
	"""Handles multicast transmission to the connected strings"""

	MCAST_GRP = '224.0.0.249'
	MCAST_PORT = 9393
	MCAST_PKT_SIZE = 4320
	#BIND_IP_ADDR = "192.168.0.20" # This is evil and we need a generalized solution thingy
	sock = None

	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		#self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
		#self.sock.bind((self.BIND_IP_ADDR, self.MCAST_PORT))		# Or else it doesn't work, I've learned.

	def transmit(self, pkt):
		if len(pkt) != self.MCAST_PKT_SIZE:
			logging.error("Bad multicast packet size! Ignoring.")
			return

		self.sock.sendto(pkt, (self.MCAST_GRP, self.MCAST_PORT))
		return

def makeRGB(hexcolor):
	"""Returns RGB tuple from hex color value"""
	r = (hexcolor & 0xff0000) >> 16
	g = (hexcolor & 0x00ff00) >> 8
	b = (hexcolor & 0xff)
	return (r,g,b)

def printme(str):
	"""A print function that can switch quickly to logging"""
	#print(str)
	logging.debug(str)

if __name__ == '__main__':	
	logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	printme('Logging initialized')
	printme("Running light test module from the command line.")

	# Parse us some command line goodness
	#
	if len(sys.argv) < 2:
		logging.critical("Usage: python light.py <string_num> [hexcolor]")
		sys.exit(1)
	string_num = int(sys.argv[1])

	if len(sys.argv) > 2:
		cvs = int(sys.argv[2],16)
	else:
		cvs = 0xffffff # white
	(r, g, b) = makeRGB(cvs)

	# Ok, so lets instance everything so nothing breaks badly
	#
	hol = tolholiday.tolHoliday()
	api = tolAPI()

	# At this point we're free to do whatever tests our heart desires.  Sorta.
	hol.fill(string_num, r, g, b)
	pkt = hol.render()
	api.transmit(pkt)
	printme("Just sent [%02x, %02x, %02x] to string %d." % (r, g, b, string_num))



