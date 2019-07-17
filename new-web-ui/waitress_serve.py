from waitress import serve
from app import server

serve(server, listen='*:8080')
