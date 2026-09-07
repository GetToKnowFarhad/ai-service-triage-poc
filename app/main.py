from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import database

# Resolve paths relative to this file so templates and CSS are easy to find.
BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize_database()
    yield


app = FastAPI(lifespan=lifespan)

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

    ticket_id = database.create_ticket(title, description)

    return templates.TemplateResponse(
        request=request,
        name="confirmation.html",
        context={"ticket_id": ticket_id, "title": title, "description": description},
    )


@app.get("/tickets", response_class=HTMLResponse)
def tickets(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="tickets.html",
        context={"tickets": database.list_tickets()},
    )


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(request: Request, ticket_id: int):
    ticket = database.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return templates.TemplateResponse(
        request=request,
        name="ticket_detail.html",
        context={"ticket": ticket},
    )
