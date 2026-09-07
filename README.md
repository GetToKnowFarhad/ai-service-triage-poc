# AI Service Triage PoC

A minimal, server-rendered FastAPI application. The homepage displays
"AI Service Triage PoC" and "System Status: Running." It also has a form for
submitting a ticket title and description.

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
        confirmation.html
    static/
        style.css
requirements.txt
.gitignore
README.md
```

- `app/__init__.py`: Marks `app` as a Python package. It is intentionally empty.
- `app/main.py`: Creates the FastAPI application, serves static files, renders the homepage at `/`, and handles form submissions at `POST /submit`. It rejects missing, empty, or whitespace-only fields and renders a confirmation for valid input.
- `app/templates/index.html`: The homepage and ticket form. Both fields are required. If server validation fails, it shows an error and keeps the entered values so the user can correct them.
- `app/templates/confirmation.html`: Displays the submitted title and description. Jinja2 escapes the values so user input appears as text.
- `app/static/style.css`: Basic styling for the pages, form controls, and validation message. Preserves line breaks in the submitted description.
- `requirements.txt`: Lists FastAPI for the application, Uvicorn to run the server, Jinja2 to render HTML templates, and `python-multipart`, which FastAPI requires to parse form data.
- `.gitignore`: Keeps the local virtual environment and Python cache files out of Git.
- `README.md`: Setup instructions and a guide to the files.

When you visit `/`, FastAPI renders the template into HTML. Your browser then
loads the CSS from `/static/style.css`. No JavaScript is needed.

Submitting the form sends the fields to `/submit`. FastAPI trims surrounding
whitespace and checks both fields. Invalid input returns the form with an error
(HTTP 400); valid input displays the confirmation page. Requests are only
displayed, not stored.

If you already have the virtual environment, install the updated dependencies
with `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` before
starting the server.

SQLite is planned for a later step; this version has no database, AI,
authentication, Docker, React, or external service integrations.
