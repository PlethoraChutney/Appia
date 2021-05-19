#!/usr/bin/env python3

from waitress import serve
from web import server

serve(server, listen='*:8080')
