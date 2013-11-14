#!/usr/bin/python
#
"""Darling Harbour Tree-of-Light Twitter Login Module

Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""
__author__ = 'Mark Pesce'
__version__ = '1.0a1'
__license__ = 'MIT'

import time, os, stat, sys, logging

# Very sorry -- the OAuth code was written using one module package,
# While the streaming is done using another.  Inefficient, but it works.

from twitter.oauth_dance import oauth_dance
import twitter

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
			logging.debug("Call failed, we don't seem to be authorized with existing credentials.  Deleting...")
			print e
			os.remove(fn)

	if authorized == False:                   # If not authorized, do the OAuth dance
		logging.debug("Authorizing the app...")
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
			logging.debug("Good, we seem to be authorized for username %s with id %d" % (twitter_handle, int(twitter_id)))
			authorized = twapi
		except twitter.TwitterError as e:		# Something bad happening, abort, abort!
			logging.debug("Call failed, we don't seem to be authorized with new credentials.  Deleting...")
			print e
			os.remove(fn)
			
	return authorized


def run():
	"""So this can be loaded as a module and run via multiprocessing"""

	# Log into Twitter, get credentials.
	#try:
	if (check_twitter_auth() == False):
		sys.exit()
	logging.debug("Authorized")
	#except:
	#	logging.critical("FATAL: Authorization failed, exiting process.")
		# We need to figure out what to do to recover from this failure, if it happens.
	#	sys.exit()
	
if __name__ == '__main__':	
	logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
	logging.debug('Logging initialized')
	logging.debug("Running login module from the command line.")
	run()


