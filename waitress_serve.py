#!/usr/bin/env python3
import socket
import os
import logging
from time import sleep

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    result = sock.connect_ex((os.environ['COUCHDB_HOST'], 5984))
except socket.error:
    logging.debug('Server refused connection')
    result = 1

while result != 0:
    logging.debug('CouchDB port not open')
    sleep(5)
    try:
        result = sock.connect_ex((os.environ['COUCHDB_HOST'], 5984))
    except socket.error:
        logging.debug('Server refused connection')
        result = 1

logging.info('Port is open')


from waitress import serve
from web import server
import logging

serve(server, listen='0.0.0.0:8080', ipv6 = False)
