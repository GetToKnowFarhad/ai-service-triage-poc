# User Acceptance Test Plan

| Document control | Value |
| --- | --- |
| System | AI Service Triage PoC |
| Package version | 1.0 |
| Prepared | 2026-09-08 |
| Status | Ready for manual execution; acceptance pending |
| Application baseline inspected | `2bc53ab164f8a021fc22340255b82525894c7e39` |
| Execution record | [UAT results](uat-results.md) |
| Requirements mapping | [UAT traceability](uat-traceability.md) |
| Business owner / analyst / environment operator | To be assigned before execution; one person may perform several roles |

## 1. Purpose and scope

Validate the implemented request-submission, local AI recommendation, and human-review workflow through ten manual acceptance scenarios on the Dell. The selected real provider is Ollama with `qwen3:1.7b`; the mock remains available for offline operation. The package does not change application behavior or establish new product requirements.

Scope includes required-field validation, structured recommendations, approval, override, preservation of original records, persistence across restart, visible provider failure, recovery, and protection against repeated analysis and provider changes.

Authentication, reviewer identity, cloud services, production readiness, disaster recovery, load testing, model selection, and the 50-ticket benchmark are outside this UAT scope. Do not run the 100-request benchmark as part of these procedures. No accuracy threshold or response-time service level is introduced. Record observed response time for context without treating it as an agreed service level.

The repository has no separate approved BR/FR/NFR, user-story, or acceptance-criteria catalogue. The identifiers below refer to the **UAT-local restatements of existing requirements** in the traceability document. They do not imply prior stakeholder approval of a formal specification.

## 2. Entry conditions and environment

1. Use a dedicated UAT installation on the Dell, containing synthetic data only. Record the project directory and existing `tickets.db` path. Do not replace or delete the database during the run.
2. Record the run ID, tester, date/time/time zone, Git revision and working-tree status, OS, Python version, browser/version, Ollama version, model name and model ID in the results document. Use `git rev-parse HEAD`, `git status --short`, `ollama --version`, and `ollama list` as supporting evidence.
3. Complete the existing [README setup](../README.md#run-the-application-with-ollama-on-the-dell) before UAT. Qwen3 1.7B must already be installed. FastAPI and Ollama must run on the Dell itself: the application's fixed endpoint is `http://localhost:11434/api/chat`.
4. Identify how the UAT Ollama instance is started and stopped. For a dedicated foreground instance, `ollama serve` starts it and `Ctrl+C` in that terminal stops it. For a managed service, record its actual start/stop controls before execution. Stopping only the model with `ollama stop` does not make the HTTP service unavailable and is insufficient for UAT-08.
5. Reserve the UAT instance for this run so unrelated submissions do not affect record counts. The operator must be able to restart the application and Dell and stop/start the UAT Ollama service.
6. Start FastAPI with the following configuration. Run without `--reload` so process restarts are explicit. Keep the terminal startup/configuration evidence; the database and detail page do not record provider/model provenance.

PowerShell, from the project directory:

```powershell
$env:AI_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "qwen3:1.7b"
$env:OLLAMA_TIMEOUT = "120"
Get-ChildItem Env:AI_PROVIDER,Env:OLLAMA_MODEL,Env:OLLAMA_TIMEOUT
.\.venv\Scripts\python.exe -m uvicorn app.main:app
```

Linux shell, from the project directory:

```bash
export AI_PROVIDER=ollama
export OLLAMA_MODEL=qwen3:1.7b
export OLLAMA_TIMEOUT=120
printenv AI_PROVIDER OLLAMA_MODEL OLLAMA_TIMEOUT
.venv/bin/python -m uvicorn app.main:app
```

7. Open `http://127.0.0.1:8000` in a browser on the Dell. Confirm the homepage loads. Use this same browser origin throughout. Record the actual configuration, including any deliberate changes in UAT-10.

## 3. Execution and evidence conventions

- Use a run ID such as `DELL-UAT-YYYYMMDD-01`. Replace `<RUN-ID>` in titles and evidence names with the actual run ID. All descriptions below are invented.
- Execute in this order: UAT-01, UAT-02, UAT-03, UAT-04, UAT-05, UAT-06, UAT-07, UAT-08, UAT-09, UAT-10. Dependencies and required baselines are specified in each case.
- Record generated ticket IDs in the results ledger. A, B, C, and D are fixture labels, not assumed database IDs. Do not reuse reviewed tickets for scenarios that require an unreviewed recommendation.
- Create an evidence directory `docs/evidence/<RUN-ID>/` at execution time. Save screenshots, copied terminal output, and read-only snapshots there. References in this plan are **planned filenames**, not claims that evidence already exists.
- Include the run ID, UAT ID, step, actual ticket ID, and capture time in each evidence record. Use names such as `UAT-06-step-03-after.png` and `UAT-06-step-04-db-after.txt`. Keep the original pre-change evidence for comparison.
- Browser developer tools may be used to observe HTTP requests or deliberately replay an existing HTML form action. This is a manual test aid; it adds no application feature or JSON API.
- Use Appendix A to verify stored rows without writing to SQLite. A screenshot alone cannot establish that a failed attempt saved no row or that an original record's ID and timestamp are unchanged.
- Capture the original recommendation in full: all five assessment fields, database ID, ticket ID, and creation time. Capture final-review ID, assessment ID, decision, category, priority, team, and creation time when applicable.
- The plan contains initial result placeholders. After execution, maintain actual results, evidence references, defects, and sign-off in [uat-results.md](uat-results.md); that register is authoritative.

### Status rules and exit criteria

`PASS` means a tester completed every required step, observed all expected results, and attached evidence. `FAIL` means an observed result contradicted an expected result; identify the step and defect. `NOT EXECUTED` means the case has not been completed, including a blocked dependency; record any partial observations without claiming a pass. A failed prerequisite may leave dependent cases not executed rather than imply additional product defects.

For this package's acceptance recommendation, all ten scenarios must pass and no unresolved defect may prevent a stated acceptance criterion from being met. The business owner records the final decision and any explicitly accepted limitations. Passing automated tests does not meet the manual exit criteria. Retests must retain the original failure and evidence in the execution history.

## 4. Synthetic test data

| Fixture | Ticket title | Ticket description | Purpose |
| --- | --- | --- | --- |
| A | `[UAT <RUN-ID> A] Wi-Fi disconnects before a client meeting` | `My laptop keeps losing Wi-Fi. I have a client meeting in 20 minutes and cannot stay connected to the meeting. Only I am affected.` | Valid submission, real assessment, unchanged approval, restart, preservation. Policy interpretation: Network / High / Network Support. |
| B | `[UAT <RUN-ID> B] Monitor intermittently goes blank` | `My desk monitor goes blank for a few seconds. I can continue working on the laptop screen. Only my desk is affected and there is no deadline today.` | Real recommendation followed by a deliberate analyst correction and original-record comparison. Initial policy interpretation: Hardware / Medium / Hardware Support. |
| C | `[UAT <RUN-ID> C] PDF application closes unexpectedly` | `The PDF application closes when I open one document. I can read it in the browser and continue my work. Only I am affected and there is no immediate deadline.` | Unavailable Ollama, then retry of the same ticket. Policy interpretation: Software / Medium / Software Support. |
| D | `[UAT <RUN-ID> D] Planned software installation` | `Please install the drawing software next month for later use. No rush; my current work is unaffected.` | New mock control ticket during provider-switch testing. Deterministic expectation: Software / Low / Software Support. |

For UAT-05, the analyst receives this **synthetic follow-up fact outside the original ticket**: investigation attributes the blank display to a display-management application, and an imminent presentation is now blocked. Save final category `Software`, priority `High`, and team `UAT Application Support`. This tests analyst control over the final values; it does not change the model's original input, category-to-team policy, or the original recommendation. The current review form permits a nonblank analyst-selected team rather than requiring the model's team mapping.

## 5. UAT scenarios

### UAT-01 — Submit a valid service request

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-01; FR-01, FR-02; AC-01 |
| Objective | Confirm a valid request is saved before confirmation and can be retrieved. |
| Preconditions | Entry conditions met; fixture A has not been submitted in this run. |
| Test data | Fixture A, with the actual run ID substituted. |
| Expected result | Confirmation displays `Request received`, a generated integer ticket ID, and the submitted title and description. The ticket appears in `/tickets` with its title and UTC creation time and opens at `/tickets/{id}`. Exactly one new ticket exists; no assessment or review exists yet. |
| Actual result | NOT EXECUTED — awaiting manual browser execution on the Dell. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-01-before-counts.txt`, `UAT-01-confirmation.png`, `UAT-01-list.png`, `UAT-01-detail.png`, `UAT-01-db-after.txt` in the run directory. |
| Notes | Record the actual ID as A. Navigate using links after submission; refreshing the confirmation POST may create another ticket. |

**Exact steps**

1. Record baseline table counts with Appendix A; before the first ticket use an empty `ticket_ids` list.
2. Open `/`, enter A's title and description, and click **Submit request** once.
3. Capture the confirmation and record the generated ID in the results ledger.
4. Click **View all tickets**. Locate A and capture its ID, linked title, and UTC creation time.
5. Open A's title link. Verify both submitted fields and `No recommendation yet.` with **Analyze ticket** available.
6. Run Appendix A for A. Compare the before/after counts and confirm one ticket row with the submitted values, a creation timestamp, and empty assessment/review lists.

### UAT-02 — Reject empty and whitespace-only fields

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-01; FR-01; AC-02 |
| Objective | Confirm neither browser validation nor direct form submission permits a blank required field to be saved. |
| Preconditions | Homepage available; A exists; no concurrent submissions; browser developer tools available. |
| Test data | The six invalid input pairs below. `VALID TITLE` means `[UAT <RUN-ID> INVALID] General request`; `VALID DESCRIPTION` means `Synthetic request used only to check required fields.` |
| Expected result | Browser required-field validation prevents empty submissions normally. When submitted to FastAPI, every invalid pair returns HTTP 400 and `Please enter both a ticket title and a ticket description.` No confirmation or new ticket is created. A supplied valid companion field remains visible, with surrounding whitespace trimmed. |
| Actual result | NOT EXECUTED — none of the input pairs has been manually exercised. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-02-browser-required.png`, `UAT-02-pair-01.png` through `UAT-02-pair-06.png`, corresponding HTTP status captures, and before/after count snapshots. |
| Notes | All six server-side pairs and the normal browser check must succeed for this scenario to pass. Disabling browser validation below affects only the current test page. |

| Pair | Title | Description |
| --- | --- | --- |
| 01 | Empty | VALID DESCRIPTION |
| 02 | VALID TITLE | Empty |
| 03 | Empty | Empty |
| 04 | Three spaces | VALID DESCRIPTION |
| 05 | VALID TITLE | Three spaces |
| 06 | Three spaces | Three spaces |

**Exact steps**

1. Record table counts with Appendix A. Open a fresh `/` page, leave both fields empty, and click **Submit request**. Capture the browser's required-field feedback; verify no `/submit` request was sent in the Network panel.
2. For pair 01, reopen `/`, enter the specified values, and open developer tools on this page.
3. In the browser Console run `document.querySelector('form').noValidate = true;` so the server's validation can also be checked. Keep the Network panel open.
4. Click **Submit request**. Capture the returned error page, HTTP 400 for `POST /submit`, and retained valid field, if present. Verify no generated-ID confirmation is shown.
5. Repeat steps 2–4 for pairs 02–06, starting with a fresh page and disabling browser validation again for each pair. Enter actual spaces, not the words “Three spaces.”
6. Rerun Appendix A and verify ticket, assessment, and review counts are unchanged. Refresh `/tickets` and verify no invalid test request appears. Record each pair's actual result in the results subcase table.

### UAT-03 — Generate a structured recommendation with Qwen3 1.7B

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-02, BR-03; FR-03, FR-04; AC-03 |
| Objective | Confirm the browser workflow obtains and stores a valid recommendation from the real local provider. |
| Preconditions | UAT-01 passed; A has no assessment; `AI_PROVIDER=ollama`, `OLLAMA_MODEL=qwen3:1.7b`; Ollama is reachable and the model installed. |
| Test data | Saved fixture A, unchanged. |
| Expected result | A successful analysis returns to the detail page showing category, priority, nonblank factual summary, recommended team, and human-review flag `Yes`. A's business interpretation is Network / High / Network Support. Exactly one original assessment and no review are stored. Human review remains pending and the Analyze action is no longer displayed. |
| Actual result | NOT EXECUTED — no live Ollama request has been made for this UAT package. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-03-config.txt`, `UAT-03-model-list.txt`, `UAT-03-ollama-request-log.txt`, `UAT-03-recommendation.png`, `UAT-03-db-original.txt`. |
| Notes | A mock result cannot satisfy this case. A schema-valid but policy-inconsistent classification is recorded as a failure of the stated expected result. Do not modify the prompt or repeatedly generate until an answer passes. |

**Exact steps**

1. Capture the FastAPI launch configuration, `ollama list` model ID, and Ollama version. Open A's detail page and confirm it has no recommendation.
2. Note the request start time, click **Analyze ticket** once, and record elapsed time and the HTTP outcome in browser developer tools.
3. Capture the resulting recommendation. Check all five fields against the contract in Appendix C, the expected category/priority/team above, and the original ticket facts. Do not require a fixed summary sentence.
4. Confirm **Approve unchanged** and the final-decision edit form are available, while no **Final human decision** is yet shown.
5. Capture the matching Ollama `/api/chat` request log and `ollama ps` output promptly after the request. Correlate the time with the browser action and retain the configured model/model ID. If real-provider provenance cannot be established, record the evidence gap rather than claim a real-model pass.
6. Run Appendix A for A; save the entire original row and verify one assessment, `requires_human_review` stored as `1`, and no review. This snapshot is the unchanged-approval baseline.

The UI does not expose raw JSON. Strict JSON typing and rejection of invalid output are supported by the offline contract/provider tests and the inspected validation boundary; screenshots alone do not prove raw JSON compliance. A successful real browser request exercises that same boundary before persistence. Record both kinds of evidence without presenting mocked responses as a live run.

### UAT-04 — Approve the recommendation unchanged

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-03, BR-04; FR-05, FR-07; AC-04 |
| Objective | Confirm approval copies the stored recommendation into a separate final human decision. |
| Preconditions | UAT-03 passed; A has its original assessment and no human review; original snapshot retained. |
| Test data | A's saved category, priority, and recommended team; no edits. |
| Expected result | Both recommendation and final decision are visible. The decision reads `Approved unchanged`; its category, priority, and team exactly match the original. One separate review is stored, and the original assessment remains identical. Review controls are removed after saving. |
| Actual result | NOT EXECUTED — awaiting analyst interaction. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-04-approved.png`, `UAT-04-db-after.txt`; baseline `UAT-03-db-original.txt`. |
| Notes | The original human-review flag remains `Yes`; the final decision section indicates review completion. |

**Exact steps**

1. Open A and compare the displayed recommendation to the UAT-03 baseline.
2. Click **Approve unchanged** once.
3. Capture the page with both sections. Compare final category, priority, and team to the original values, and confirm `Approved unchanged` and a UTC review time.
4. Refresh the detail page. Verify the saved decision remains and neither review form is available.
5. Run Appendix A for A. Verify one review with `decision=approved`, linked to the original assessment ID. Compare the complete assessment row with the baseline and retain this reviewed-ticket snapshot for UAT-07 and UAT-10.

### UAT-05 — Modify category, priority, and team

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-03; FR-06; AC-05 |
| Objective | Confirm an analyst can save changes to all three final-decision fields. |
| Preconditions | Real Ollama available; new fixture B with no final review; follow-up facts from section 4 available to the analyst. |
| Test data | Fixture B; final category `Software`, priority `High`, team `UAT Application Support`. |
| Expected result | The edit controls initially contain the saved recommendation. The final decision records all three selected values and `Modified by analyst`, separately from the original recommendation. Both sections are visible after saving; the decision persists on refresh. |
| Actual result | NOT EXECUTED — awaiting submission, real analysis, and analyst edits. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-05-before.png`, `UAT-05-db-before.txt`, `UAT-05-edits.png`, `UAT-05-final.png`, `UAT-05-db-after.txt`. |
| Notes | Retain the before snapshot for UAT-06. If a generated field already equals the intended override, record it and select another allowed value for that field solely to exercise editing; record the exact test substitution and rationale. This does not establish a new policy label. |

**Exact steps**

1. Submit B using the UAT-01 browser procedure, record its ID, and open its detail page. Click **Analyze ticket** with the real Ollama configuration.
2. Capture the complete original recommendation and an Appendix A snapshot before review. Record any policy discrepancy against B's initial interpretation; do not silently correct it in the original.
3. Confirm the edit form defaults match the original category, priority, and team. Ensure the planned edits change each field; document any necessary test substitution as described above.
4. Select **Final category** `Software`, **Final priority** `High`, and enter **Final team** `UAT Application Support` (or the recorded substitutions). Capture the populated form.
5. Click **Save final decision**. Verify `Modified by analyst` and that all final fields match the entered values, with the original recommendation still displayed.
6. Refresh the detail page and take an Appendix A snapshot. Verify one linked review with `decision=modified`, the selected values, and a review timestamp. Use UAT-06 for the full original-record comparison.

### UAT-06 — Preserve the original after human override

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-04; FR-07; AC-06 |
| Objective | Confirm the override does not alter any original recommendation field or its identity. |
| Preconditions | UAT-05 completed with a saved modified decision; its before/after evidence is available. |
| Test data | B's original assessment snapshot and saved final human decision. |
| Expected result | Original assessment ID, ticket ID, category, priority, summary, recommended team, review flag, and creation time match the pre-review snapshot exactly. The final decision has its own row and ID, references that assessment, and retains the analyst's values. Both are displayed independently. |
| Actual result | NOT EXECUTED — comparison requires the manual UAT-05 evidence. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-06-comparison.txt`, `UAT-06-both-sections.png`, `UAT-06-db-after.txt`; baseline `UAT-05-db-before.txt`. |
| Notes | Check the full row, not only its category and priority. The original summary and flag must not change when the review is saved. |

**Exact steps**

1. Open B's detail page and the UAT-05 pre-review snapshot side by side.
2. Compare each displayed original value, including the full summary and flag, to the baseline. Separately check the final values against the recorded override.
3. Capture both sections on the detail page; use multiple screenshots if necessary to include every value.
4. Run Appendix A for B and compare every column of the original assessment with `UAT-05-db-before.txt`. Record a field-by-field comparison in `UAT-06-comparison.txt`.
5. Confirm there is one assessment and one review, that the review references the original ID, and that final and original values remain distinguishable. Retain this snapshot for restart testing.

### UAT-07 — Persist tickets and reviews after restart

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-01, BR-04; FR-02, FR-07, FR-08; AC-07 |
| Objective | Confirm saved tickets, recommendations, and both review types survive application-process and Dell-server restarts. |
| Preconditions | UAT-04 and UAT-06 passed; A and B reviewed; operator can restart the dedicated UAT Dell; database path and configuration recorded. |
| Test data | Existing A (approved) and B (modified), with complete pre-restart snapshots. |
| Expected result | After each restart, A and B are listed and accessible with identical ticket, assessment, and review rows, including IDs, relationships, text, and timestamps. No resubmission, re-analysis, or second review is required. |
| Actual result | NOT EXECUTED — neither a live application restart nor a Dell reboot has been performed for UAT. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-07-db-before.txt`, `UAT-07-process-restart.txt`, `UAT-07-db-after-process.txt`, `UAT-07-reboot.txt`, `UAT-07-db-after-reboot.txt`, A/B screenshots after each phase. |
| Notes | Both phases must be completed for PASS. If the Dell reboot cannot be performed, record the process-phase observation and leave the scenario NOT EXECUTED with the limitation. Automatic service startup is not a requirement. |

**Exact steps**

1. Capture A/B list and detail pages, an Appendix A snapshot, the absolute database path, and the current launch configuration.
2. Stop FastAPI with `Ctrl+C`. Confirm the process has exited, then restart it from the same project using the same environment configuration. Do not delete, replace, or initialize a new database manually.
3. Reload `/tickets` and both detail URLs. Compare every saved field with the baseline and capture evidence plus `UAT-07-db-after-process.txt`.
4. Stop the UAT application cleanly and reboot the Dell using its normal OS restart control. Record the shutdown and boot times. Reopen the same project and restore the recorded environment variables; start Ollama and FastAPI as needed.
5. Reopen the browser and retrieve A and B by their original URLs. Compare their rows and both visible decision sections to the original baseline. Capture `UAT-07-db-after-reboot.txt` and screenshots.
6. Record the result of each phase in the results subcase table and confirm no Analyze or review action was needed to restore the records.

### UAT-08 — Report unavailable Ollama without saving a recommendation

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-02, BR-05; FR-04, FR-09; AC-08 |
| Objective | Confirm real-provider unavailability is visible and does not create a recommendation or substitute mock data. |
| Preconditions | FastAPI remains running with `AI_PROVIDER=ollama`; C is a newly submitted ticket with no assessment/review; operator can stop the dedicated Ollama service. |
| Test data | Fixture C. |
| Expected result | `POST /tickets/{C}/analyze` returns HTTP 503. The detail page states that Ollama is unavailable at `http://localhost:11434`, advises starting the service and retrying, and says `No recommendation was saved.` C remains saved, with no assessment or review, and Analyze remains available. |
| Actual result | NOT EXECUTED — the Dell Ollama service has not been stopped for this test. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-08-config.txt`, `UAT-08-service-unavailable.txt`, `UAT-08-error.png`, `UAT-08-http-status.png`, `UAT-08-db-before.txt`, `UAT-08-db-after.txt`. |
| Notes | This case exercises connection failure. Timeout, HTTP, malformed JSON, and schema failures have separate automated evidence; do not claim they were all induced manually by this case. |

**Exact steps**

1. Submit C through the browser, record its ID, and open its detail page without analyzing it. Capture its row and empty assessment/review lists with Appendix A.
2. Capture FastAPI's Ollama configuration. Stop the dedicated Ollama HTTP service using the control recorded in section 2; leave FastAPI running.
3. Verify the endpoint is unavailable using Appendix B and capture the connection failure. If a service supervisor restarts it, resolve that test setup issue before continuing.
4. On C, click **Analyze ticket** once with the Network panel open. Capture HTTP 503 and the useful visible error, including `No recommendation was saved.`
5. Confirm **Analyze ticket** is still present, no recommendation values or review form are displayed, and C is still in `/tickets`.
6. Run Appendix A for C. Verify its ticket row is unchanged and both assessment and review lists are empty. Retain C, its URL, and the failure evidence for UAT-09; do not switch to mock to complete it.

### UAT-09 — Retry the same ticket after Ollama is restored

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-05; FR-03, FR-10; AC-09 |
| Objective | Confirm a failed attempt does not prevent a later successful real assessment of the same ticket. |
| Preconditions | UAT-08 passed; C still has no assessment/review; FastAPI remains configured for Ollama and Qwen3 1.7B. |
| Test data | The existing C ID, title, and description from the failed attempt. |
| Expected result | Retrying succeeds through the real provider. C's original ticket ID, content, and timestamp are unchanged. Exactly one valid assessment is created for C, the error is absent on the successful detail page, and human review is pending with no saved final decision. |
| Actual result | NOT EXECUTED — awaiting a real failure followed by service restoration and browser retry. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-09-service-restored.txt`, `UAT-09-retry.png`, `UAT-09-ollama-request-log.txt`, `UAT-09-db-after.txt`; baseline UAT-08 snapshots. |
| Notes | Creating a different ticket or accepting mock output does not satisfy this scenario. |

**Exact steps**

1. Restart the same Ollama service and confirm the endpoint responds using Appendix B. Capture service readiness and `ollama list` showing `qwen3:1.7b`.
2. Confirm FastAPI still uses `AI_PROVIDER=ollama` and the selected model. Reopen the exact C detail URL recorded in UAT-08; do not submit a new request.
3. Click **Analyze ticket** once. Record elapsed time, successful redirect/detail response, and the corresponding Ollama request evidence.
4. Verify a valid five-field recommendation with review flag `Yes`, a factual summary, and C's policy interpretation Software / Medium / Software Support. Verify human review is pending and no failure alert remains.
5. Run Appendix A for C. Compare its ticket row to the UAT-08 snapshot, confirm exactly one assessment and zero reviews, and verify the overall ticket count did not increase during retry.

### UAT-10 — Preserve saved recommendations across repeats and provider changes

| Field | Detail |
| --- | --- |
| Related business / functional requirement | BR-04, BR-05; FR-07, FR-11; AC-10 |
| Objective | Confirm an existing original is retained without a provider call, including after selecting another provider. |
| Preconditions | A has a real saved assessment and approved review; original snapshots retained; operator can restart FastAPI with different provider settings and stop/start Ollama. |
| Test data | Existing real-provider ticket A; new fixture D assessed with mock as a control. |
| Expected result | Repeated Analyze POSTs redirect to the saved detail page without changing any assessment or review field or creating duplicates. A's real result survives a switch to mock; D's mock result survives a switch to Ollama. With Ollama unavailable, both already-assessed tickets remain usable without an analysis error. No new Ollama generation occurs for a saved assessment. |
| Actual result | NOT EXECUTED — no manual repeated POST or provider-switch check has been performed. |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot reference | Planned: `UAT-10-config-mock.txt`, `UAT-10-config-ollama.txt`, `UAT-10-db-baselines.txt`, `UAT-10-replay-statuses.txt`, `UAT-10-unavailable.txt`, `UAT-10-db-final.txt`, A/D screenshots and correlated Ollama logs. |
| Notes | The normal UI hides Analyze after saving. Appendix B's browser replay deliberately exercises the existing POST route. No route or UI change is required. The mock control is explicitly identified as mock evidence. |

**Exact steps**

1. Capture A's complete ticket, assessment, and review rows. While Ollama is still available, replay Analyze on A using Appendix B. Verify HTTP 303 followed by the saved detail page and no corresponding new `/api/chat` generation in the isolated Ollama log.
2. Stop FastAPI. Set `AI_PROVIDER=mock` in its launching shell (`$env:AI_PROVIDER = "mock"` in PowerShell or `export AI_PROVIDER=mock` on Linux), capture the setting, and restart the same app with the same database.
3. Open A and replay Analyze again. Compare its full saved rows with the baseline and verify the approved human decision remains visible.
4. Submit D and click its normal **Analyze ticket** button. Verify the deterministic mock result Software / Low / Software Support with review flag `Yes`. Capture its original row, ID, timestamp, and summary as D's baseline; leave D unreviewed.
5. Stop FastAPI, restore `AI_PROVIDER=ollama`, `OLLAMA_MODEL=qwen3:1.7b`, and the recorded timeout, then restart. Stop the UAT Ollama HTTP service and capture the unavailable endpoint using Appendix B.
6. Replay Analyze separately on A and D. Capture both HTTP 303 redirects and detail pages. Neither should show an Ollama error despite the unavailable service; neither should acquire a new recommendation or review.
7. Run Appendix A for A and D and compare all fields to their baselines. Confirm exactly one assessment per ticket, A's single original review, and no review for D. Record each replay's result in the results subcase table. The offline no-provider-call assertion supplements these live observations.
8. Restore the Ollama service, confirm readiness, and leave FastAPI on the recorded Ollama configuration. Record the restored end state.

## Appendix A — Read-only database evidence

Use this procedure on the Dell from the recorded project root after FastAPI has created `tickets.db`. It uses Python's existing standard library and opens SQLite in read-only mode. It neither imports application startup code nor changes schema or records.

Start the project's Python interpreter:

```powershell
.\.venv\Scripts\python.exe
```

On Linux use `.venv/bin/python`. Paste the following statements into that interpreter. Replace the example integer IDs in `ticket_ids` with the actual recorded fixture IDs; use `[]` for counts before any fixture exists. The comprehensions are single expressions and require no interactive loop blocks.

```python
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ticket_ids = [1, 2, 3]
database_path = Path("tickets.db").resolve()
connection = sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
queries = {
    "ticket": "SELECT * FROM tickets WHERE id = ?",
    "assessments": "SELECT * FROM ai_assessments WHERE ticket_id = ? ORDER BY id",
    "reviews": "SELECT r.* FROM human_reviews r JOIN ai_assessments a ON a.id = r.assessment_id WHERE a.ticket_id = ? ORDER BY r.id",
}
counts = dict(connection.execute("SELECT (SELECT COUNT(*) FROM tickets) AS tickets, (SELECT COUNT(*) FROM ai_assessments) AS ai_assessments, (SELECT COUNT(*) FROM human_reviews) AS human_reviews").fetchone())
records = {str(ticket_id): {name: [dict(row) for row in connection.execute(sql, (ticket_id,))] for name, sql in queries.items()} for ticket_id in ticket_ids}
print(json.dumps({"captured_at_utc": datetime.now(timezone.utc).isoformat(), "database_path": str(database_path), "counts": counts, "records": records}, indent=2))
connection.close()
exit()
```

Copy the printed JSON to the scenario's planned `.txt` evidence file. Compare `records` and relevant counts; the evidence capture timestamp necessarily changes and is not a stored application timestamp. Queries use fixed SQL and parameterized IDs. SQLite stores the review flag as integer `0`/`1`; the API contract requires a true JSON boolean before persistence. A database snapshot is not a capture of the raw model response.

## Appendix B — Manual operational checks

### Check Ollama service reachability

From the project directory, this read-only check contacts the existing local tags endpoint and prints its status and model list:

```powershell
.\.venv\Scripts\python.exe -c "from urllib.request import ProxyHandler, build_opener; response = build_opener(ProxyHandler({})).open('http://localhost:11434/api/tags', timeout=5); print(response.status); print(response.read().decode()); response.close()"
```

On Linux replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`. Capture successful HTTP 200 when restored and a connection-refused/unreachable error when stopped. An absent model or an unloaded model with a reachable service is not the unavailable-service condition. This operator diagnostic can print a Python exception; the separate browser test must still show the application's safe error page.

### Replay an existing Analyze form action

Open the target ticket's exact detail URL `/tickets/{id}` in the browser. Open developer tools, enable **Preserve log** in Network, and run this in the Console:

```javascript
{
  const form = document.createElement("form");
  form.method = "POST";
  form.action = window.location.pathname + "/analyze";
  document.body.appendChild(form);
  form.submit();
}
```

This submits the existing HTML form route for the currently displayed ticket. Record the POST's HTTP 303 and the following GET's HTTP 200; checking only the final page would miss the redirect status. Repeat from the appropriate detail page when instructed. Do not run it on `/tickets`, `/submit`, or another page.

## Appendix C — Existing assessment and decision expectations

| Contract field | Existing rule |
| --- | --- |
| `category` | Exactly Network, Hardware, Software, Account Access, Security, or Other |
| `priority` | Exactly Low, Medium, High, or Critical |
| `summary` | Required nonblank string, factual and limited to reported information |
| `recommended_team` | Required nonblank string; model policy uses the mapping below |
| `requires_human_review` | Strict boolean; this application's Ollama provider requires `true` |

All five fields are required. Extra fields, invalid choices, wrong types, malformed JSON, or blank text are rejected before saving or displaying an assessment. The schema itself accepts either boolean; the provider additionally enforces mandatory review. Raw text, Markdown fences, and repaired JSON are not accepted substitutes.

| Category | Model's recommended team |
| --- | --- |
| Network | Network Support |
| Hardware | Hardware Support |
| Software | Software Support |
| Account Access | Identity and Access |
| Security | IT Security |
| Other | Service Desk |

The shared [business policy](../app/assessment_policy.txt) defines Low as minimal impact without urgency; Medium as an ordinary single-user issue without major immediate or time-sensitive impact; High as blocked or significantly affected important work, meaningful time sensitivity, or a suspicious/security event; and Critical as broad disruption or an obviously severe incident affecting multiple users/services. Single-user urgency alone is not Critical.

These are the existing rules. The same policy and schema remain shared by application and benchmark. UAT data and expected results must not be inserted into the model prompt to obtain a passing result.
