#!/usr/bin/env python3

from waitress import serve
from app import server

serve(server, listen='*:8080')
