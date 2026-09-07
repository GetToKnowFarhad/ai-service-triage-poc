# AI Service Triage PoC

A minimal, server-rendered FastAPI application. The homepage displays
"AI Service Triage PoC" and "System Status: Running."

## Run locally

You need Python 3.10 or newer. Open PowerShell in the project folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser. Stop the server with `Ctrl+C`.
The commands use the virtual environment's Python directly, so activating it
is not required. The `--reload` option restarts the server when you edit Python
files during development.

## Project files

```text
app/
    __init__.py
    main.py
    templates/
        index.html
    static/
        style.css
requirements.txt
.gitignore
README.md
```

- `app/__init__.py`: Marks `app` as a Python package. It is intentionally empty.
- `app/main.py`: Creates the FastAPI application, serves static files, and renders the homepage at `/`.
- `app/templates/index.html`: The Jinja2 HTML template for the homepage.
- `app/static/style.css`: Basic styling for the page.
- `requirements.txt`: Lists the three direct dependencies: FastAPI for the application, Uvicorn to run the server, and Jinja2 to render HTML templates.
- `.gitignore`: Keeps the local virtual environment and Python cache files out of Git.
- `README.md`: Setup instructions and a guide to the files.

When you visit `/`, FastAPI renders the template into HTML. Your browser then
loads the CSS from `/static/style.css`. No JavaScript is needed.

SQLite is planned for a later step; this version has no database, AI,
authentication, Docker, React, or external service integrations.
