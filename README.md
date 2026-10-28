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

## Sprint 1 Profiles and Member Search

Verified members can create a profile, update their basic information, view
other members at `/profiles/<user-id>`, and discover members at `/members`.
Profiles require a full name, Student/Alumni status, and graduation year
(1900 through the current year plus 10). Major/degree is optional. Names and
status use the existing account fields, keeping authentication and profiles
consistent. Selecting a status does not grant verified UF affiliation.

Search matches keywords against names and majors, with case-insensitive exact
major and graduation-year filters. Results are alphabetical, paginated in
groups of 20, and exclude accounts without completed profiles or verified,
active membership. Member responses do not expose emails or account secrets.

### Local demo accounts

Email verification alone does not verify UF affiliation. The existing
membership access check remains in place. To demonstrate profiles locally,
run this command from `backend` using its virtual environment:

```bash
python -m app.features.profiles.demo
```

This development-only command creates three synthetic accounts in local
SQLite and prints a randomly generated shared password. It refuses production
mode, non-SQLite databases, or any existing demo account; it never resets an
existing password or upgrades a real account.

- `profiles.student.demo@ufl.edu`: Alex Demo, initially without a profile.
- `profiles.alumni.demo@ufl.edu`: Jordan Demo, Computer Science, class of 2022.
- `profiles.finance.demo@ufl.edu`: Taylor Demo, Finance, class of 2027.

Demo steps:

1. Sign in as Alex and select **Create profile**.
2. Demonstrate the required-field feedback, then save a graduation year and major.
3. Refresh to show that the profile and session persist.
4. Edit the profile and save a correction.
5. Open **Find Members**, search by name or major, and combine filters.
6. Open Jordan's profile from a result card, then refresh its direct URL.
7. Search for a nonexistent name to demonstrate the empty state.
8. Sign out and sign in as Jordan to view Alex's saved profile.

The automated profile tests cover validation, persistence, identity consistency,
owner-only updates, CSRF, membership restrictions, search, pagination, and hidden
accounts. Bio, experience, skills, photo uploads, job titles, advanced filters,
relevance ranking, and messaging integration remain later work. The test-case
workbook's full TC-UP and TC-NW scenarios include some of those later features;
do not mark an entire scenario passed based only on this Sprint 1 subset.

The profile implementation does not implement live UF identity verification.
Synthetic demo membership is for local demonstrations only.

### Profile API

All routes require verified, active membership. POST and PATCH also require
the session's CSRF token. Writes always target the signed-in member.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/profiles/me` | Own profile, or 404 before setup |
| POST | `/api/profiles/me` | Create once, or 409 if already present |
| PATCH | `/api/profiles/me` | Update supplied basic profile fields |
| GET | `/api/profiles/<user-id>` | Available member profile |
| GET | `/api/profiles` | Search using `q`, `major`, `graduation_year`, `limit`, `offset` |

## Git Workflow

Create a feature branch, work mainly inside your assigned feature folder, run
the project checks, push the branch, and open a pull request to `main`. Never
commit `.env`, local databases, virtual environments, caches, or build output.
