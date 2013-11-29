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

import time, socket, sys, os, stat, threading 
from multiprocessing import Queue
import logging
import tolholiday

from twitter.oauth_dance import oauth_dance
import twitter

from tweepy import OAuthHandler
from tweepy import API
from tweepy import TweepError

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
tolapi = None
updater = None
backoff = 0
BACKOFF_MAX = 600 # Ten minutes backoff

# Here are the render thingies.
#
curr_render = {}			# The list of current shapes being rendered, with timestamps
wait_list = []				# The list of shapes waiting to be rendered

class tolAPImcast:
	"""Handles multicast transmission to the connected strings"""

	MCAST_GRP = '224.0.0.249'
	MCAST_PORT = 9393
	MCAST_PKT_SIZE = 4320
	#BIND_IP_ADDR = "192.168.0.2"			# This is evil and we need a generalized solution thingy
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

class tolAPIpipe:
	"""Writes to pipe which handles transmission to the connected strings"""

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

		return

	def transmit(self, buffer):
		"""Write to the named pipe."""

		if (len(buffer) == self.BUFFER_SIZE):	# Only if it's the right lenght, precisely
			try:
				count = os.write(self.pipedesc, buffer)
				#printme("Wrote %d bytes to pipe" % count)
			except OSError as e:
				logging.critical("Could not write to named pipe. Reason: %s" % e)

		return

def makeRGB(hexcolor):
	"""Returns RGB tuple from hex color value"""
	r = (hexcolor & 0xff0000) >> 16
	g = (hexcolor & 0x00ff00) >> 8
	b = (hexcolor & 0xff)
	return (r,g,b)

def alert_twitter(username):
	"""Use Twitter to send alert to user that their colour is about to come up."""
	global tweepy_api, backoff, BACKOFF_MAX

	if ((time.time() - backoff) < BACKOFF_MAX):		# Are we backing off?
		return 							

	# We add a timestamp in order to make the tweet unique for Twitter, or else it gets cranky
	ts = int(time.time())
	the_tweet = u"""@%s It's your time to shine! #christmasconversations #santafest #%d""" % (username,ts)
	logging.debug(the_tweet)
	try:
		tweepy_api.update_status(the_tweet, lat=-33.872932, long=151.199453, display_coordinates=True)
	except TweepError as e:
		try:
			if e[0]['code'] == 185:
				logging.debug("Too many updates to Twitter, backing off...")
				backoff = time.time()
			else:
				logging.error("Update failed with error %s, could not notify %s" % (e,username))
		except:
			logging.error("Update failed, couldn't even parse error code %s" % e)
	return

def render():
	"""Rendering routine.  Takes stuffs off the queue and does stuffs with it."""
	global hol, tolapi

	# We  walk the curr_render dictionary, and render each entry to the buffer
	#
	for a_shape in curr_render:
		((shape_data, colorval, user), timestamp) = curr_render[a_shape]

		# Now render the colors onto those holidays
		rgb = makeRGB(colorval)
		for string_number in shape_data[1]:
			logging.debug("Writing to string %d" % string_number)
			hol.fill(string_number, rgb[0], rgb[1], rgb[2])

	# Now that we have everything, render to a byte array and send it out
	pkt = hol.render()
	tolapi.transmit(pkt)
	return

class ShapeUpdater(object):
	"""This object is used to keep track of the queue of shapes waiting to be displayed"""

	def check_queue(self):
		"""This thread checks the wait_list to see if shapes should move into the curr_render list."""
		global wait_list, curr_render

		while True:
			time.sleep(self.SCANTIME)			# Sleep for predetermined time
			if (len(wait_list) > 0):			# Only if there's something on the list do we bother
				changed = False
				current_timestamp = time.time()
				logging.debug("Checking queue")
				i = 0
				while (i < len(wait_list)):
					shape_name = wait_list[i][0]	# Get the shape name waiting
					try:
						curr_entry = curr_render[shape_name]
					except KeyError:
						logging.error("Shape not in curr_render, how can this be?")
						continue
					if current_timestamp - curr_entry[1] > 15:	# 15 seconds have passed?
						curr_render[shape_name] = (wait_list[i][1], time.time())		# Update the render info
						changed = True
						alert_twitter(wait_list[i][1][2])		# Send an alert to the user that their shape has come up
						wait_list.pop(i)						# And remove from the wait list - DOES THIS SCREW THINGS UP?
						logging.debug("Popping %s from wait_list" % shape_name)
						# We don't increment the counter in this case because the list got smaller
					else:
						i = i + 1			# List hasn't gotten smaller, so we increment the list here.
				if changed == True:
					render()									# If things have changed, render to the strings

	def __init__(self):
		"""Set up the data structures for the ShapeUpdater object"""
		# Will likely read whitelist and blacklist in from file system
		self.SCANTIME = 5       # 5 seconds between scans

		# And start the cleaner thread
		self.checker = threading.Thread(target=self.check_queue)
		self.checker.start()

		return

def process_queue(queue_object):
	"""We get a queue object, and determine whether it goes out immediately onto the render display
	Or if it goes into the wait queue, while we wait for the currently rendered shape to finish up."""
	global wait_list, curr_render

	(shape_data, colorval, user) = queue_object
	printme("renderer --> shape_data: %s, colorval 0x%06x" % (shape_data, colorval))

	# Ok so the first element of shape_data should be the shape name.
	# If that is already in curr_render, it needs to go on the wait_list
	# Otherwise it gets put onto curr_render with a timestamp, then rendered.
	shape_name = shape_data[0]
	if shape_name in curr_render:	# Is it already in a slot?
		wait_packet = (shape_name, queue_object, time.time())
		wait_list.append(wait_packet)
		logging.debug("Already displaying %s, appended to wait_list" % shape_name)
	else:		# Add it to the list of stuffs being rendered now
		curr_render[shape_name] = (queue_object, time.time())
		logging.debug("Shape %s going onto the curr_render list" % shape_name)
		alert_twitter(user)
		render()		# And force a render of the curr_render list

	return

def run(render_queue):
	"""So this can be loaded as a module and run via multiprocessing"""
	global rend_queue, hol, tolapi, consumer_key, consumer_secret, tweepy_api, updater
	rend_queue = render_queue

	# Log into Twitter, get credentials.	
	tokens = twitter.oauth.read_token_file(fn)
	logging.debug("We have authorization tokens in the renderer")

	auth = OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(tokens[0], tokens[1])

	# Setup an API thingy
	try:
		tweepy_api = API(auth)
		logging.debug("Got API of %s" % tweepy_api)
		logging.debug("We have the API for tweepy in the renderer")
	except:
		logging.critical("Failed to get the API for tweepy in the renderer!")

	# Instance  the holiday object and the api object and the queue updater object
	hol = tolholiday.tolHoliday()
	tolapi = tolAPIpipe()				# use tolAPImcast for direct multicast
	updater = ShapeUpdater()

	while True:
		# Check the command parser queue for messages
		if rend_queue.empty() == False:
			process_queue(rend_queue.get())
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
