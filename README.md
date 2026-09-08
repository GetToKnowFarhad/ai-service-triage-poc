# AI Service Triage PoC

A minimal, server-rendered FastAPI application. The homepage displays
"AI Service Triage PoC" and "System Status: Running." It also has a form for
submitting a ticket title and description. Valid submissions are saved in a
local SQLite database and can be viewed later. Each ticket can receive a
recommendation from the deterministic mock or a local Ollama model, followed
by an analyst's approval or changes. The original recommendation and final
decision are stored separately. The mock remains the default, so local
development and tests do not need Ollama.

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

## Run the application with Ollama on the Dell

Run FastAPI and Ollama on the Dell itself: `localhost` refers to the computer
running FastAPI. The application sends inference requests only to
`http://localhost:11434/api/chat`. Qwen3 1.7B is the default model, provisionally
selected from the Dell benchmark.

Install Ollama if needed using its
[official setup instructions](https://docs.ollama.com/quickstart). Start the
Ollama application/service; if it is not already running, use `ollama serve`
in a separate terminal. Prepare the model before starting the app:

```text
ollama pull qwen3:1.7b
ollama list
```

Downloading the model requires internet access during setup. Inference runs
locally. The application does not install Ollama, download models, or start
the Ollama service automatically. Application requests bypass HTTP proxies
and reject redirects, keeping ticket text at the configured fixed local endpoint.

Configuration uses environment variables in the terminal that starts FastAPI:

| Variable | Default | Purpose |
| --- | --- | --- |
| `AI_PROVIDER` | `mock` | Select `mock` or `ollama` |
| `OLLAMA_MODEL` | `qwen3:1.7b` | Name of the locally installed Ollama model |
| `OLLAMA_TIMEOUT` | `120` | HTTP timeout in seconds; must be a positive, finite number |

For PowerShell, after setting up the virtual environment above:

```powershell
$env:AI_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "qwen3:1.7b"
$env:OLLAMA_TIMEOUT = "120"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

For a Linux Dell, create its own virtual environment instead of copying a
Windows `.venv`. From the project folder:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export AI_PROVIDER=ollama
export OLLAMA_MODEL=qwen3:1.7b
export OLLAMA_TIMEOUT=120
.venv/bin/python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 on the Dell, submit a ticket, open its detail page,
and select **Analyze ticket**. Review the result and approve or edit it as
before. To return to offline development, stop FastAPI, set
`$env:AI_PROVIDER = "mock"` in PowerShell or `export AI_PROVIDER=mock` on
Linux, and restart the server. Restart after changing any environment setting.
Omitting `AI_PROVIDER` also selects the mock.

An unavailable Ollama service, a missing model, timeout, or invalid response
shows an error on the ticket detail page. No assessment or human review is
saved for that failed attempt, and **Analyze ticket** remains available to
retry after resolving the problem. Failures never silently fall back to the
mock. Connection/configuration errors return HTTP 503, timeouts return HTTP
504, and Ollama HTTP errors or invalid output return HTTP 502. Raw model
output and internal exception details are not shown on the page.

## Project files

```text
app/
    __init__.py
    main.py
    database.py
    assessment_schema.py
    assessment_errors.py
    assessment_policy.py
    assessment_policy.txt
    ai_service.py
    config.py
    mock_assessment.py
    ollama_provider.py
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
    test_evaluation_reporting.py
    test_ollama_provider.py
    test_shared_policy.py
    test_workflow.py
evaluation/
    __init__.py
    benchmark.py
    tickets.json
requirements.txt
tickets.db                 # Created automatically on server startup
.gitignore
README.md
```

- `app/__init__.py`: Marks `app` as a Python package. It is intentionally empty.
- `app/main.py`: Initializes the database and handles page and form routes. Displays safe assessment errors on the detail page and skips the provider call when the ticket already has an original assessment. Existing review handling is preserved.
- `app/database.py`: Keeps all SQLite logic separate from routes. Accepts an `AIAssessment` when saving a recommendation and reads its attributes into the existing parameterized insert. Table definitions and review storage are unchanged.
- `app/assessment_schema.py`: Defines the validated `AIAssessment` contract and the shared allowed category and priority choices.
- `app/assessment_errors.py`: Defines assessment failures with safe messages and HTTP status codes that routes can display without exposing raw responses.
- `app/assessment_policy.py`: Builds the reusable system prompt from the business policy, existing category guidance, team mapping, and assessment JSON schema. Both the application provider and benchmark use this helper.
- `app/assessment_policy.txt`: The benchmark's existing business policy, moved unchanged from `evaluation/policy.txt` so application and evaluation share the same rules. It contains no ticket-specific examples or expected answers.
- `app/ai_service.py`: Provides `assess_ticket(title, description)`, selects the configured mock or Ollama provider, and validates its result against the contract. It never substitutes mock data after an Ollama failure.
- `app/config.py`: Reads and validates provider, model, and timeout environment settings without adding a configuration package.
- `app/mock_assessment.py`: The unchanged deterministic provider, with keyword rules, team mappings, and summary logic. Returns an `AIAssessment` without language models, network calls, or randomness.
- `app/ollama_provider.py`: Calls the fixed local Ollama chat endpoint using Python's standard library, requests structured output, validates responses, and reports connection, timeout, HTTP, and output failures.
- `app/templates/index.html`: The homepage and required ticket form, with a link to the saved tickets. Validation errors retain the entered values.
- `app/templates/confirmation.html`: Displays the generated ticket ID, title, and description after the ticket is saved, with links to the saved ticket and list.
- `app/templates/tickets.html`: Lists saved ticket IDs, linked titles, and UTC creation times, newest first. Shows a message when no tickets exist.
- `app/templates/ticket_detail.html`: Displays the ticket, Analyze ticket action, original recommendation, review forms, saved final human decision, and assessment errors. The recommendation description now works for either provider. Jinja2 escapes submitted values so input appears as text.
- `app/static/style.css`: Styles pages and form controls, including review dropdowns and sections. Preserves line breaks in submitted text.
- `tests/test_assessment.py`: Tests the assessment contract, mock return type, and safe rejection of invalid provider output. Provider settings are isolated from the developer's environment.
- `tests/test_evaluation.py`: Tests scoring, latency calculations, request settings, the 50-ticket dataset's integrity and coverage, error handling, and a complete 100-row CSV export with mocked HTTP responses; Ollama is not needed.
- `tests/test_evaluation_reporting.py`: Tests correct/incorrect totals, breakdowns by expected category and priority, missing groups, and expected-versus-predicted reporting for misclassified or failed tickets.
- `tests/test_ollama_provider.py`: Tests Ollama request settings, validated responses, configuration, provider selection, and failures without mock fallback using mocked HTTP responses; no model or Ollama server is required.
- `tests/test_shared_policy.py`: Checks that the shared prompt preserves benchmark behavior and that application and benchmark use the same policy.
- `tests/test_workflow.py`: Tests priority rules and the full workflow with isolated environment settings and a temporary database. Also checks visible assessment failures, retry behavior, and preservation of saved recommendations and human decisions.
- `evaluation/__init__.py`: Marks the standalone evaluation directory as a Python package so the benchmark can run with `python -m`.
- `evaluation/benchmark.py`: Calls the local Ollama chat API, validates responses, and writes the existing detailed CSV. Reports overall rates, correct/incorrect totals, category/priority breakdowns, and misclassified ticket details. The request settings, shared policy, scoring rules, and CSV columns are unchanged. It does not import routes, call the application service, or access SQLite.
- `evaluation/tickets.json`: Fifty hand-authored synthetic tickets with predefined category, priority, and team labels. T01-T10 are retained; T11-T50 expand the coverage. Expected labels follow the business policy and are never generated from predictions or sent to the models.
- `requirements.txt`: Lists FastAPI, Uvicorn, Jinja2, `python-multipart`, and Pydantic 2. Pydantic is already installed through FastAPI; it is now declared directly because the application imports it for assessment validation.
- `tickets.db`: The local database, generated automatically; stores tickets, assessments, and reviews between server restarts.
- `.gitignore`: Keeps the virtual environment, Python caches, and local database files out of Git.
- `README.md`: Setup instructions, file explanations, database details, assessment contract, workflow rules, routes, offline tests, Dell application configuration, and benchmark instructions and measurement definitions.

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
The service selects `app/mock_assessment.py` by default, or
`app/ollama_provider.py` when `AI_PROVIDER=ollama`. Both return the same
validated model, and the service validates the result before returning it.
Invalid output is rejected before the route can save or display a
recommendation. The database function accepts the model and writes its
attributes into the existing columns; no database migration is needed.
The example above has the shown deterministic result with the default mock.

The Ollama provider sends the same reusable system prompt used by the benchmark,
with ticket title and description in a separate user message. It supplies
`AIAssessment.model_json_schema()` as Ollama's structured-output `format`,
uses `stream: false`, and sets `temperature: 0`, `seed: 0`, `num_ctx: 4096`,
and `num_predict: 512`. It disables thinking for supported boolean-thinking
model families, including Qwen3; it omits that setting for Gemma3. These
requests use Ollama's [structured-output API](https://docs.ollama.com/capabilities/structured-outputs)
and [thinking controls](https://docs.ollama.com/capabilities/thinking).

Returned content must be valid JSON and pass the existing strict Pydantic
contract. The provider does not repair JSON, strip Markdown fences, or accept
raw text as an assessment. It also rejects `requires_human_review: false`
because this workflow requires an analyst's decision; the reusable schema's
boolean field remains unchanged. Temperature zero controls sampling, but
does not guarantee the same result across model, hardware, or software versions.

New providers can implement the same two-input function and return a validated
`AIAssessment`, then be added to the service's explicit provider selection.
Routes continue to use the service function. Provider failures use the shared
`AssessmentError` so the existing page can report them safely. The mock remains
available for deterministic offline development and tests.

## Assessment and human review

1. Submit a ticket and open its detail page.
2. Select **Analyze ticket**. The service assesses the title and description
   with the configured provider and stores the validated original result in
   `ai_assessments`. A failure displays an error without saving a result.
3. Read the category, priority, summary, recommended team, and human-review flag.
4. Select **Approve unchanged**, or change category, priority, and/or team and
   select **Save final decision**. The edit form starts with the recommendation.
5. The page displays both the original recommendation and final human decision.

Every saved recommendation in this workflow has `requires_human_review = True`.
This original flag stays unchanged after review; the final decision section
shows that review is complete. No recommendation is automatically accepted.
Switching providers does not replace existing assessments. Selecting Analyze
ticket again for an already assessed ticket keeps its original without calling
the provider. Provider/model provenance is not stored in the current schema,
so the page uses a neutral recommendation description for historical mock and
new Ollama assessments.

Approval copies the stored original values on the server. Edited reviews must
use one of the listed categories and priorities and a nonblank team. Invalid
reviews show an error and retain entered values without saving. Saving the edit
form without changes counts as approval. A final decision cannot be saved
before analysis.

### Deterministic mock rules

With the mock provider, the same input always produces the same result.
Matching is case-insensitive and uses simple substring checks. The first
matching category below wins:

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
negation; they are for exercising the workflow. The Ollama provider instead
uses the shared business policy described above.

## Routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/` | Display the submission form |
| POST | `/submit` | Validate and save a ticket, then display confirmation |
| GET | `/tickets` | List saved tickets, newest first |
| GET | `/tickets/{ticket_id}` | Display one saved ticket; return HTTP 404 if it does not exist |
| POST | `/tickets/{ticket_id}/analyze` | Save the configured provider's validated assessment once and redirect to ticket details; display a useful error on failure |
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

The default run makes 100 sequential requests: 50 tickets for `qwen3:1.7b`,
then the same 50 for `gemma3:1b`. It prints progress and one console summary per
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

`app/assessment_policy.txt` expresses the project's business impact definitions,
including the distinction between a single-user disruption and widespread
interruption. It contains no Wi-Fi/client-meeting example. The existing
category precedence and team names are imported from the mock module; expected
answers stay in the dataset and are used only for scoring. The benchmark and
application provider share the same prompt-building helper; moving the policy
did not change its contents or the benchmark's requests and scoring.

All 50 tickets are invented and contain no real organizational/customer data.
Each has an explicit expected category, priority, and recommended team in
`evaluation/tickets.json`. The original T01-T10 remain unchanged for continuity.
The added tickets include natural descriptions, plausible workarounds, and
overlapping symptoms that require attention to the reported cause and impact.

Coverage spans all six categories and all four priorities. Low cases include
planned/nonurgent requests; Medium cases include ordinary single-user incidents;
High cases include blocked work, several business deadlines, and suspicious
events. Critical cases describe widespread disruption or severe incidents
affecting multiple services/users, rather than a single user's urgent deadline.

| Expected category | Low | Medium | High | Critical | Total |
| --- | --- | --- | --- | --- | --- |
| Network | 1 | 3 | 3 | 2 | 9 |
| Hardware | 2 | 3 | 2 | 1 | 8 |
| Software | 2 | 3 | 3 | 1 | 9 |
| Account Access | 1 | 3 | 3 | 1 | 8 |
| Security | 0 | 0 | 5 | 3 | 8 |
| Other | 4 | 3 | 1 | 0 | 8 |
| Total | 10 | 15 | 17 | 8 | 50 |

These labels are authored against the reusable business policy. They are not
required to match the limited mock keyword classifier on every naturally worded
ticket. Tests check dataset integrity and coverage without deriving expected
answers from the mock. No per-ticket instructions or examples were added to
the shared prompt.

### Reading the results

For each model, the console reports correct/incorrect category, priority, and
routing totals, their existing accuracy rates, valid structured-output rate,
and average/median response latency. It also prints category/priority breakdowns
and the IDs of misclassified or failed tickets with expected/predicted values.

- Accuracy is exact, case-sensitive matching: correct predictions divided by
  **all attempted tickets** for that model. Routing accuracy means an exact
  match of the recommended team to the predefined expected team.
- Invalid output and failed requests receive no category, priority, or routing
  credit, even if a partial response contains a correct label. The validation
  rate also uses all attempts as its denominator.
- Per-category accuracy groups tickets by their **expected category** and measures
  correct category decisions within that group. Per-priority accuracy groups by
  **expected priority** and measures correct priority decisions. Wrong or missing
  predictions stay in the expected group's denominator. Each group shows correct,
  total, and incorrect counts; a group absent from a custom dataset shows N/A.
- The misclassified/failed list includes any ticket with an incorrect category,
  priority, or team decision, including failed requests and invalid structured
  output. It shows all three expected/predicted fields, identifies unavailable
  predictions, and flags invalid output that received no accuracy credit.
  If every decision is correct, the list shows None.
- Each CSV row records model and ticket ID, expected/predicted category,
  priority, and team, validation and correctness flags, and elapsed seconds.
  It also includes request status, whether a completed HTTP response arrived,
  the predicted human-review flag when readable, error details, and the raw
  Ollama response for diagnosis. Summary wording and the human-review flag are
  available for inspection; their semantic correctness is not part of the
  three label-accuracy scores. The schema permits either boolean, while the
  business policy asks for `requires_human_review: true`. Benchmark validation
  remains unchanged; the application's Ollama provider additionally rejects a
  false flag before saving so human review remains mandatory.
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
hardware or software versions. The 50-ticket set gives broader coverage but
does not establish production accuracy. Compare results on the same dataset
revision; a prior 10-ticket aggregate is not directly comparable to a new
50-ticket aggregate. The preserved IDs allow comparison on the original subset.

## Tests

From the project folder, run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Workflow tests create and remove their own database files beside `tickets.db`;
they do not change your saved tickets. Tests isolate provider configuration
from your shell settings and mock Ollama HTTP responses. Evaluation tests
clean up their temporary CSV files. No Ollama instance, model download, or
additional test dependency is required.

This stage uses Pydantic 2, already supplied by FastAPI, and declares it as a
direct dependency. It otherwise uses the existing FastAPI, Jinja2, HTML/CSS,
SQLite, Uvicorn, and form-parsing dependencies. Ollama integration and evaluation
use only the Python standard library and existing packages; no Python
dependencies were added for the provider. The application defaults to the mock
and uses local Ollama only when configured. There is no authentication,
Docker, PostgreSQL, or cloud-service integration.
