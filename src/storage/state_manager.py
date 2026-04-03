import json
import os
import logging

logger = logging.getLogger(__name__)

# Paths relative to the project root
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
VISITED_PATH = os.path.join(DATA_DIR, "visited_urls.json")
EVENTS_PATH = os.path.join(DATA_DIR, "events.json")
ENTITY_PATH = os.path.join(DATA_DIR, "entity_index.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return default if default is not None else {}

def save_json(path, data):
    ensure_data_dir()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving {path}: {e}")

class StateManager:
    def __init__(self):
        ensure_data_dir()
        self.visited = load_json(VISITED_PATH, default={})
        self.events = load_json(EVENTS_PATH, default=[])
        self.entity_index = load_json(ENTITY_PATH, default={})

    def save_visited(self, visited):
        self.visited = visited
        save_json(VISITED_PATH, visited)

    def save_events(self, events):
        self.events = events
        save_json(EVENTS_PATH, events)

    def get_visited(self, source_name):
        return self.visited.get(source_name, [])

    def add_visited(self, source_name, url):
        if source_name not in self.visited:
            self.visited[source_name] = []
        if url not in self.visited[source_name]:
            self.visited[source_name].append(url)
            self.save_visited(self.visited)
