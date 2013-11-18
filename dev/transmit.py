#!/usr/bin/python
#
import socket, sys, time
import tolapi

MCAST_GRP = '224.0.0.249'
MCAST_PORT = 9393

tol = tolapi.tolAPI()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

# Here's where we would want things to happen somewhat regularly
while True:
	#now = '%12f' % time.time()
    sock.sendto(tol.render(), (MCAST_GRP, MCAST_PORT))
    time.sleep(.5)
    print("TX")
