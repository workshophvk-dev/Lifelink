"""Tiny JSON-file database so the project runs with zero setup.
Swap this module for PostgreSQL (psycopg / SQLAlchemy) for production."""
import copy
import json
import threading
from pathlib import Path

FILE = Path(__file__).parent / "data.json"
_lock = threading.Lock()

SEED = {
    "users": [],
    "requests": [],
    "donors": [
        {"id": 1, "name": "Aarav S.", "group": "O+", "x": 20, "y": 30, "lastDonationDays": 140},
        {"id": 2, "name": "Meera K.", "group": "B+", "x": 70, "y": 40, "lastDonationDays": 95},
        {"id": 3, "name": "Rohan P.", "group": "B-", "x": 35, "y": 80, "lastDonationDays": 200},
        {"id": 4, "name": "Sana M.", "group": "O-", "x": 90, "y": 90, "lastDonationDays": 130},
        {"id": 5, "name": "Vikram D.", "group": "B+", "x": 55, "y": 55, "lastDonationDays": 30},
        {"id": 6, "name": "Isha R.", "group": "A+", "x": 15, "y": 60, "lastDonationDays": 250},
        {"id": 7, "name": "Kabir T.", "group": "B+", "x": 85, "y": 20, "lastDonationDays": 180},
        {"id": 8, "name": "Neha J.", "group": "O+", "x": 45, "y": 20, "lastDonationDays": 100},
        {"id": 9, "name": "Arjun L.", "group": "AB+", "x": 60, "y": 75, "lastDonationDays": 160},
        {"id": 10, "name": "Pooja V.", "group": "B-", "x": 25, "y": 45, "lastDonationDays": 110},
    ],
    "stock": {"O-": 8, "O+": 42, "A-": 24, "A+": 38, "B-": 12, "B+": 30, "AB-": 6, "AB+": 22},
    "demand": {
        "Pune": [310, 300, 320, 340, 360, 350, 330, 345, 370, 390, 400, 410],
        "Mumbai": [620, 610, 640, 660, 700, 690, 680, 720, 750, 770, 790, 820],
        "Nagpur": [150, 160, 155, 170, 165, 175, 170, 180, 175, 185, 190, 195],
    },
    "cityStock": {"Pune": 420, "Mumbai": 780, "Nagpur": 210},
}


def _load():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = copy.deepcopy(SEED)
        FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data


db = _load()


def save():
    with _lock:
        FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")


def next_id(items):
    return max((i["id"] for i in items), default=0) + 1
