#!/usr/bin/env python3

from waitress import serve
from web import server
from time import sleep

while True:
    try:
        serve(server, listen='0.0.0.0:8080')
    except ConnectionRefusedError:
        sleep(5)
