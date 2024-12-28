from watchdog.events import FileSystemEvent, FileSystemEventHandler
from multiprocessing import Process, Queue, Event
from watchdog.observers import Observer
from typing import List 
import time
import sys
import os


class MyEventHandler(FileSystemEventHandler):
    def __init__(self, event_queue:Queue):
        super().__init__()
        self.event_queue = event_queue


    def on_created(self, event:FileSystemEvent) -> None:
        if event.is_directory:
            self._add_event("created", event, is_file=False)
        else:
            self._add_event("created", event, is_file=True)


    def on_deleted(self, event:FileSystemEvent) -> None:
        if event.is_directory:
            self._add_event("deleted", event, is_file=False)
        else:
            self._add_event("deleted", event, is_file=True)


    def on_modified(self, event:FileSystemEvent) -> None:
        if not event.is_directory:
            self._add_event("modified", event, is_file=True)


    def on_moved(self, event: FileSystemEvent) -> None:
        src_parent:str|bytes = os.path.dirname(event.src_path)
        dest_parent:str|bytes = os.path.dirname(event.dest_path)

        # Rename #
        if src_parent == dest_parent:
            if event.is_directory:
                self._add_event("renamed", event, new_path=event.dest_path, is_file=False)

            else:
                self._add_event("renamed", event, new_path=event.dest_path,is_file=True)

        # Move #
        else:
            src_base:str|bytes = os.path.basename(src_parent)
            dest_base:str|bytes = os.path.basename(dest_parent)

            if src_base != dest_base:
                if event.is_directory:
                    self._add_event("moved", event, new_path=dest_parent,is_file=False)
                else:
                    self._add_event("moved", event, new_path=dest_parent,is_file=True)


    def _add_event(self, event_type: str, event: FileSystemEvent, new_path = None, is_file: bool = False) -> None:
        self.event_queue.put({
            "type": event_type,
            "path": os.path.normpath(event.src_path),
            "new_path": new_path,
            "is_file": is_file,
        })



def directory_monitoring(path:str, event_queue:Queue, stop_event) -> None:
    event_handler:MyEventHandler = MyEventHandler(event_queue) 

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        sys.exit(0)
            
    finally:
        observer.stop()
        observer.join()



class DirectoryMonitor:
    def __init__(self, path: str):
        self.path = path
        self.event_queue = Queue()
        self.stop_event = Event()
        self.process = None


    def start(self) -> None:
        if not self.process or not self.process.is_alive():
            self.process = Process(
                target=directory_monitoring,
                args=(self.path, self.event_queue, self.stop_event),
                daemon=True
            )
            self.process.start()


    def stop(self) -> None:
        if self.process and self.process.is_alive():
            self.stop_event.set()
            self.process.join()


    def get_changes(self) -> List[dict]:
        changes = []
        while not self.event_queue.empty():
            changes.append(self.event_queue.get())
        return changes

