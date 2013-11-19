#!/usr/bin/python
#
"""
Tree of Light class implementation for the Tree-of-Light API for Holiday by Moorescloud

Homepage and documentation: http://dev.moorescloud.com/

Copyright (c) 2013, Mark Pesce.
License: MIT (see LICENSE for details)
"""

__author__ = 'Mark Pesce'
__version__ = '1.0a1'
__license__ = 'MIT'

import sys, array, socket, logging

class tolHoliday:

	NUM_HOLIDAYS = 27			# 9 shapes by 3 strings
	NUM_GLOBES = 50				# Number of globes on each string
	GENUINE_MOORESCLOUD = True	# False if cheap as Chinese crapware strings

	def __init__(self):
		print "Instancing tolHoliday..."
		self.holidays = []
		for i in range(self.NUM_HOLIDAYS):
			da_globes = []
			for j in range(self.NUM_GLOBES):
				da_globes.append([0x00, 0x00, 0x00])		# Create and zero the globes for each holiday instance
			self.holidays.append(da_globes)
		#printme(self.holidays)
		return

	def setglobe(self, stringnum, globenum, r, g, b):
		"""Set a globe on a holiday"""
		return

	def fill(self, stringnum, r, g, b):
		"""Sets the whole string to a particular colour"""
		hol = self.holidays[stringnum]
		for i in range(self.NUM_GLOBES):
			if self.GENUINE_MOORESCLOUD == False:
				hol[i][0] = g
				hol[i][1] = r
			else:
				hol[i][0] = r
				hol[i][1] = g
			hol[i][2] = b

	def getglobe(self, stringnum, globenum):
		"""Return a tuple representing a globe's RGB color value"""
		return

	def render(self):
		"""The render routine sends out a UDP packet using the tolAPI"""
		# Create the 160-byte array of data
		pkt = array.array('B')
		for ahol in self.holidays:
			for j in range(10):
				pkt.append(0)  		# initialize basic packet, ignore first 10 bytes
			for glbs in ahol:
				pkt.append(glbs[0])
				pkt.append(glbs[1])
				pkt.append(glbs[2])

		# Send the packet to the caller
		return pkt

def printme(str):
	"""A print function that can switch quickly to logging"""
	#print(str)
	logging.debug(str)

# Just some basic testerating from the command linery
#
if __name__ == '__main__':
	logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	printme('Logging initialized')
	printme("Running tolholiday module from the command line.")
	hol = tolHoliday()
	p = hol.render()
	printme("pkt size in bytes: %d" % len(p))