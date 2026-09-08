from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import database
from app.ai_service import assess_ticket
from app.assessment_errors import AssessmentError
from app.assessment_schema import CATEGORIES, PRIORITIES

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
    return render_ticket_detail(request, ticket_id)


def render_ticket_detail(request: Request, ticket_id: int, error=None, form=None, status_code=200):
    # Reuse the detail page when a review needs correction.
    ticket = database.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    assessment = database.get_assessment(ticket_id)
    review = database.get_review(assessment["id"]) if assessment else None
    return templates.TemplateResponse(
        request=request,
        name="ticket_detail.html",
        context={
            "ticket": ticket,
            "assessment": assessment,
            "review": review,
            "categories": CATEGORIES,
            "priorities": PRIORITIES,
            "error": error,
            "form": form,
        },
        status_code=status_code,
    )


@app.post("/tickets/{ticket_id}/analyze")
def analyze_ticket(request: Request, ticket_id: int):
    ticket = database.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    detail_url = request.url_for("ticket_detail", ticket_id=ticket_id)
    if database.get_assessment(ticket_id) is not None:
        return RedirectResponse(detail_url, status_code=303)

    try:
        recommendation = assess_ticket(ticket["title"], ticket["description"])
    except AssessmentError as error:
        return render_ticket_detail(
            request, ticket_id, error=f"{error} No recommendation was saved.", status_code=error.status_code
        )
    database.save_assessment(ticket_id, recommendation)
    return RedirectResponse(detail_url, status_code=303)


@app.post("/tickets/{ticket_id}/review")
def review_ticket(
    request: Request,
    ticket_id: int,
    action: str = Form(default=""),
    category: str = Form(default=""),
    priority: str = Form(default=""),
    team: str = Form(default=""),
):
    if database.get_ticket(ticket_id) is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    assessment = database.get_assessment(ticket_id)
    if assessment is None:
        return render_ticket_detail(
            request, ticket_id, error="Analyze this ticket before reviewing it.", status_code=400
        )

    detail_url = request.url_for("ticket_detail", ticket_id=ticket_id)
    if database.get_review(assessment["id"]) is not None:
        return RedirectResponse(detail_url, status_code=303)

    if action == "approve":
        # Approval always copies the saved original, not values from the browser.
        category = assessment["category"]
        priority = assessment["priority"]
        team = assessment["recommended_team"]
    elif action == "modify":
        category, priority, team = category.strip(), priority.strip(), team.strip()
        if category not in CATEGORIES or priority not in PRIORITIES or not team:
            return render_ticket_detail(
                request,
                ticket_id,
                error="Choose a listed category and priority, and enter a team.",
                form={"category": category, "priority": priority, "team": team},
                status_code=400,
            )
    else:
        return render_ticket_detail(
            request, ticket_id, error="Choose approve or save a final decision.", status_code=400
        )

    unchanged = (
        category == assessment["category"]
        and priority == assessment["priority"]
        and team == assessment["recommended_team"]
    )
    database.save_review(
        assessment["id"], "approved" if unchanged else "modified", category, priority, team
    )
    return RedirectResponse(detail_url, status_code=303)
