import sys
import logging
import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

auto_exp_dir = os.path.abspath(os.path.join('..', '..', '..', '..', 'experiment_watcher'))

class WatersWatcher:
    watch_dir = os.path.join(auto_exp_dir, 'reports')
    print(watch_dir)

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = WatersHandler()
        self.observer.schedule(event_handler, self.watch_dir, recursive = True)

        self.observer.start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()


class WatersHandler(PatternMatchingEventHandler):
    patterns = ['*.txt']

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type == 'modified':
            return None
        elif event.event_type == 'created':
            subprocess.run(['python', 'assemble_traces.py', os.path.join(auto_exp_dir, 'traces'), '--quiet', '--no-db'])

if __name__ == '__main__':
    w = WatersWatcher()
    w.run()
