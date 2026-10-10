"""Small local JSON store, so importing is not repeated on every visit."""
import json
import os
from pathlib import Path
from uuid import UUID, uuid4


def storage_folder():
    # Persistent hosting needs this directory on a persistent disk.
    default = Path(__file__).parent / '.timetable-data'
    return Path(os.getenv('TIMETABLE_DATA_DIR', str(default)))


def file_for(identifier):
    # Validate the ID so a URL parameter cannot become an arbitrary file path.
    safe_id = str(UUID(identifier))
    return storage_folder() / (safe_id + '.json')


def save_timetable(timetable):
    identifier = str(uuid4())
    path = file_for(identifier)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(timetable)
    record['id'] = identifier
    path.write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


def load_timetable(identifier):
    path = file_for(identifier)
    return json.loads(path.read_text(encoding='utf-8'))


def delete_timetable(identifier):
    file_for(identifier).unlink(missing_ok=True)
