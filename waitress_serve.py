#!/usr/bin/env python3

from waitress import serve
from web_ui import server

serve(server, listen='*:8080')
