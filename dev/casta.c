#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
 
#define DATALEN 150
#define HEADERLEN 10
#define MSGLEN (DATALEN+HEADERLEN)
#define CORRECT_LENGTH 4320

#ifdef TARGET
#include "spi.h"
#endif 
 
struct sockaddr_in    localSock;
struct ip_mreq        group;
int                   sd;
int                   datalen, actual_len;
char                  databuf[10240];
int                   the_index = -1;
int                   start_offset = 0;

void render(char* buf) {
int j, k;
char* obf;

    obf = &buf[HEADERLEN+start_offset];   // The the correct start position

#ifdef TARGET
    // And send it on its merry way
    spi_send(obf, DATALEN); 
#endif
#ifdef DEBUG
    // This is where we get dirty with spi.h
    // For the moment, just show the values in the buffer.
    for (j=0, k=0; j < DATALEN; j++) {
        printf("%02x ", (uint8_t) obf[j]);
        if ((++k % 3) == 0) {
            printf("  ");
        }
        if ((k % 15) == 0) {
            printf("\n");
        }
    }
    printf("\n");
#endif
    return;
}

 
int main (int argc, char *argv[])
{
 
  /* ------------------------------------------------------------*/
  /*                                                             */
  /* Receive Multicast Datagram code example.                    */
  /*                                                             */
  /* ------------------------------------------------------------*/
 
  // We should have an index on the command line, so read it in.
  if (argc < 2) {
    printf("Usage: casta <index>\n");
    exit(1);
  } else {
    the_index = atoi(argv[1]);
    printf("Launching with an index of %d\n", the_index);
    start_offset = the_index * MSGLEN;  // Establish the starting offset for reads
  }

  /*
   * Create a datagram socket on which to receive.
   */
  sd = socket(AF_INET, SOCK_DGRAM, 0);
  if (sd < 0) {
    perror("opening datagram socket");
    exit(1);
  }
 
  /*
   * Enable SO_REUSEADDR to allow multiple instances of this
   * application to receive copies of the multicast datagrams.
   */
  {
    int reuse=1;
 
    if (setsockopt(sd, SOL_SOCKET, SO_REUSEADDR,
                   (char *)&reuse, sizeof(reuse)) < 0) {
      perror("setting SO_REUSEADDR");
      close(sd);
      exit(2);
    }
  }
 
  /*
   * Bind to the proper port number with the IP address
   * specified as INADDR_ANY.
   */
  memset((char *) &localSock, 0, sizeof(localSock));
  localSock.sin_family = AF_INET;
  localSock.sin_port = htons(9393);;
  localSock.sin_addr.s_addr  = INADDR_ANY;
 
  if (bind(sd, (struct sockaddr*)&localSock, sizeof(localSock))) {
    perror("binding datagram socket");
    close(sd);
    exit(3);
  }
 
 
  /*
   * Join the multicast group 225.1.1.1 on the local 9.5.1.1
   * interface.  Note that this IP_ADD_MEMBERSHIP option must be
   * called for each local interface over which the multicast
   * datagrams are to be received.
   */
  group.imr_multiaddr.s_addr = inet_addr("224.0.0.249");
  group.imr_interface.s_addr = inet_addr("192.168.0.177");
  if (setsockopt(sd, IPPROTO_IP, IP_ADD_MEMBERSHIP,
                 (char *)&group, sizeof(group)) < 0) {
    perror("adding multicast group");
    close(sd);
    exit(4);
  }
 
#ifdef TARGET
    spi_open();
#endif

while (1) {
    /*
     * Read from the socket.
     */
    datalen = sizeof(databuf);
    actual_len = read(sd, databuf, datalen);
    if ( actual_len < 0) {
      perror("reading datagram message");
      close(sd);
      exit(5);
    } else {
  	 printf("We got some datas of length %d.\n", actual_len);
      if (actual_len == CORRECT_LENGTH) {
        render(databuf);
      } else {
        printf("Datagram too short, rejecting.\n");
      }
    }
}

#ifdef TARGET
    spi_close();
#endif
 
}
