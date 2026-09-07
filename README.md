# AI Service Triage PoC

A minimal, server-rendered FastAPI application. The homepage displays
"AI Service Triage PoC" and "System Status: Running." It also has a form for
submitting a ticket title and description. Valid submissions are saved in a
local SQLite database and can be viewed later. Each ticket can receive a mock
recommendation, followed by an analyst's approval or changes. The original
recommendation and final decision are stored separately.

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
    database.py
    assessment_schema.py
    ai_service.py
    mock_assessment.py
    templates/
        index.html
        confirmation.html
        tickets.html
        ticket_detail.html
    static/
        style.css
tests/
    test_assessment.py
    test_evaluation.py
    test_workflow.py
evaluation/
    __init__.py
    benchmark.py
    policy.txt
    tickets.json
requirements.txt
tickets.db                 # Created automatically on server startup
.gitignore
README.md
```

- `app/__init__.py`: Marks `app` as a Python package. It is intentionally empty.
- `app/main.py`: Initializes the database and handles page and form routes. Imports the assessment function from `ai_service` and review choices from `assessment_schema`; route behavior is unchanged.
- `app/database.py`: Keeps all SQLite logic separate from routes. Accepts an `AIAssessment` when saving a recommendation and reads its attributes into the existing parameterized insert. Table definitions and review storage are unchanged.
- `app/assessment_schema.py`: Defines the validated `AIAssessment` contract and the shared allowed category and priority choices.
- `app/ai_service.py`: Provides the application-facing `assess_ticket(title, description)` function. Calls the active mock provider and validates its result against the contract.
- `app/mock_assessment.py`: The deterministic provider, with the existing keyword rules, team mappings, and summary logic. Now returns an `AIAssessment` instead of a dictionary. It has no language model, network calls, or randomness.
- `app/templates/index.html`: The homepage and required ticket form, with a link to the saved tickets. Validation errors retain the entered values.
- `app/templates/confirmation.html`: Displays the generated ticket ID, title, and description after the ticket is saved, with links to the saved ticket and list.
- `app/templates/tickets.html`: Lists saved ticket IDs, linked titles, and UTC creation times, newest first. Shows a message when no tickets exist.
- `app/templates/ticket_detail.html`: Displays the ticket, Analyze ticket action, original mock recommendation, review forms, and saved final human decision. Jinja2 escapes submitted values on all pages so input appears as text.
- `app/static/style.css`: Styles pages and form controls, including review dropdowns and sections. Preserves line breaks in submitted text.
- `tests/test_assessment.py`: Tests strict field validation, allowed values, missing/extra fields, the mock provider's return type, and the service interface's validation of provider output.
- `tests/test_evaluation.py`: Tests scoring, latency calculations, request settings, dataset coverage, error handling, and a complete CSV export with mocked HTTP responses; Ollama is not needed.
- `tests/test_workflow.py`: Tests existing priority rules and the full workflow. Uses model attributes for mock results and checks their type; database rows still use column names. Uses an isolated test database and sends requests directly to the application without starting a server.
- `evaluation/__init__.py`: Marks the standalone evaluation directory as a Python package so the benchmark can run with `python -m`.
- `evaluation/benchmark.py`: Calls the local Ollama chat API, validates responses with the existing assessment contract, calculates results, prints summaries, and writes a CSV. It does not import routes, call the application service, or access SQLite.
- `evaluation/policy.txt`: Shared, reusable business-priority instructions for both evaluated models. The script adds the existing category guidance, team mapping, and JSON schema. It contains no ticket-specific examples or expected answers.
- `evaluation/tickets.json`: Ten hand-authored synthetic tickets with predefined category, priority, and team labels. The benchmark does not calculate these labels from model predictions or send them to the models.
- `requirements.txt`: Lists FastAPI, Uvicorn, Jinja2, `python-multipart`, and Pydantic 2. Pydantic is already installed through FastAPI; it is now declared directly because the application imports it for assessment validation.
- `tickets.db`: The local database, generated automatically; stores tickets, assessments, and reviews between server restarts.
- `.gitignore`: Keeps the virtual environment, Python caches, and local database files out of Git.
- `README.md`: Setup instructions, file explanations, database details, the assessment contract, workflow rules, routes, tests, and Dell benchmark instructions and measurement definitions.

When you visit `/`, FastAPI renders the template into HTML. Your browser then
loads the CSS from `/static/style.css`. No JavaScript is needed.

Submitting the form sends the fields to `/submit`. FastAPI trims surrounding
whitespace and checks both fields. Invalid input returns the form with an error
(HTTP 400) without saving a ticket. Valid input is saved before displaying the
confirmation page with its generated ticket ID.

If you already have the virtual environment, install the updated dependencies
with `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` before
starting the server.

## Database

SQLite is included with Python through the `sqlite3` standard-library module;
no new dependency or separate database server is needed.

On startup, the application creates `tickets.db` in the project folder and
creates any missing tables. Restarting an existing installation adds
`ai_assessments` and `human_reviews` without replacing the `tickets` table or
its data. The database path is based on `database.py`, not the terminal's
current directory.

The `tickets` table contains these fields:

| Column | SQLite type | Purpose |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | Unique integer generated by SQLite |
| `title` | TEXT NOT NULL | Ticket title |
| `description` | TEXT NOT NULL | Ticket description |
| `created_at` | TEXT NOT NULL | UTC timestamp generated by SQLite, in `YYYY-MM-DD HH:MM:SS` format |

The `ai_assessments` table stores `id`, `ticket_id`, `category`, `priority`,
`summary`, `recommended_team`, `requires_human_review` (0 or 1), and
`created_at`. Its unique `ticket_id` links to the ticket and allows one original
assessment per ticket.

The `human_reviews` table stores `id`, `assessment_id`, `decision` (`approved`
or `modified`), final `category`, final `priority`, final `team`, and
`created_at`. Its unique `assessment_id` links the final decision to the exact
original recommendation. A ticket is found through that assessment's
`ticket_id`; ticket text is not copied into the review.

Both new tables restrict categories and priorities to the allowed values with
SQLite `CHECK` constraints. Foreign keys prevent orphaned records. All three
tables use SQLite-generated UTC timestamps.

Assessment and review writes only insert records. A repeated analysis keeps
the original assessment, and a repeated review keeps the first final decision.
There is no replacement, edit-after-review, or re-analysis history in this stage.

Inserts and ID lookups use `?` placeholders with separate parameter values.
User input is never interpolated into SQL. Tickets are ordered by creation
time descending, then ID descending to put the newest ID first when timestamps
match within the same second.

## Assessment contract and service interface

`app/assessment_schema.py` defines a Pydantic model named `AIAssessment` with
exactly five required fields:

| Field | Accepted value |
| --- | --- |
| `category` | Network, Hardware, Software, Account Access, Security, or Other |
| `priority` | Low, Medium, High, or Critical |
| `summary` | A nonblank string |
| `recommended_team` | A nonblank string |
| `requires_human_review` | A boolean (`True` or `False`) |

Values are case-sensitive. Missing fields, unknown fields, invalid choices,
blank text, and wrong types raise Pydantic `ValidationError`. For example,
`"Urgent"` is not a priority, and `"true"` or `1` cannot replace a boolean.
The model is frozen, so its fields cannot be reassigned after validation.
Ticket IDs and timestamps belong to database records, not this contract.

Application code calls the service rather than importing a provider directly:

```python
from app.ai_service import assess_ticket

assessment = assess_ticket(
    "My laptop keeps losing Wi-Fi",
    "I have a client meeting in 20 minutes",
)
print(assessment.category)  # Network
print(assessment.priority)  # High
```

The interface is `assess_ticket(title: str, description: str) -> AIAssessment`.
The service currently calls `app/mock_assessment.py`. The mock builds the
validated model, and the service validates the provider result before returning
it. Invalid output is rejected before the route can save a recommendation.
The database function accepts the model and writes its attributes into the
existing columns. Saved records and templates continue to work as before.

To replace the mock in a future stage:

1. Implement a provider function with the same two inputs and `AIAssessment`
   return type. Validate any parsed provider output with
   `AIAssessment.model_validate(parsed_output)` before returning it.
2. Change the provider import and call in `app/ai_service.py`. Routes keep
   calling the same service function.
3. Run the contract and workflow tests for that provider. Keep the mock for
   deterministic tests; add provider-specific error handling when integrating
   the real provider.

The FastAPI application has no provider selection UI, real model connection,
or external API integration. The standalone benchmark below calls local Ollama
only when you run it explicitly. It does not replace the active mock provider
or change the application's requirement for human review.

## Mock assessment and human review

1. Submit a ticket and open its detail page.
2. Select **Analyze ticket**. The service applies keyword rules to the title
   and description and stores the original result in `ai_assessments`.
3. Read the category, priority, summary, recommended team, and human-review flag.
4. Select **Approve unchanged**, or change category, priority, and/or team and
   select **Save final decision**. The edit form starts with the recommendation.
5. The page displays both the original recommendation and final human decision.

Every mock recommendation has `requires_human_review = True`. This original
flag stays unchanged after review; the final decision section shows that review
is complete. No recommendation is automatically accepted.

Approval copies the stored original values on the server. Edited reviews must
use one of the listed categories and priorities and a nonblank team. Invalid
reviews show an error and retain entered values without saving. Saving the edit
form without changes counts as approval. A final decision cannot be saved
before analysis.

The same input always produces the same result. Matching is case-insensitive
and uses simple substring checks. The first matching category below wins:

| Category (match order) | Keywords | Recommended team |
| --- | --- | --- |
| Security | phishing, malware, ransomware, breach, suspicious | IT Security |
| Account Access | password, login, log in, account, locked out, mfa | Identity and Access |
| Network | network, wifi, wi-fi, internet, vpn, connection | Network Support |
| Hardware | laptop, printer, monitor, keyboard, mouse, hardware | Hardware Support |
| Software | software, application, app, install, crash, license | Software Support |
| Other | No category keyword matched | Service Desk |

Priority rules run in this order:

- **Critical:** Broad impact (such as all users, multiple services, widespread,
  or business-wide) together with an interruption or severe incident (such as
  outage, unavailable, cannot connect, ransomware, or breach). Neither "outage"
  nor "all users" alone makes a ticket Critical.
- **High:** Security category, explicitly blocked work (such as "cannot work"
  or "cannot complete"), or a business context (client, customer, meeting,
  deadline, presentation, payroll, or production) with urgency. Urgency includes
  "in N minutes/hours", "urgent" (except "not urgent"), "asap", "due today",
  "deadline today", "meeting today", or "time-sensitive".
- **Low:** Minimal-impact wording (cosmetic, how to, minor), or a planned/requested
  installation, upgrade, or license with deferral (for later, next week/month,
  when convenient, no rush, not urgent, no urgency). This applies only without
  disruption or urgency, and never overrides Critical or High.
- **Medium:** Default for an ordinary single-user issue without a matching
  major impact or time-sensitive interruption. "Broken", "cannot", and
  "locked out" alone do not establish High priority.

For example, "My laptop keeps losing Wi-Fi and I have a client meeting in
20 minutes" produces **Network / High**. A planned software request for later
produces **Software / Low**. A VPN outage affecting all users is **Network /
Critical**. A ransomware report on one isolated laptop is **Security / High**;
an incident affecting multiple services is **Security / Critical**.

The summary is the title and description combined, whitespace normalized, and
shortened to at most 240 characters. These rules do not understand context or
negation; they are for exercising the workflow. The detail page labels the
recommendation as mock.

## Routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/` | Display the submission form |
| POST | `/submit` | Validate and save a ticket, then display confirmation |
| GET | `/tickets` | List saved tickets, newest first |
| GET | `/tickets/{ticket_id}` | Display one saved ticket; return HTTP 404 if it does not exist |
| POST | `/tickets/{ticket_id}/analyze` | Save the mock assessment once and redirect to ticket details |
| POST | `/tickets/{ticket_id}/review` | Validate and save the final human decision once and redirect to ticket details |

For example, `/tickets/1` displays ticket 1 if it exists.

The new POST routes receive HTML forms; no JSON API was added. They also return
HTTP 404 for unknown tickets. Successful actions redirect with HTTP 303 so
refreshing the detail page does not resubmit the action.

## Local Ollama benchmark on the Dell

Run the benchmark on the Dell itself: `localhost` means the computer running
the script. FastAPI does not need to be running. The benchmark only reads its
synthetic dataset; it never reads or writes `tickets.db`.

### Prepare the Dell

Copy this project to the Dell and set up the Python virtual environment using
the instructions above. No new Python package is required for evaluation:
HTTP calls use Python's standard library, and validation uses existing Pydantic.

Install Ollama on the Dell if needed using its
[official setup instructions](https://docs.ollama.com/quickstart). Start the
Ollama application/service. If it is not already running, run `ollama serve`
in a separate terminal. Download the two models before benchmarking:

```text
ollama pull qwen3:1.7b
ollama pull gemma3:1b
ollama --version
ollama list
```

The model downloads require internet access during setup. Evaluation inference
uses only `http://localhost:11434/api/chat`; it does not use cloud inference or
an external API. The script does not install Ollama, download models, or start
the service automatically.

### Run the comparison

From the project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m evaluation.benchmark
```

If the Dell runs Linux, create/use its own virtual environment rather than
copying the Windows `.venv`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m evaluation.benchmark
```

The default run makes 20 sequential requests: 10 tickets for `qwen3:1.7b`,
then the same 10 for `gemma3:1b`. It prints progress and one console summary per
model, then saves `evaluation/results/ollama_<UTC timestamp>.csv`.

Optional arguments let you select either model, reverse their order, specify
an output filename, use another synthetic dataset in the same format, or allow
more time per HTTP request. For example:

```powershell
.\.venv\Scripts\python.exe -m evaluation.benchmark --models gemma3:1b qwen3:1.7b --timeout 180 --output evaluation/results/dell_comparison.csv
```

Use `--dataset path/to/synthetic_tickets.json` to supply additional labeled
synthetic cases. Keep the dataset and policy identical across compared models.
The default HTTP timeout is 120 seconds. An existing output file is never
overwritten; select a new filename or use the timestamped default.

### Shared settings and dataset

Both models receive the same system policy and a fresh title/description pair
for each request, with no conversation history or expected labels. The JSON
schema is generated directly from `AIAssessment.model_json_schema()` and sent
as Ollama's `format`. Responses must pass the existing strict Pydantic model;
the script does not repair JSON, strip Markdown fences, or retry invalid answers.
This follows Ollama's [structured-output API](https://docs.ollama.com/capabilities/structured-outputs).

Both requests set `stream: false`, `temperature: 0`, `seed: 0`, `num_ctx: 4096`,
and `num_predict: 512`. The same context and output limits apply to both models.
Qwen3 requests set `think: false`; Gemma3 has no thinking mode, so that field is
omitted. See Ollama's [thinking controls](https://docs.ollama.com/capabilities/thinking)
and the [Gemma3 model page](https://ollama.com/library/gemma3:1b).

`evaluation/policy.txt` expresses the project's business impact definitions,
including the distinction between a single-user disruption and widespread
interruption. It contains no Wi-Fi/client-meeting example. The existing
category precedence and team names are imported from the mock module; expected
answers stay in the dataset and are used only for scoring.

All tickets are invented and contain no real organizational/customer data:

| ID | Synthetic scenario | Expected category | Expected priority | Expected team |
| --- | --- | --- | --- | --- |
| T01 | Software installation for next month | Software | Low | Software Support |
| T02 | General service-desk information | Other | Low | Service Desk |
| T03 | Broken printer with a usable spare | Hardware | Medium | Hardware Support |
| T04 | Optional learning account locked out | Account Access | Medium | Identity and Access |
| T05 | Intermittent Wi-Fi with a working wired alternative | Network | Medium | Network Support |
| T06 | Wi-Fi drops before an imminent client meeting | Network | High | Network Support |
| T07 | Software crash blocking a report due today | Software | High | Software Support |
| T08 | Suspicious phishing email to one user | Security | High | IT Security |
| T09 | Company-wide network outage | Network | Critical | Network Support |
| T10 | Ransomware affecting multiple services | Security | Critical | IT Security |

### Reading the results

The console reports category accuracy, priority accuracy, routing accuracy,
valid structured-output rate, and average/median response latency for each model.

- Accuracy is exact, case-sensitive matching: correct predictions divided by
  **all attempted tickets** for that model. Routing accuracy means an exact
  match of the recommended team to the predefined expected team.
- Invalid output and failed requests receive no category, priority, or routing
  credit, even if a partial response contains a correct label. The validation
  rate also uses all attempts as its denominator.
- Each CSV row records model and ticket ID, expected/predicted category,
  priority, and team, validation and correctness flags, and elapsed seconds.
  It also includes request status, whether a completed HTTP response arrived,
  the predicted human-review flag when readable, error details, and the raw
  Ollama response for diagnosis. Summary wording and the human-review flag are
  available for inspection; their semantic correctness is not part of the
  three label-accuracy scores. The schema permits either boolean, while the
  business policy asks for `requires_human_review: true`.
- Latency uses the client's monotonic clock from sending the request through
  reading its full response, before local scoring. The CSV records elapsed time
  for failures too. The console average/median includes completed HTTP responses,
  including invalid model output, and excludes connection failures and timeouts.
  When none completes, latency is shown as **N/A**, not zero.
- A first response may include loading the model. No warmup, unload, automatic
  retry, or model switching in the application is performed. The raw response
  retains Ollama timing fields such as `load_duration` when supplied.
- Connection errors, timeouts, missing models, and malformed responses are
  recorded, and evaluation continues to the next ticket/model. Completed rows
  are flushed to CSV immediately, including before a later interruption.
  A completed run exits with code 0 even if individual attempts failed; inspect
  the rates and `status`/`error` columns. Setup/output errors exit with code 1.

For a fair Dell comparison, use the same dataset/settings and similar server
load. Record its CPU, RAM, GPU (if any), Ollama version, model IDs from
`ollama list`, and whether models were already loaded alongside the CSV. Repeat
with reversed model order to check loading/resource effects. Temperature zero
reduces sampling variation but is not a guarantee of identical results across
hardware or software versions. This 10-ticket set is an initial check, not a
statistical ranking; expand the synthetic cases before choosing a provider.

## Tests

From the project folder, run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Workflow tests create and remove their own database files beside `tickets.db`;
they do not change your saved tickets. Evaluation tests mock HTTP and clean up
their temporary CSV files. No Ollama instance, model download, or additional
test dependency is required.

This stage uses Pydantic 2, already supplied by FastAPI, and declares it as a
direct dependency. It otherwise uses the existing FastAPI, Jinja2, HTML/CSS,
SQLite, Uvicorn, and form-parsing dependencies. Evaluation uses only the Python
standard library and existing packages. The application still uses the mock;
there is no authentication, Docker, PostgreSQL, or cloud-service integration.
