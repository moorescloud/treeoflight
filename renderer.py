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

import time, socket, sys
from multiprocessing import Queue
import logging
import tolholiday

rend_queue = None
hol = None
api = None

class tolAPI:
	"""Handles multicast transmission to the connected strings"""

	MCAST_GRP = '224.0.0.249'
	MCAST_PORT = 9393
	MCAST_PKT_SIZE = 4320
	sock = None

	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)		

	def transmit(self, pkt):
		if len(pkt) != self.MCAST_PKT_SIZE:
			logging.error("Bad multicast packet size! Ignoring.")
			return

		self.sock.sendto(pkt, (self.MCAST_GRP, self.MCAST_PORT))
		return

def render(queue_object):
	"""Rendering routine.  Takes stuffs off the queue and does stuffs with it."""
	(shape_data, colorval) = queue_object
	printme("shape_data: %s, colorval 0x%06x" % (shape_data, colorval))
	return

def run(render_queue):
	"""So this can be loaded as a module and run via multiprocessing"""
	global rend_queue, hol, api
	rend_queue = render_queue

	# Instance both the holiday object and the api object
	hol = tolholiday.tolHoliday()
	api = tolAPI()

	while True:
		# Check the command parser queue for messages
		if rend_queue.empty() == False:
			render(rend_queue.get())
		time.sleep(.025)

def printme(str):
	"""A print function that can switch quickly to logging"""
	#print(str)
	logging.debug(str)

if __name__ == '__main__':	
	logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	printme('Logging initialized')
	printme("Running renderer module from the command line.")

	# Ok, so lets instance everything so nothing breaks badly
	#
	rend_queue = Queue()
	hol = tolholiday.tolHoliday()
	api = tolAPI()

	# At this point we're free to do whatever tests our heart desires.  Sorta.
	hol.fill(0, 0x80, 0, 0)
	pkt = hol.render()
	for i in range(5):
		api.transmit(pkt)
		time.sleep(.1)
	printme("We should have transmitted 5 packets.  Hopefully.")