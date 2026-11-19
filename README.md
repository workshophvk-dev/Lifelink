# LifeLink: AI-Driven Blood and Body Donation (Python / Flask backend)

```
lifelink-py/
├── frontend/index.html      # Single-page UI (HTML, CSS, JS)
├── backend/
│   ├── app.py               # Flask API + serves the frontend
│   ├── ai.py                # Triage, ranking, forecast, FAQ assistant
│   ├── db.py                # JSON-file database (swap for PostgreSQL later)
│   ├── requirements.txt
│   └── .env.example
└── .gitignore
```

## Run locally

Requires Python 3.9 or newer.

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit JWT_SECRET (Windows: copy)
python app.py
```

Open http://localhost:3000. The backend serves the frontend, so nothing else is needed.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/auth/register` | `{name,email,password,role}` returns a JWT |
| POST | `/api/auth/login` | `{email,password}` returns a JWT |
| GET | `/api/me` | Current user (needs token) |
| POST | `/api/triage` | `{text}` returns urgency |
| POST | `/api/match` | `{group,urgency}` returns ranked donors |
| POST | `/api/requests` | Create an emergency request, alerts the top 3 donors |
| GET | `/api/requests` | List requests (Hospital role only) |
| GET | `/api/stock`, POST `/api/stock/simulate` | Blood stock |
| GET | `/api/forecast?city=Pune` | 3-month demand forecast |
| POST | `/api/assistant` | `{question}` returns an answer |

## Connect to GitHub

### 1. One-time setup
1. Create a free account at https://github.com.
2. Install Git: https://git-scm.com/downloads.
3. Tell Git who you are:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```

### 2. Create the repository on GitHub
1. On GitHub, click **+ → New repository**.
2. Name it `lifelink`. Leave **Add a README**, **.gitignore** and **license** unchecked (this project already has them).
3. Click **Create repository** and copy the URL, e.g. `https://github.com/YOUR-USERNAME/lifelink.git`.

### 3. Push your project
Run these from the `lifelink` folder:

```bash
git init
git add .
git commit -m "Initial commit: LifeLink frontend and backend"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/lifelink.git
git push -u origin main
```

GitHub does not accept your account password for pushes. When asked for a password, paste a **Personal Access Token**:
GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → generate one with **Contents: Read and write** for this repo.
(Or use SSH: https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

### 4. Daily workflow
```bash
git pull                      # get teammates' changes
git add .
git commit -m "Describe what you changed"
git push
```

### 5. Team work
- Add teammates: repo → **Settings → Collaborators**.
- Each person works on a branch: `git checkout -b feature/my-feature`, push it, then open a **Pull Request**.

### 6. Never commit secrets
`.env` and `backend/data.json` are already in `.gitignore`. If you ever commit a secret by mistake, change it immediately.

## Deploy (optional)

**Render / Railway** (backend + frontend together, free tier):
1. New Web Service → connect your GitHub repo.
2. Root directory: `backend`. Build command: `pip install -r requirements.txt`. Start command: `gunicorn app:app`.
3. Add environment variable `JWT_SECRET` (a long random string).
4. Note: free hosts reset local files, so move `db.js` to PostgreSQL before real use.

**GitHub Pages** can host only the `frontend/` folder (static). Then set `API` in `index.html` to your deployed backend URL and add that site to `CORS_ORIGINS`.

## Notes
- All donor, stock and demand data is synthetic. This is a demo, not medical advice.
- AI ranks and suggests; a doctor confirms every match.
- Before real use: replace the JSON store with an encrypted PostgreSQL database, add email/phone verification, and train models on real hospital data.
