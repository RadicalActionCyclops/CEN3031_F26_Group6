# SwampSpace

SwampSpace is a networking platform for University of Florida students and
alumni. It brings profiles, professional connections, direct messaging,
community discussions, and job opportunities into one UF-focused space.

## Features

- UF account registration, login, and verification
- Student and alumni profiles
- Member search and networking
- Direct messages and conversations
- Community posts and discussions
- Job and internship opportunities

## Technology

- **Frontend:** React, JavaScript, and Vite
- **Backend:** Python, FastAPI, and Pydantic
- **Database:** SQLite and SQLAlchemy
- **Testing:** Pytest
- **Collaboration:** Git and GitHub

```text
SwampSpace/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── profiles/
│   │   │   ├── messages/
│   │   │   └── community/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── features/
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Team

- **Denny Kantarevic:** authentication, registration, database, and security
- **Ananya Balla:** profiles, member search, and networking
- **Sydney Dodson:** direct messaging, conversations, and inbox
- **Antonio Vega:** community posts, feed, and jobs board

## Run Locally

Start the backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

On Windows, activate with `.venv\Scripts\Activate.ps1`.

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Run project checks with `python -m pytest -v` from `backend` and
`npm run build` from `frontend`.

## Git Workflow

Create a feature branch, work mainly inside your assigned feature folder, run
the project checks, push the branch, and open a pull request to `main`. Never
commit `.env`, local databases, virtual environments, caches, or build output.
