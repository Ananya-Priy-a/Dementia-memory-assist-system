import json
import os
from datetime import datetime
from typing import Dict, List


class MemoryStore:
    """
    Very small JSON-backed store for person memories.
    Optimized for demo reliability, not scale.
    """

    def __init__(self, path: str):
        self.path = path
        self._data: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        if not os.path.isfile(self.path):
            self._data = {}
            self._persist()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    def _persist(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def ensure_person(self, person_id: str, name: str, relationship: str):
        if person_id in self._data:
            # Fill in missing basics only
            entry = self._data[person_id]
            entry.setdefault("name", name)
            entry.setdefault("relationship", relationship)
            self._persist()
            return
        self._data[person_id] = {
            "name": name,
            "relationship": relationship,
            "visit_count": 0,
            "last_visit": None,
            "last_summary": "",
        }
        self._persist()

    def get_person(self, person_id: str) -> Dict:
        return self._data.get(person_id, {})

    def update_after_visit(self, person_id: str, new_summary: str) -> Dict:
        today = datetime.utcnow().date().isoformat()
        entry = self._data.setdefault(
            person_id,
            {
                "name": person_id,
                "relationship": "",
                "visit_count": 0,
                "last_visit": None,
                "last_summary": "",
            },
        )
        entry["visit_count"] = int(entry.get("visit_count", 0)) + 1
        entry["last_visit"] = today
        if new_summary:
            entry["last_summary"] = new_summary

        self._persist()
        return entry

    def list_people(self) -> List[Dict]:
        return list(self._data.values())

