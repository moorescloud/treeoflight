#!/usr/bin/python
#
"""Darling Harbour Tree-of-Light Twitter Listener Module

This module listens to Twitter, and passes authenticated commands along to the parser.

It has one queues, outbound to the parser.

Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""
__author__ = 'Mark Pesce'
__version__ = '1.0a1'
__license__ = 'MIT'

import time, os, sys, json, threading
from multiprocessing import Queue

# Very sorry -- the OAuth code was written using one module package,
# While the streaming is done using another.  Inefficient, but it works.

from twitter.oauth_dance import oauth_dance
import twitter

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

# File name for the oauth info
#
# This will work for *NIX systems, not sure for Windows.
#
fn = os.path.join(os.path.expanduser('~'),'.tol-oauth')

# New codes specific for the Tree-of-Light twitter application

consumer_secret=con_secret = "5BOTziGnWOuGRNIWyBknuKck7Rn4gUPgO9EusgKsJhI"
consumer_key=con_key = "Hzj8ndSL6cGEjXOwMltRBQ"

# Do we have the correct OAuth credentials?
# If credentials exist, test them.  
# If they fail, delete them.
# If they do not exist or fail, create them.
#
def check_twitter_auth():
	authorized = False
	if os.path.isfile(fn):  # Does the token file exist?
		tokens = twitter.oauth.read_token_file(fn)
		#print 'OAuth tokens exist, will try to authorize with them...'
		twapi = twitter.Twitter(auth = twitter.OAuth(token=tokens[0],
					token_secret=tokens[1],
					consumer_secret=con_secret, 
					consumer_key=con_key))
		try:
			result = twapi.account.verify_credentials()
			twitter_id = result['id']
			twitter_handle = result['screen_name']
			#print 'Good, we seem to be authorized for username %s with id %d' % (twitter_handle, int(twitter_id))
			authorized = twapi
		except twitter.TwitterError as e:
			print "Call failed, we don't seem to be authorized with existing credentials.  Deleting..."
			print e
			os.remove(fn)

	if authorized == False:                   # If not authorized, do the OAuth dance
		print 'Authorizing the app...'
		tokens = oauth_dance(app_name='TreeOfLight', consumer_key=con_key, consumer_secret=con_secret, token_filename=fn)
		os.chmod(fn, stat.S_IRUSR | stat.S_IWUSR)		# Read/write, user-only
		#
		# Get an open API object for Twitter
		#
		twapi = twitter.Twitter(auth = twitter.OAuth(token=tokens[0],
						token_secret=tokens[1],
						consumer_secret=con_secret, 
						consumer_key=con_key))
		try:	# Is this going to work?
			result = twapi.account.verify_credentials()
			twitter_id = result['id']
			twitter_handle = result['screen_name']
			print 'Good, we seem to be authorized for username %s with id %d' % (twitter_handle, int(twitter_id))
			authorized = twapi
		except twitter.TwitterError as e:		# Something bad happening, abort, abort!
			print "Call failed, we don't seem to be authorized with new credentials.  Deleting..."
			print e
			os.remove(fn)
			
	return authorized

class UserVerify(object):
	"""This object is used to keep track of users tweeting the Tree-of-Light
		In order to assure they don't flood the Tree with tweets.

		Right now we'll allow 5 accesses in a 10 minute period.  After that, we block.
		We sin bin them for 15 minutes."""


	def clean_naughtylist(self):
		"""This thread keeps the naughtylist cleaned."""
		while True:
			time.sleep(15)			# Sleep for 15 seconds
			current_timestamp = time.time()
			print "Cleaning naughtylist"
			for naughty in self.naughtylist:
				if (self.naughtylist[naughty] + self.SIN_BIN_SECS) < current_timestamp:	# Time out?
					del self.naughtylist[naughty]			# Remove from list

	def __init__(self):
		"""Set up the data structures for the UserVerify object"""
		# Will likely read whitelist and blacklist in from file system
		self.MAX_HITS = 5       # 5 hits in 10 minutes, max
		self.MAX_SECONDS = 600
		self.SIN_BIN_SECS = 900		# 15 minutes in sin bin

		try:
			f = open('tol-whitelist.json')
			d = f.read()
			self.whitelist = json.loads(d)
			print self.whitelist
		except:
			print "Could not read whitelist"
			self.whitelist = []
		try:
			f = open('tol-blacklist.json')
			d = f.read()
			self.blacklist = json.loads(d)
			print self.blacklist
		except:
			print "Could not read blacklist"
			self.blacklist = []

		self.userlist = {}
		self.naughtylist = {}

		# And start the cleaner thread
		self.cleaner = threading.Thread(target=self.clean_naughtylist)
		self.cleaner.start()

		return

	def test(self, username):
		"""Return True if the user has permission to send a Tweet to the Tree, otherwise false"""

		# Check on always whitelist (moorescloud, Roger, SHFA, etc)
		if self.on_whitelist(username) == True:
			return True

		# Check on blacklist 
		if self.on_blacklist(username) == True:
			return False

		if self.on_naughtylist(username) == True:
			return False

		# Check regular list
		current_timestamp = time.time()
		if username in self.userlist:
			# In the userlist, let's have a look at their statistics
			# Count the number of tweets in the last 10 minutes
			# If more than 5, they go onto the naughtylist
			# datas tuple contains count, last timestamp, first timestamp
			(hit_count, last_timestamp, first_timestamp) = self.userlist[username]
			if ++hit_count > self.MAX_HITS:
				add_naughtylist(username, current_timestamp)
				del self.userlist[username] # delete entry from this list
				return False
			else:
				last_timestamp = current_timestamp
				self.userlist[username] = (hit_count, last_timestamp, first_timestamp)
				return True
		else:
			# We need to insert into the user list
			# Then return True
			self.userlist[username] = (1, current_timestamp, current_timestamp)
			return True

		return True 		# Hope we never get here -- can we?

	def add_naughtylist(self, username, current_timestamp):
		"""Add a user to the sin bin for trying to be too chatty"""
		self.naughtylist['username'] = current_timestamp


	def on_whitelist(self, username):
		"""Return True if on the whitelist"""
		if username in self.whitelist:
			return True
		return False

	def on_blacklist(self, username):
		"""Return true if on the blacklist"""
		if username in self.blacklist:
			return True
		return False

	def on_naughtylist(self, username):
		"""If the user is on the naughtlist, that's extra naughty - we reset their timer"""
		if username in self.naughtylist:
			self.naughtlist[username] = time.time()
			return True
		return False

# Instance the UserVerify object
uv = UserVerify()

class StdOutListener(StreamListener):
	""" A listener handles tweets are the received from the stream. 
		Once received, their passed along for user testing and parsing.
	"""
	def on_data(self, data):
		global uv, cmd_parser_queue

		print "Got data"
		djt = json.loads(data)
		print djt
		try:
			user = djt['username']
			if uv.test(user) == True:
				# Got a good user, we can pass this along to the parser...
				msg = djt['text']
				#print msg
				# Let's enqueue the message to the Command Parser
				cmd_parser_queue.send([user, msg])
				# and we're done here

		except KeyError:
			#print "KeyError, skipping..."
			pass

		return True

	def on_error(self, status):
		print status

cmd_parser_queue = None			# Set up a global variable

def run(parser_queue):
	"""So this can be loaded as a module and run via multiprocessing"""
	global cmd_parser_queue
	cmd_parser_queue = parser_queue

	# Log into Twitter, get credentials.
	try:
		if (check_twitter_auth() == False):
			sys.exit()
		print "Authorized"
	except:
		print "FATAL: Authorization failed, exiting process."
		# We need to figure out what to do to recover from this failure, if it happens.
		sys.exit()
	
	tokens = twitter.oauth.read_token_file(fn)

	l = StdOutListener()
	auth = OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(tokens[0], tokens[1])

	# Set up the stream listener
	stream = Stream(auth, l)	
	# Suspect we need to make a different call here that just gets all mentions
	#stream.filter(track=[self.searchterm])  # Blocking call.  We do not come back.
	stream.userstream()  # Blocking call.  We do not come back.  We think this is right.  Possibly.

	while True:
		print "Where we should never be in the listener -- que?"
		time.sleep(1)

if __name__ == '__main__':	
	print "Running listener module from the command line."



