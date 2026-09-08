# UAT Requirements Traceability

| Document control | Value |
| --- | --- |
| System / package | AI Service Triage PoC / UAT 1.0 |
| Prepared | 2026-09-08 |
| Inspected application baseline | `2bc53ab164f8a021fc22340255b82525894c7e39` |
| Plan / execution record | [UAT plan](uat-plan.md) / [UAT results](uat-results.md) |

## 1. Basis and interpretation

No separate approved business-requirements, functional-requirements, non-functional-requirements, user-story, or acceptance-criteria documents were found in the inspected repository. The IDs in this document are **local traceability references reconstructed from the existing implementation, README, shared business policy, assessment contract, and the user's implemented-workflow requirements**. The user-story phrasing is a restatement of existing capabilities, not a claim that an approved story backlog already existed.

These references introduce no new product scope, numerical performance target, model-selection decision, or acceptance result. The business owner should confirm that the restatements match the intended requirements during UAT review. Source coverage means the requirement can be traced to existing behavior; it does not mean a manual test passed.

### Source register

| Source | Existing material | Relevance |
| --- | --- | --- |
| SRC-01 | [README](../README.md#assessment-and-human-review), including [routes](../README.md#routes), [database](../README.md#database), and [Dell setup](../README.md#run-the-application-with-ollama-on-the-dell) | Documented workflow, persistence, configuration, safe failures, preservation |
| SRC-02 | [main.py](../app/main.py) and existing [templates](../app/templates/ticket_detail.html) / [submission form](../app/templates/index.html) | Form validation, save-before-confirmation, analysis guard, approval/override, error display |
| SRC-03 | [database.py](../app/database.py) | Parameterized queries; separate tickets, assessments, and reviews; uniqueness and persistence |
| SRC-04 | [assessment_schema.py](../app/assessment_schema.py) | Strict, frozen five-field contract; allowed category/priority values |
| SRC-05 | [assessment_policy.txt](../app/assessment_policy.txt) and [assessment_policy.py](../app/assessment_policy.py) | Reusable business-impact rules, category/team guidance, mandatory human review, shared prompt |
| SRC-06 | [ai_service.py](../app/ai_service.py), [config.py](../app/config.py), [ollama_provider.py](../app/ollama_provider.py), [assessment_errors.py](../app/assessment_errors.py) | Provider selection, default mock, local Qwen3, validation before persistence, safe failures without fallback |
| SRC-07 | [test_assessment.py](../tests/test_assessment.py), [test_ollama_provider.py](../tests/test_ollama_provider.py), [test_shared_policy.py](../tests/test_shared_policy.py), [test_workflow.py](../tests/test_workflow.py) | Offline contract, configuration, provider, business-rule, persistence, and workflow evidence |
| SRC-08 | [benchmark.py](../evaluation/benchmark.py), [synthetic dataset](../evaluation/tickets.json), [evaluation tests](../tests/test_evaluation.py), [reporting tests](../tests/test_evaluation_reporting.py) | Separate 50-ticket model evaluation; included in full regression suite but not a manual UAT substitute |

## 2. Existing requirements restated for traceability

### Business requirements

| ID | Restatement | Existing basis |
| --- | --- | --- |
| BR-01 | Capture valid IT service requests and make their saved details retrievable. | SRC-01, SRC-02, SRC-03 |
| BR-02 | Assist triage with a structured local-model recommendation governed by the shared business policy. | SRC-01, SRC-04, SRC-05, SRC-06 |
| BR-03 | Keep the analyst responsible for the final decision, through unchanged approval or an explicit override. | SRC-01, SRC-02, SRC-05 |
| BR-04 | Preserve the original recommendation and the separate final human decision as durable records. | SRC-01, SRC-03 |
| BR-05 | Support recoverable local-provider failures and offline mock operation without disguising failed real requests or replacing saved evidence. | SRC-01, SRC-02, SRC-06 |

### Functional requirements

| ID | Restatement | Existing basis |
| --- | --- | --- |
| FR-01 | Trim title/description; reject either if empty; save valid requests before showing confirmation with a generated ID. | SRC-01; `submit_ticket` in SRC-02; SRC-03 |
| FR-02 | Show saved ticket IDs, titles, and creation times newest first at `/tickets`, and full details at `/tickets/{id}`. | SRC-01, SRC-02, SRC-03 |
| FR-03 | Analyze an unassessed ticket with the configured provider; support real local Ollama at `http://localhost:11434`, default model `qwen3:1.7b`, while retaining mock as the unconfigured default. | SRC-01, SRC-06 |
| FR-04 | Request structured JSON using the existing schema and shared policy, temperature 0 and thinking disabled where supported; validate before saving/displaying; require human review for application recommendations. | SRC-04, SRC-05, SRC-06 |
| FR-05 | Approve unchanged by copying the saved recommendation's category, priority, and team into a separate review. | SRC-01, SRC-02, SRC-03 |
| FR-06 | Let an analyst change category, priority, and team; require allowed category/priority values and a nonblank team; save the final decision separately. | SRC-01, SRC-02, SRC-03 |
| FR-07 | Preserve the original recommendation and first final decision; show both after review, with separate IDs/relationships in storage. | SRC-01, SRC-02, SRC-03 |
| FR-08 | Keep tickets, recommendations, and reviews in the same SQLite database across application/server restart. | SRC-01, SRC-03 |
| FR-09 | Display useful provider failures without saving an assessment or silently substituting mock data. | SRC-01, SRC-02, SRC-06 |
| FR-10 | Keep an unassessed ticket available for retry after provider recovery without resubmitting it. | SRC-01, SRC-02, SRC-06 |
| FR-11 | Skip the provider call when a recommendation already exists; repeated analysis and provider changes cannot regenerate or replace the original. | SRC-01, SRC-02, SRC-03 |

### Non-functional requirements and implementation constraints

These quality references restate implemented constraints. They do not claim that this package performs a complete security, reliability, or performance assessment.

| ID | Restatement | Existing basis |
| --- | --- | --- |
| NFR-01 | Maintain input/output integrity through required-field checks, strict assessment validation, and controlled review choices. | SRC-02, SRC-04, SRC-06 |
| NFR-02 | Preserve committed records and relationships across restart using local SQLite persistence. | SRC-01, SRC-03 |
| NFR-03 | Report real-provider failures safely and permit recovery without corrupting state or hiding failure through fallback. | SRC-02, SRC-06 |
| NFR-04 | Keep original and final records separate and protected against later replacement through ordinary repeated workflow actions. | SRC-02, SRC-03 |
| NFR-05 | Keep inference local, environment-configurable, and compatible with offline mock development through the same assessment contract. | SRC-01, SRC-04, SRC-06 |
| NFR-06 | Retain separated database/provider/policy concerns, parameterized SQL, and a shared application/benchmark policy. | SRC-03, SRC-05, SRC-06, SRC-08 |

NFR-06 is supported by source inspection and automated regression evidence. It is not fully demonstrable through a browser acceptance scenario and has no standalone manual case in this ten-scenario package. Architectural separation and parameterized SQL have not been changed for UAT.

### User stories restated from implemented capabilities

| ID | Restated user story | Requirement links |
| --- | --- | --- |
| US-01 | As a requester, I can submit a valid request and later retrieve it using its ticket ID. | BR-01; FR-01, FR-02 |
| US-02 | As an analyst, I can request a local AI recommendation and inspect its category, priority, summary, routing team, and human-review flag. | BR-02, BR-03; FR-03, FR-04 |
| US-03 | As an analyst, I can approve the recommendation unchanged or save my chosen category, priority, and team. | BR-03; FR-05, FR-06 |
| US-04 | As an analyst reviewing a ticket's history, I can distinguish the original recommendation from the final human decision after override and restart. | BR-04; FR-07, FR-08 |
| US-05 | As an analyst, I can see that a real assessment failed and retry the same request after the service is restored. | BR-05; FR-09, FR-10 |
| US-06 | As a local operator or developer, I can select mock or Ollama without replacing already saved recommendations. | BR-04, BR-05; FR-03, FR-11 |

### Acceptance criteria restated from existing behavior

| ID | Criterion | Manual case |
| --- | --- | --- |
| AC-01 | Given nonblank title/description, submitting saves one ticket before confirmation; its integer ID and details can be retrieved with a creation time. | UAT-01 |
| AC-02 | Given an empty or whitespace-only required field, submission is rejected and no ticket is saved; server validation returns useful feedback. | UAT-02 |
| AC-03 | Given an unassessed ticket and available configured Qwen3 1.7B, Analyze saves one validated, policy-consistent recommendation with all five fields and leaves final human review pending. | UAT-03 |
| AC-04 | Given a recommendation without review, unchanged approval creates a separate final decision copying category, priority, and team exactly. | UAT-04 |
| AC-05 | Given a recommendation without review, an analyst can change all three permitted final fields and save a modified decision. | UAT-05 |
| AC-06 | Given a saved override, every original assessment field and identifier remains unchanged and both records can be inspected independently. | UAT-06 |
| AC-07 | Given committed tickets and reviews, restarting the application and server while retaining the same database preserves all records and relationships. | UAT-07 |
| AC-08 | Given unavailable Ollama and no existing assessment, Analyze displays a useful failure, saves no assessment/review, and does not fall back to mock. | UAT-08 |
| AC-09 | Given the failed, unassessed ticket and restored Ollama, retrying that ticket saves one real assessment without creating another ticket. | UAT-09 |
| AC-10 | Given an existing recommendation, repeated Analyze submissions, including after changing providers, do not call a provider again or alter original/final records. | UAT-10 |

## 3. Scenario-to-requirement matrix

Automated evidence IDs are defined in section 4. They indicate supporting checks, not manual acceptance status. All manual statuses are maintained in the results document and currently remain NOT EXECUTED.

| UAT ID | Business | Functional | Non-functional | User story | Acceptance criterion | Supporting automated evidence | Manual evidence still required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-01 | BR-01 | FR-01, FR-02 | NFR-01, NFR-02 | US-01 | AC-01 | No dedicated intake test; source review only for `/submit` | Actual browser submission, confirmation, listing/detail, and stored row |
| UAT-02 | BR-01 | FR-01 | NFR-01 | US-01 | AC-02 | No dedicated intake validation test; review validation tests cover a different form | Browser-required behavior, all six server pairs, unchanged counts |
| UAT-03 | BR-02, BR-03 | FR-03, FR-04 | NFR-01, NFR-05; NFR-06 supporting only | US-02 | AC-03 | AE-01, AE-02, AE-03, AE-09 | Real Qwen3 call, provider/model provenance, visible fields and factual/policy review |
| UAT-04 | BR-03, BR-04 | FR-05, FR-07 | NFR-01, NFR-04 | US-03, US-04 | AC-04 | AE-04 | Actual analyst click, both visible records, separate stored review |
| UAT-05 | BR-03 | FR-06 | NFR-01, NFR-04 | US-03 | AC-05 | AE-05 | Actual dropdown/team edits, saved values, evidence before and after |
| UAT-06 | BR-04 | FR-07 | NFR-02, NFR-04 | US-04 | AC-06 | AE-05, AE-06 | Complete original-row comparison and both displayed decisions |
| UAT-07 | BR-01, BR-04 | FR-02, FR-07, FR-08 | NFR-02, NFR-04 | US-01, US-04 | AC-07 | AE-06, limited to lifespan re-entry | Real process restart and Dell reboot, same database, complete before/after rows |
| UAT-08 | BR-02, BR-05 | FR-04, FR-09 | NFR-01, NFR-03, NFR-05 | US-05 | AC-08 | AE-02, AE-07 | Service outage, safe browser error, no saved recommendation or review |
| UAT-09 | BR-05 | FR-03, FR-10 | NFR-02, NFR-03 | US-05 | AC-09 | AE-07 and AE-04/AE-05 cover failure and success separately | Restore service and retry the exact failed ticket through the browser |
| UAT-10 | BR-04, BR-05 | FR-03, FR-07, FR-11 | NFR-02, NFR-04, NFR-05 | US-04, US-06 | AC-10 | AE-03, AE-08 | Real/mock provider switches, repeated POSTs, unchanged originals/reviews and no regeneration |

## 4. Supporting automated evidence catalogue

All named methods already exist. Read the exact current run count, outcome, and evidence log in the [results document](uat-results.md#3-supporting-automated-test-evidence). The full suite includes the separate evaluation/reporting tests; not every test is evidence for one of these ten manual scenarios.

| Evidence ID | Existing test location and representative methods | What it supports / limit |
| --- | --- | --- |
| AE-01 | [test_assessment.py](../tests/test_assessment.py), `AssessmentSchemaTests.test_invalid_categories_are_rejected`, `test_invalid_priorities_are_rejected`, `test_all_fields_are_required_and_extra_fields_are_rejected`, `test_summary_and_team_require_nonblank_strings`, `test_review_flag_is_a_strict_boolean`, `test_assessment_cannot_be_modified_after_validation`; `AssessmentServiceTests.test_service_rejects_invalid_provider_output` | Strict contract and service boundary. No actual model response or browser interaction. |
| AE-02 | [test_ollama_provider.py](../tests/test_ollama_provider.py), `OllamaProviderTests.test_request_uses_local_api_shared_policy_and_strict_output_contract`, `test_invalid_assessment_fields_are_rejected_without_exposing_output`, `test_review_flag_cannot_bypass_the_human_review_policy`, `test_incomplete_or_malformed_envelopes_are_rejected`, `test_invalid_json_or_encoding_is_rejected`, `test_unavailable_server_is_reported`, `test_direct_and_wrapped_timeouts_are_reported`, `test_read_timeout_is_reported`, `test_http_errors_are_reported_without_raw_server_messages`, `test_redirects_never_send_requests_to_another_endpoint` | Local request settings, structured response handling, and safe failures using mocked HTTP. No live Dell availability or latency result. |
| AE-03 | [test_ollama_provider.py](../tests/test_ollama_provider.py), `AssessmentConfigurationTests.test_defaults_use_the_mock_provider`, `test_environment_can_select_ollama_and_override_settings`; `ConfiguredAssessmentServiceTests.test_default_mock_works_without_calling_ollama`, `test_ollama_receives_inputs_and_configured_settings`, `test_ollama_failure_never_falls_back_to_mock`, `test_invalid_output_is_rejected_at_the_service_boundary` | Provider selection/default, configured model, no fallback, validation. Does not prove the Dell's actual launch settings. |
| AE-04 | [test_workflow.py](../tests/test_workflow.py), `WorkflowTests.test_approve_copies_original_and_shows_both_records`, `test_ollama_success_preserves_original_through_approval_or_override` | Server copies original values and preserves records through approval. ASGI requests and mock HTTP replace a real browser/model. |
| AE-05 | [test_workflow.py](../tests/test_workflow.py), `WorkflowTests.test_modify_preserves_original_and_survives_restart`, `test_all_allowed_choices_and_unchanged_edit`, `test_review_validation_and_missing_tickets`, `test_ollama_success_preserves_original_through_approval_or_override` | Separate override storage, allowed review choices, immutable originals, escaped output. These do not test intake `/submit` validation. |
| AE-06 | [test_workflow.py](../tests/test_workflow.py), `WorkflowTests.test_modify_preserves_original_and_survives_restart` | Ticket/assessment/review survival when application lifespan is exited and re-entered against the same temporary SQLite file. It is not a process restart, Dell reboot, or backup/restore test. |
| AE-07 | [test_workflow.py](../tests/test_workflow.py), `WorkflowTests.test_ollama_failures_show_errors_without_saving_or_fallback`, `test_invalid_provider_configuration_is_visible` | Safe rendered errors, no assessment saved, Analyze still available, no fallback. Failure cases repeat on an unassessed fixture; a successful recovery on that same ticket is not executed by these methods. |
| AE-08 | [test_workflow.py](../tests/test_workflow.py), `WorkflowTests.test_repeated_actions_keep_first_records`, `test_ollama_success_preserves_original_through_approval_or_override` | Duplicate route/storage protection and explicit assertion that a provider must not be called for an already-assessed ticket. Live service/configuration changes still require UAT-10. |
| AE-09 | [test_shared_policy.py](../tests/test_shared_policy.py), `SharedPolicyTests.test_policy_file_is_unchanged_after_move`, `test_shared_prompt_matches_original_benchmark`; [test_workflow.py](../tests/test_workflow.py), `MockAssessmentTests.test_client_meeting_example_is_network_high`, `test_priorities_follow_business_impact`, `test_higher_impact_overrides_low_priority_signals` | Shared policy/prompt continuity and deterministic mock priority behavior. Does not establish Qwen3's semantic correctness or benchmark accuracy on the Dell. |

## 5. Coverage boundaries and acceptance interpretation

- All ten requested scenarios map to an existing functional requirement, business purpose, restated user story, acceptance criterion, and relevant quality constraint. The matrix does not assert exhaustive coverage of every feature or every possible input.
- UAT-01/02 have a direct manual validation obligation; the 68-test baseline must not be described as containing dedicated ticket-intake tests that are absent from the suite.
- The live schema scenario combines a real browser/provider request with existing automated evidence of strict validation. Raw JSON is not a UI feature, and database snapshots cannot reconstruct the original JSON types or prove model provenance.
- The outage/restoration sequence and two restart phases must be observed in the target environment. Mocked HTTP and application lifespan re-entry are useful supporting checks with narrower scope.
- Shared policy, request settings, schema constraints, and benchmark behavior are retained. No benchmark rerun, target accuracy, or performance threshold is required by this package.
- The schema does not store model/provider provenance or analyst identity. The manual run's configuration, model ID, service logs, and tester record supply context outside the application.
- Final acceptance remains pending until the scenario results and evidence have been reviewed by the business owner. Engineering test success is not business sign-off.
