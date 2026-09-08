# User Acceptance Test Results

| Document control | Value |
| --- | --- |
| System / package | AI Service Triage PoC / UAT 1.0 |
| Prepared | 2026-09-08 |
| Results revision | 2 — manually executed results recorded from the user's report |
| Manual execution status | **COMPLETE — 10 scenarios reported PASS** |
| Acceptance status | All ten scenario dispositions recorded as PASS; separate named/dated sign-off not supplied |
| Procedures | [UAT plan](uat-plan.md) |
| Requirements | [UAT traceability](uat-traceability.md) |

The user reports that all ten scenarios were manually executed on the Dell Ubuntu server using the live application and Qwen3 1.7B through Ollama, with a deliberate switch to mock for UAT-10. The observations and PASS dispositions below are recorded from that manual execution report. They are not claims that the documentation editor independently operated the Dell or inspected screenshots.

The original [plan](uat-plan.md), requirements, acceptance criteria, and expected-outcome column remain unchanged. Its initial result placeholders represent the pre-execution baseline; this register is the authoritative current result record. The supplied observations do not enumerate every original subcheck. Execution differences and evidence limitations are retained explicitly below without inventing additional results or changing the user's final scenario dispositions. Model-accuracy limitations remain separate from UAT defects.

## 1. Manual run record

The following environment details are taken from the user's report. Unprovided metadata remains identified as such; the original document preparation date is not the manual execution date.

| Field | Actual value |
| --- | --- |
| Run ID | Not supplied; `manual-dell-uat` is a documentation evidence-folder label, not an asserted execution ID |
| Tester / analyst | Manual results supplied by the user; tester name not supplied |
| Business owner / acceptance authority | Separate identity and formal signature not supplied |
| Environment operator | Service and application operations reported by the user; operator name not supplied |
| Start / finish, with time zone | Execution completed; dates, times, and time zone not supplied |
| Dell host identifier and OS/version | Dell Ubuntu server; hostname and Ubuntu version not supplied |
| CPU / RAM / GPU, if present | Not supplied |
| Project directory / absolute `tickets.db` path | Not supplied |
| Git revision / working-tree changes on Dell | Not supplied; do not substitute the development test revision |
| Python / browser versions | Not supplied for the Dell run |
| Ollama version / `qwen3:1.7b` model ID | Qwen3 1.7B through live Ollama confirmed by the user; Ollama version and model digest not supplied |
| Actual `AI_PROVIDER`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT` | Provider `ollama`, then `mock` for UAT-10; Qwen3 1.7B used for real assessments. Exact model environment value and timeout not supplied |
| Ollama start/stop controls | Ollama stopped for UAT-08 and restarted for UAT-09; exact commands not supplied |
| Evidence directory | Placeholder: `docs/evidence/manual-dell-uat/`; screenshot files are not present in the repository |
| End-state configuration and service readiness | Last reported application state: `AI_PROVIDER=mock` after application restart for UAT-10. Ollama was restored for UAT-09; no later readiness check or return to the Ollama provider was reported |

### Fixture ledger

| Reported ticket | Detail URL | Assessment ID | Review ID | Observed use |
| --- | --- | --- | --- | --- |
| Ticket #3 | `/tickets/3` | Not supplied; original recommendation reported preserved | Not supplied; override reported saved | UAT-01, UAT-05, UAT-06: exact submitted title/description persisted; original Network / Medium / Network Support; final Hardware / Medium / Hardware Support |
| Ticket #4 | `/tickets/4` | Not supplied; recommendation reported saved | Not supplied; unchanged approval reported saved | UAT-04, UAT-07: AI and human values matched and all three records survived application restart |
| Ticket #5 | `/tickets/5` | Not supplied; absent after failure, created on retry | Review state not supplied | UAT-08, UAT-09, UAT-10: failed real request, successful Security / High / IT Security retry, preserved after switching to mock |

These are actual ticket IDs from the report. They are not retroactively assigned the plan's A/B/C/D fixtures or their invented input text. The literal titles/descriptions, internal row IDs, and UAT-03-specific ticket ID were not supplied. Exact title/description matching for Ticket #3 is the user's reported observation; no text has been reconstructed.

## 2. Scenario results register

Objectives, preconditions, planned data, exact steps, expected results, and requirement references remain in each linked plan case. The expected-outcome column below is preserved verbatim from the pre-execution register. The actual-result column records only supplied observations. Every screenshot filename is a descriptive **placeholder**, relative to `docs/evidence/manual-dell-uat/`; no image file is claimed to exist or to have been reviewed.

| UAT ID / procedure | Expected outcome | Actual result | PASS / FAIL / NOT EXECUTED | Evidence / screenshot reference | Notes |
| --- | --- | --- | --- | --- | --- |
| [UAT-01](uat-plan.md#uat-01--submit-a-valid-service-request) | Valid request saved once; generated ID, fields, list entry, and detail page available | Valid submission created and persisted Ticket #3 with the exact submitted title and description. | **PASS** | Placeholder: `UAT-01-ticket-3-submission.png` | User-reported manual result; literal input text and individual list/detail observations not supplied |
| [UAT-02](uat-plan.md#uat-02--reject-empty-and-whitespace-only-fields) | Browser and server reject required-field failures; no row saved | Whitespace-only title/description was rejected with a visible validation message, and no ticket was created. | **PASS** | Placeholder: `UAT-02-whitespace-validation-no-ticket.png` | Individual empty-input/browser subchecks and observed HTTP status not enumerated in the report |
| [UAT-03](uat-plan.md#uat-03--generate-a-structured-recommendation-with-qwen3-17b) | Real Qwen3 produces a validated, policy-consistent five-field recommendation; human review pending | Live Qwen3 1.7B generated a valid structured assessment through Ollama in the application. | **PASS** | Placeholder: `UAT-03-qwen3-structured-assessment.png` | Ticket ID, full field values, raw response, model digest, and request logs not supplied for this case |
| [UAT-04](uat-plan.md#uat-04--approve-the-recommendation-unchanged) | Approval copies original values into a separate review | Analyst approved Ticket #4 unchanged; the AI recommendation and final human decision matched. | **PASS** | Placeholder: `UAT-04-ticket-4-approved-unchanged.png` | Exact matching values and internal record IDs not supplied |
| [UAT-05](uat-plan.md#uat-05--modify-category-priority-and-team) | All three analyst edits are saved as a modified final decision | Ticket #3 changed from Network / Medium / Network Support to Hardware / Medium / Hardware Support. | **PASS** | Placeholder: `UAT-05-ticket-3-human-override.png` | Category and team changed; priority remained Medium. The report does not demonstrate a priority change; the original three-field expectation is retained |
| [UAT-06](uat-plan.md#uat-06--preserve-the-original-after-human-override) | Every original field, ID, and timestamp is unchanged; review is separately linked | Ticket #3 preserved its original Network / Medium / Network Support AI recommendation after the human override. | **PASS** | Placeholder: `UAT-06-ticket-3-original-and-final.png` | Full before/after row snapshots, IDs, timestamps, summary, and flag values not supplied |
| [UAT-07](uat-plan.md#uat-07--persist-tickets-and-reviews-after-restart) | A/B records survive application restart and Dell reboot unchanged | Ticket #4, its AI recommendation, and its human review persisted after application restart. | **PASS** | Placeholder: `UAT-07-ticket-4-after-application-restart.png` | Application restart is confirmed by the report; an Ubuntu/Dell OS reboot or second reviewed ticket is not specifically reported |
| [UAT-08](uat-plan.md#uat-08--report-unavailable-ollama-without-saving-a-recommendation) | Useful HTTP 503 error; C retained; no recommendation/review or fallback | With Ollama stopped, Ticket #5 displayed a visible unavailable-service error, showed no recommendation, and saved no assessment. | **PASS** | Placeholder: `UAT-08-ticket-5-ollama-unavailable.png` | No mock result substituted in the reported failure; exact observed HTTP code and database snapshot not supplied |
| [UAT-09](uat-plan.md#uat-09--retry-the-same-ticket-after-ollama-is-restored) | Restored real provider assesses the same C once; ticket unchanged and review pending | After restarting Ollama, the same Ticket #5 successfully retried and generated Security / High / IT Security. | **PASS** | Placeholder: `UAT-09-ticket-5-successful-security-retry.png` | Actual execution used Ticket #5; do not replace the plan's fixture C text or expected labels with this result |
| [UAT-10](uat-plan.md#uat-10--preserve-saved-recommendations-across-repeats-and-provider-changes) | Repeated requests and provider switches preserve real and mock originals and existing review | After switching the configured provider from Ollama to mock and restarting the application, Ticket #5 retained Security / High / IT Security and was not regenerated or overwritten. | **PASS** | Placeholder: `UAT-10-ticket-5-preserved-after-mock-switch.png` | Report confirms Ollama-to-mock preservation; reverse switching, stale POST replay, and a fresh mock control are not specifically reported |

### Execution coverage and evidence notes

The user's final PASS disposition is recorded for each of the ten scenarios. The plan's stricter subcase completion rules and expected outcomes have not been rewritten. The notes below distinguish what the supplied report establishes from details it does not establish; they are documentation/coverage limitations, not newly observed failures or additional scenarios. An unreported subcheck must not be represented as a separately verified PASS.

| Scenario / planned coverage | Supplied execution evidence | Limit of the current record |
| --- | --- | --- |
| UAT-02 / browser check and six invalid-input pairs | Whitespace-only title/description rejected visibly, no ticket created | Pair-by-pair empty/whitespace outcomes and browser-vs-server checks not supplied |
| UAT-03 / fixture-specific interpretation and full structured response | Valid structured assessment from live Qwen3 1.7B through Ollama | No fixture ID or exact response supplied; do not claim that the plan's specific classification was observed |
| UAT-05 / change all three fields | Category and team changed on Ticket #3; Medium priority retained | Priority-edit subcheck is not demonstrated by the supplied values |
| UAT-06 / every column, identity, and timestamp | Original recommendation reported preserved on Ticket #3 | No complete stored-row comparison supplied |
| UAT-07 / application restart and Dell reboot for two reviewed tickets | Ticket #4 and both associated records persisted after application restart | OS reboot and the second reviewed-ticket comparison not specifically reported |
| UAT-08 / failure HTTP code and storage evidence | Unavailable-service error, no recommendation, no assessment on Ticket #5 | No observed HTTP status, service log, or read-only snapshot attached |
| UAT-09 / planned fixture C and same-ticket retry | Failed Ticket #5 successfully retried with Security / High / IT Security | Literal input was not supplied, so correspondence to the plan's fixture C cannot be established; its expected labels remain unchanged |
| UAT-10 / repeated POSTs, both switch directions, unavailable-service checks, restored end state | Existing Ticket #5 result preserved after Ollama-to-mock switch and application restart | Reverse switch, explicit replay/no-call observation, fresh mock control, and restoration to Ollama not specifically reported |

Attach the descriptive screenshot files when available. Read-only database snapshots and service logs may supplement them where available; screenshots alone do not prove all row counts, timestamps, JSON types, or absence of a provider call. The current actual results rely on the user's reported observations rather than an independent review of those artifacts.

### Results history and future retests

The initial package recorded all ten scenarios as not yet executed. This revision records the subsequently supplied manual results: all ten PASS, with no reported failed attempt or UAT defect. The original plan and prior automated log are retained. No earlier manual failure has been erased or converted into a pass.

For any future attempt, append its run/UAT ID, tester, date/time/time zone, actual input and ticket IDs, step observations, unchanged expected outcome, disposition, evidence references, defect links, and execution notes. Retain prior observations rather than overwrite the history. No new attempt is implied by this instruction.

## 3. Supporting automated test evidence

The original package's [68-test passing log](evidence/unit-tests.txt) is retained as historical supporting evidence. After updating the manual results and traceability, the full suite was rerun and all 68 tests passed. Automated tests remain separate from the user-reported live UAT results.

| Item | Result |
| --- | --- |
| Command | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` |
| Current run status | **PASS — exit code 0; full suite completed after the documentation update** |
| Run time (UTC) | 2026-09-08 03:57:34–03:57:35; exact timestamps in the log, independent of the unprovided manual UAT execution date |
| Test count / failures / errors / skipped | **68 / 0 / 0 / 0** |
| Environment | Windows development workspace; Python 3.13.0; offline mocked HTTP and temporary test databases |
| Detailed evidence | [Post-update full unit-test output and execution metadata](evidence/unit-tests-after-manual-uat.txt); the prior log is preserved |
| Dell/Ollama calls | None required by this suite; live UAT remains separate |

The [traceability matrix](uat-traceability.md#3-scenario-to-requirement-matrix) identifies relevant test methods and evidence limitations. The unit total counts discovered test methods, not each `subTest` input or each mocked model request. It is not the UAT scenario count.

## 4. Defect and retest register

The user reports no UAT failures or open UAT defects across the ten completed scenarios. **Open UAT defects: 0.** Evidence/coverage limitations and previously measured model-accuracy limitations are tracked separately below; they are not reclassified as UAT failures. This record does not claim the system is free of every possible defect outside the reported acceptance scenarios.

| Defect ID | UAT ID / failed step | Observed vs expected / reproduction | Impact and severity | Evidence | Owner / status | Retest run / result |
| --- | --- | --- | --- | --- | --- | --- |
| None logged | Not applicable | No UAT defect reported in the manual results | Not applicable | User's execution report; screenshot placeholders above | 0 open UAT defects | No defect retest required by the reported results |

For observed defects, use IDs such as `UAT-DEF-001`. Classify impact as blocking acceptance, materially impairing a scenario, or minor presentation/usability; record the reason. Any proposed change to policy, schema, architecture, model selection, or benchmark behavior requires separate scope consideration and is not an automatic UAT fix.

## 5. Final UAT summary

These final totals reflect the user's ten manual scenario dispositions. Evidence notes and unenumerated planned subchecks are not additional scenarios and do not change these totals.

| Measure | Current result |
| --- | --- |
| Total scenarios | **10** |
| Passed | **10** |
| Failed | **0** |
| Not executed | **0** |
| Defects found | **0 UAT defects reported** |
| Open UAT defects | **0** |
| Open limitations | Evidence/coverage and PoC/model limitations recorded separately as L-01 through L-06 |
| Overall recommendation | **Accept the demonstrated PoC workflow on the basis of the user's reported 10/10 manual PASS results. Complete the evidence archive and retain the stated coverage/model limitations; this is not a production-readiness or model-accuracy certification.** |

### Open limitations

| ID | Limitation / required follow-up |
| --- | --- |
| L-01 | Screenshot files, raw responses, database snapshots, execution times, and detailed environment metadata were not supplied. Filenames are placeholders; the recorded observations are attributed to the user. Attach existing artifacts when available without inventing evidence. |
| L-02 | The original plan includes broader subchecks than the supplied observations enumerate: notably a changed priority, a Dell OS reboot, and repeated/reverse provider-switch checks. See the execution coverage table. Requirements and expected outcomes remain unchanged; the report does not independently establish every planned subcheck. |
| L-03 | The automated suite still has no dedicated `/submit` intake test or complete real-service outage/recovery sequence. Manual UAT-01/02 and UAT-08/09 now provide user-reported live observations; offline tests remain supporting evidence with their existing scope. |
| L-04 | Provider/model provenance and reviewer identity are not stored in the schema. Exact model digest, tester identity, and signed/date-stamped acceptance were not supplied externally. These are evidence and PoC scope limits, not observed workflow defects. |
| L-05 | Previously measured model-accuracy limitations remain model-evaluation limitations, **not UAT failures or open UAT defects**. No accuracy figures or benchmark outcomes are changed by this update. Workflow acceptance does not establish production accuracy, capacity, a response-time service level, security certification, or disaster recovery; analyst review remains necessary. |
| L-06 | Existing PoC scope constraints remain: final decisions are saved once, there is no edit-after-review/re-analysis history, and refreshing the submission confirmation POST can resubmit a request. None was reported as a defect in this manual UAT run. |

### Acceptance decision

| Field | Record |
| --- | --- |
| Scenario acceptance disposition | User-reported manual UAT complete: all ten scenarios PASS |
| Formal business-owner sign-off | Separate named/dated approval not supplied; no signature is invented |
| Evidence and outstanding defects reviewed | User's manual-result report recorded; 0 open UAT defects reported. Screenshot artifacts have not been supplied for independent review |
| Limitations / rationale | Recorded separately above; successful workflow UAT does not remove model-accuracy or evidence-coverage limitations |
| Name / role / date | Not supplied |

The ten PASS dispositions come from the user's live manual execution report, not from the automated suite. Portfolio reporting should identify that source, retain the unchanged planned expectations and execution notes, and add descriptive screenshot evidence and any formal sign-off when available.
