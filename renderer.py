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

import time, socket, sys, os, stat
from multiprocessing import Queue
import logging
import tolholiday

from twitter.oauth_dance import oauth_dance
import twitter

from tweepy import OAuthHandler
from tweepy import API

# File name for the oauth info
#
# This will work for *NIX systems, not sure for Windows.
#
fn = os.path.join(os.path.expanduser('~'),'.tol-oauth')

# New codes specific for the Tree-of-Light twitter application

consumer_secret=con_secret = "5BOTziGnWOuGRNIWyBknuKck7Rn4gUPgO9EusgKsJhI"
consumer_key=con_key = "Hzj8ndSL6cGEjXOwMltRBQ"

tweepy_api = None
rend_queue = None
hol = None
api = None

class tolAPI:
	"""Handles multicast transmission to the connected strings"""

	MCAST_GRP = '224.0.0.249'
	MCAST_PORT = 9393
	MCAST_PKT_SIZE = 4320
	BIND_IP_ADDR = "192.168.0.2"			# This is evil and we need a generalized solution thingy
	sock = None

	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
		self.sock.bind((self.BIND_IP_ADDR, self.MCAST_PORT))		# Or else it doesn't work, I've learned.

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

def alert_twitter(username):
	"""Use Twitter to send alert to user that their colour is about to come up."""
	global tweepy_api

	the_tweet = u"""@%s It's your time to shine!""" % username
	logging.debug(the_tweet)
	tweepy_api.update_status(the_tweet)
	return

def render(queue_object):
	"""Rendering routine.  Takes stuffs off the queue and does stuffs with it."""
	global hol, api
	(shape_data, colorval, user) = queue_object
	printme("shape_data: %s, colorval 0x%06x" % (shape_data, colorval))

	# At this very first level of implementation, we'll simply send the colour value to the requiste strings.
	# We'll establish a queue soon, and keep things around, etc.
	#
	# The shape data is an array with the shape name, and list of strings mapped to that shape
	#
	rgb = makeRGB(colorval)
	for string_number in shape_data[1]:
		logging.debug("Writing to string %d" % string_number)
		hol.fill(string_number, rgb[0], rgb[1], rgb[2])
	pkt = hol.render()
	alert_twitter(user)
	api.transmit(pkt)
	return

def run(render_queue):
	"""So this can be loaded as a module and run via multiprocessing"""
	global rend_queue, hol, api, consumer_key, consumer_secret, tweepy_api
	rend_queue = render_queue

	# Log into Twitter, get credentials.	
	tokens = twitter.oauth.read_token_file(fn)
	logging.debug("We have authorization tokens in the renderer")

	auth = OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(tokens[0], tokens[1])

	# Setup an API thingy
	#try:
	tweepy_api = API(auth)
	logging.debug("Got API of %s" % tweepy_api)
	logging.debug("We have the API for tweepy in the renderer")
	#except:
	#	logging.critical("Failed to get the API for tweepy in the renderer!")

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
	# hol.fill(0, 0, 0x80, 0)
	# pkt = hol.render()
	# for i in range(5):
	# 	api.transmit(pkt)
	# 	time.sleep(.1)
	# printme("We should have transmitted 5 packets.  Hopefully.")

	qmsg = ([ "crown", (0, 1, 2) ], 0x0000FF)
	render(qmsg)
