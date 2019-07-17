from waitress import serve
from app import server
import watcher

serve(server, listen='*:8080')
watcher.watch()
