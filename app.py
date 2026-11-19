import os
import re
import random
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import jwt
from dotenv import load_dotenv
from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash

import ai
import db as store

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET") or "dev-only-secret-change-me"
if not os.getenv("JWT_SECRET"):
    print("WARNING: JWT_SECRET not set. Using an insecure dev secret.")

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=None)
origins = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]
CORS(app, resources={r"/api/*": {"origins": origins or "*"}})
limiter = Limiter(get_remote_address, app=app, default_limits=["120 per minute"], storage_uri="memory://")

GROUPS = list(ai.COMPAT)


def make_token(u):
    payload = {"id": u["id"], "name": u["name"], "role": u["role"],
               "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def auth_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        header = request.headers.get("Authorization", "")
        try:
            g.user = jwt.decode(header.replace("Bearer ", ""), JWT_SECRET, algorithms=["HS256"])
        except jwt.PyJWTError:
            return jsonify(error="Login required"), 401
        return fn(*a, **kw)
    return wrapper


def body():
    return request.get_json(silent=True) or {}


# ---------- Health ----------
@app.get("/api/health")
def health():
    return jsonify(ok=True, time=datetime.now(timezone.utc).isoformat())


# ---------- Auth ----------
@app.post("/api/auth/register")
@limiter.limit("20 per 15 minutes")
def register():
    d = body()
    name, email, pw, role = (d.get("name") or "").strip(), (d.get("email") or ""), (d.get("password") or ""), d.get("role", "Donor")
    if not name or not re.match(r"^\S+@\S+\.\S+$", email) or len(pw) < 6:
        return jsonify(error="Name, valid email and password of 6+ characters are required."), 400
    if role not in ("Donor", "Recipient", "Hospital"):
        return jsonify(error="Invalid role."), 400
    users = store.db["users"]
    if any(u["email"] == email.lower() for u in users):
        return jsonify(error="Email already registered."), 409
    user = {"id": store.next_id(users), "name": name[:60], "email": email.lower(), "role": role,
            "passwordHash": generate_password_hash(pw), "createdAt": datetime.now(timezone.utc).isoformat()}
    users.append(user)
    store.save()
    return jsonify(token=make_token(user), user={"id": user["id"], "name": user["name"], "role": user["role"]}), 201


@app.post("/api/auth/login")
@limiter.limit("20 per 15 minutes")
def login():
    d = body()
    email = (d.get("email") or "").lower()
    user = next((u for u in store.db["users"] if u["email"] == email), None)
    if not user or not check_password_hash(user["passwordHash"], d.get("password") or ""):
        return jsonify(error="Wrong email or password."), 401
    return jsonify(token=make_token(user), user={"id": user["id"], "name": user["name"], "role": user["role"]})


@app.get("/api/me")
@auth_required
def me():
    return jsonify(user=g.user)


# ---------- AI: triage + matching ----------
@app.post("/api/triage")
def triage():
    return jsonify(urgency=ai.triage(body().get("text")))


@app.post("/api/match")
def match():
    d = body()
    group = d.get("group")
    if group not in GROUPS:
        return jsonify(error="Invalid blood group."), 400
    urgency = (ai.triage(d["text"]) if d.get("text") else None) or d.get("urgency", "moderate")
    return jsonify(urgency=urgency, donors=ai.rank(group, urgency, store.db["donors"])[:4])


# ---------- Emergency requests ----------
@app.post("/api/requests")
def create_request():
    d = body()
    group, urgency = d.get("group"), d.get("urgency", "moderate")
    if group not in GROUPS:
        return jsonify(error="Invalid blood group."), 400
    top = ai.rank(group, urgency, store.db["donors"])[:3]
    row = {"id": store.next_id(store.db["requests"]), "group": group, "urgency": urgency,
           "text": str(d.get("text", ""))[:500], "alerted": [t["id"] for t in top],
           "status": "alerted" if top else "no_donor_found",
           "createdAt": datetime.now(timezone.utc).isoformat()}
    store.db["requests"].append(row)
    store.save()
    return jsonify(request=row, alerted=top), 201


@app.get("/api/requests")
@auth_required
def list_requests():
    if g.user["role"] != "Hospital":
        return jsonify(error="Hospitals only."), 403
    return jsonify(requests=list(reversed(store.db["requests"][-50:])))


# ---------- Donors ----------
@app.get("/api/donors")
@auth_required
def donors():
    return jsonify(donors=[{"id": d["id"], "name": d["name"], "group": d["group"]} for d in store.db["donors"]])


# ---------- Stock ----------
@app.get("/api/stock")
def stock():
    return jsonify(stock=store.db["stock"])


@app.post("/api/stock/simulate")
def simulate():
    s = store.db["stock"]
    for k in s:
        s[k] = max(0, s[k] - random.randint(0, 8) + random.randint(0, 4))
    store.save()
    return jsonify(stock=s)


# ---------- Forecast ----------
@app.get("/api/forecast")
def forecast():
    city = request.args.get("city")
    if city not in store.db["demand"]:
        return jsonify(error="Unknown city. Use Pune, Mumbai or Nagpur."), 400
    return jsonify(city=city, **ai.forecast(store.db["demand"][city], store.db["cityStock"][city]))


# ---------- Assistant ----------
@app.post("/api/assistant")
def assistant():
    return jsonify(answer=ai.assistant(body().get("question")))


@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api"):
        return jsonify(error="Not found"), 404
    return send_from_directory(FRONTEND, "index.html")


# ---------- Serve the frontend ----------
@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/<path:p>")
def static_files(p):
    return send_from_directory(FRONTEND, p)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    print(f"LifeLink running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
