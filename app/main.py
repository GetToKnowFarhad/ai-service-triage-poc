from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Resolve paths relative to this file so templates and CSS are easy to find.
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/submit", response_class=HTMLResponse)
def submit_ticket(
    request: Request,
    title: str = Form(default=""),
    description: str = Form(default=""),
):
    # Check on the server too: spaces alone do not count as a value.
    title = title.strip()
    description = description.strip()

    if not title or not description:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": "Please enter both a ticket title and a ticket description.",
                "title": title,
                "description": description,
            },
            status_code=400,
        )

    return templates.TemplateResponse(
        request=request,
        name="confirmation.html",
        context={"title": title, "description": description},
    )
