# User Acceptance Test Results

| Document control | Value |
| --- | --- |
| System / package | AI Service Triage PoC / UAT 1.0 |
| Prepared | 2026-09-08 |
| Manual execution status | NOT EXECUTED |
| Acceptance status | Pending manual Dell execution and business-owner review |
| Procedures | [UAT plan](uat-plan.md) |
| Requirements | [UAT traceability](uat-traceability.md) |

This register contains no claimed manual passes. The package was prepared from the current implementation and automated tests. No browser UAT, live Qwen3 request, Ollama outage/restoration, or Dell restart was performed during document preparation. Automated evidence below is supporting engineering evidence and does not replace user acceptance testing.

## 1. Manual run record

Complete these fields before executing the plan. Record each subsequent run separately or retain an archived copy with its run ID.

| Field | Actual value |
| --- | --- |
| Run ID | NOT RECORDED |
| Tester / analyst | NOT ASSIGNED |
| Business owner / acceptance authority | NOT ASSIGNED |
| Environment operator | NOT ASSIGNED |
| Start / finish, with time zone | NOT EXECUTED |
| Dell host identifier and OS/version | NOT RECORDED |
| CPU / RAM / GPU, if present | NOT RECORDED |
| Project directory / absolute `tickets.db` path | NOT RECORDED |
| Git revision / working-tree changes on Dell | NOT RECORDED |
| Python / browser versions | NOT RECORDED |
| Ollama version / `qwen3:1.7b` model ID | NOT RECORDED |
| Actual `AI_PROVIDER`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT` | NOT RECORDED; planned starting values: ollama, qwen3:1.7b, 120 |
| Ollama start/stop controls | NOT RECORDED |
| Evidence directory | Planned: `docs/evidence/<RUN-ID>/`; not yet populated |
| End-state configuration and service readiness | NOT EXECUTED |

### Fixture ledger

| Fixture | Actual ticket ID / detail URL | Assessment ID | Review ID | Purpose |
| --- | --- | --- | --- | --- |
| A | NOT CREATED | NOT CREATED | NOT CREATED | Real recommendation, unchanged approval, restart, preservation |
| B | NOT CREATED | NOT CREATED | NOT CREATED | Real recommendation, override, original comparison, restart |
| C | NOT CREATED | NOT CREATED | NOT CREATED | Failure then retry of the same ticket |
| D | NOT CREATED | NOT CREATED | Not planned | Mock recommendation retained after selecting Ollama |

These are placeholders for tickets the tester will create, not statements about records already present in a development database.

## 2. Scenario results register

Objectives, preconditions, synthetic data, exact steps, expected results, requirement references, and planned evidence are defined for each linked case in the plan. Enter observed results here, including actual values and any failed step. Replace planned evidence references only when the corresponding artifacts exist.

| UAT ID / procedure | Expected outcome | Actual result | PASS / FAIL / NOT EXECUTED | Evidence / screenshot reference | Notes |
| --- | --- | --- | --- | --- | --- |
| [UAT-01](uat-plan.md#uat-01--submit-a-valid-service-request) | Valid request saved once; generated ID, fields, list entry, and detail page available | NOT EXECUTED — no manual submission observed | NOT EXECUTED | None captured; planned `UAT-01-*` | Record generated A ID; no dedicated `/submit` test is claimed from the automated suite |
| [UAT-02](uat-plan.md#uat-02--reject-empty-and-whitespace-only-fields) | Browser and server reject required-field failures; no row saved | NOT EXECUTED — browser check and six input pairs pending | NOT EXECUTED | None captured; planned `UAT-02-*` | Complete every subcase below |
| [UAT-03](uat-plan.md#uat-03--generate-a-structured-recommendation-with-qwen3-17b) | Real Qwen3 produces a validated, policy-consistent five-field recommendation; human review pending | NOT EXECUTED — no live Dell/Ollama generation observed | NOT EXECUTED | None captured; planned `UAT-03-*` | Capture provider/model provenance separately from database rows |
| [UAT-04](uat-plan.md#uat-04--approve-the-recommendation-unchanged) | Approval copies original values into a separate review | NOT EXECUTED — analyst approval pending | NOT EXECUTED | None captured; planned `UAT-04-*` | Depends on UAT-03 |
| [UAT-05](uat-plan.md#uat-05--modify-category-priority-and-team) | All three analyst edits are saved as a modified final decision | NOT EXECUTED — analyst override pending | NOT EXECUTED | None captured; planned `UAT-05-*` | Record any test-value substitution and original classification discrepancy |
| [UAT-06](uat-plan.md#uat-06--preserve-the-original-after-human-override) | Every original field, ID, and timestamp is unchanged; review is separately linked | NOT EXECUTED — before/after comparison pending | NOT EXECUTED | None captured; planned `UAT-06-*` plus UAT-05 baseline | Depends on UAT-05 evidence |
| [UAT-07](uat-plan.md#uat-07--persist-tickets-and-reviews-after-restart) | A/B records survive application restart and Dell reboot unchanged | NOT EXECUTED — both live restart phases pending | NOT EXECUTED | None captured; planned `UAT-07-*` | Automated lifespan re-entry is not a Dell restart |
| [UAT-08](uat-plan.md#uat-08--report-unavailable-ollama-without-saving-a-recommendation) | Useful HTTP 503 error; C retained; no recommendation/review or fallback | NOT EXECUTED — live outage has not been induced | NOT EXECUTED | None captured; planned `UAT-08-*` | Preserve failed C for retry |
| [UAT-09](uat-plan.md#uat-09--retry-the-same-ticket-after-ollama-is-restored) | Restored real provider assesses the same C once; ticket unchanged and review pending | NOT EXECUTED — live recovery/retry pending | NOT EXECUTED | None captured; planned `UAT-09-*` | Failure and success in separate unit tests do not prove this live sequence |
| [UAT-10](uat-plan.md#uat-10--preserve-saved-recommendations-across-repeats-and-provider-changes) | Repeated requests and provider switches preserve real and mock originals and existing review | NOT EXECUTED — live repeated requests and switches pending | NOT EXECUTED | None captured; planned `UAT-10-*` | Include the unavailable-service check and restore the end state |

### Required subcase observations

Subcases do not increase the ten-scenario total. The parent case can pass only when all its required checks are complete and meet expectations.

| Parent / subcase | Actual observation | Status | Evidence |
| --- | --- | --- | --- |
| UAT-02 / browser required-field check | Pending | NOT EXECUTED | None |
| UAT-02 / 01 empty title, valid description | Pending | NOT EXECUTED | None |
| UAT-02 / 02 valid title, empty description | Pending | NOT EXECUTED | None |
| UAT-02 / 03 both empty | Pending | NOT EXECUTED | None |
| UAT-02 / 04 spaces-only title | Pending | NOT EXECUTED | None |
| UAT-02 / 05 spaces-only description | Pending | NOT EXECUTED | None |
| UAT-02 / 06 both spaces-only | Pending | NOT EXECUTED | None |
| UAT-07 / application process restart | Pending | NOT EXECUTED | None |
| UAT-07 / Dell reboot | Pending | NOT EXECUTED | None |
| UAT-10 / repeat existing real recommendation with Ollama selected | Pending | NOT EXECUTED | None |
| UAT-10 / existing real recommendation with mock selected | Pending | NOT EXECUTED | None |
| UAT-10 / fresh mock control D | Pending | NOT EXECUTED | None |
| UAT-10 / existing real A with Ollama selected but unavailable | Pending | NOT EXECUTED | None |
| UAT-10 / existing mock D with Ollama selected but unavailable | Pending | NOT EXECUTED | None |
| UAT-10 / restore recorded Ollama end state | Pending | NOT EXECUTED | None |

### Execution / retest entry template

Append a completed entry for each attempt; retain earlier attempts if a defect is fixed. Do not overwrite failure history with a later pass.

| Field | Entry to complete |
| --- | --- |
| Run ID / UAT ID / attempt number | Pending |
| Tester / execution time and time zone | Pending |
| Requirement / objective / preconditions | Reference linked plan case; record actual precondition checks |
| Actual ticket IDs and test data | Pending; include any declared substitutions |
| Step-by-step observations / actual result | Pending; include HTTP outcomes and compared field values where required |
| Expected result met? | Pending; identify deviations by step |
| PASS / FAIL / NOT EXECUTED | NOT EXECUTED |
| Evidence / screenshot references | None captured |
| Defect IDs / blocked dependencies / notes | Pending |

## 3. Supporting automated test evidence

The previously reported baseline was 68 passing unit tests. After creating this package, the complete suite was rerun in the development workspace and all 68 tests passed. This is supporting automated evidence, not manual UAT evidence.

| Item | Result |
| --- | --- |
| Command | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` |
| Current run status | **PASS — exit code 0; full suite completed** |
| Run time (UTC) | 2026-09-08 03:32:27–03:32:28; exact timestamps in the log |
| Test count / failures / errors / skipped | **68 / 0 / 0 / 0** |
| Environment | Windows development workspace; Python 3.13.0; offline mocked HTTP and temporary test databases |
| Detailed evidence | [Full unit-test output and execution metadata](evidence/unit-tests.txt) |
| Dell/Ollama calls | None required by this suite; live UAT remains separate |

The [traceability matrix](uat-traceability.md#3-scenario-to-requirement-matrix) identifies relevant test methods and evidence limitations. The unit total counts discovered test methods, not each `subTest` input or each mocked model request. It is not the UAT scenario count.

## 4. Defect and retest register

No product defect has been identified during package preparation. No manual UAT has run, so this is not evidence that the live system is defect-free. If a case cannot start because a prerequisite is missing, record the limitation and dependency; do not invent a product defect or PASS.

| Defect ID | UAT ID / failed step | Observed vs expected / reproduction | Impact and severity | Evidence | Owner / status | Retest run / result |
| --- | --- | --- | --- | --- | --- | --- |
| None logged | Not applicable | Manual execution pending | Not assessed | None | Not assigned | Not executed |

For observed defects, use IDs such as `UAT-DEF-001`. Classify impact as blocking acceptance, materially impairing a scenario, or minor presentation/usability; record the reason. Any proposed change to policy, schema, architecture, model selection, or benchmark behavior requires separate scope consideration and is not an automatic UAT fix.

## 5. Final UAT summary

This is the current package-level summary and must be updated after manual execution. Counts are for the ten scenarios only.

| Measure | Current result |
| --- | --- |
| Total scenarios | **10** |
| Passed | **0** |
| Failed | **0** |
| Not executed | **10** |
| Defects found | **0 logged during preparation; manual findings unknown** |
| Open limitations | **L-01 through L-06 below remain open** |
| Overall recommendation | **Proceed to controlled manual UAT on the Dell. Acceptance and portfolio claims of successful live UAT remain pending.** |

### Open limitations

| ID | Limitation / required follow-up |
| --- | --- |
| L-01 | No manual browser interaction or actual Dell/Ollama response has been observed for this package. Execute all ten cases and attach evidence before sign-off. |
| L-02 | Application-process restart and Dell reboot remain untested manually. The unit test re-enters application lifespan using a temporary database; it does not restart the OS or a deployed process. |
| L-03 | The suite has no dedicated `/submit` intake validation test, and mocked failure/success tests do not establish a real outage-restoration retry on the same ticket. UAT-01, UAT-02, and UAT-09 supply the required manual evidence. |
| L-04 | Provider/model provenance and reviewer identity are not stored in the schema. Record launch settings, model ID, correlated service activity, and the tester externally. Authentication and a provenance-schema change are outside scope. |
| L-05 | This small manual workflow package does not establish production model accuracy, capacity, a response-time service level, security certification, or disaster recovery. The existing 50-ticket benchmark remains a separate evaluation. |
| L-06 | Final decisions are saved once; there is no edit-after-review or re-analysis history. Refreshing the ticket-submission confirmation POST can resubmit a request. Follow the planned navigation and use fresh fixtures for a new review attempt. These scope constraints are not reported here as newly discovered defects. |

### Acceptance decision

| Field | Record |
| --- | --- |
| Business-owner decision | PENDING — not accepted through UAT yet |
| Evidence and outstanding defects reviewed | NOT EXECUTED |
| Accepted limitations / rationale | Pending business-owner decision |
| Name / role / date | NOT SIGNED |

Automated success alone must not change this decision to accepted. When manual execution is complete, reconcile the totals with the scenario register, assess any open defects, and record the authorized acceptance decision.
