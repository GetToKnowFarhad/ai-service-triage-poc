# Local model selection

**Decision:** Select **Qwen3 1.7B (`qwen3:1.7b`)** as the production PoC provider on the dedicated Dell server. Gemma 3 1B responded faster, but Qwen was materially more accurate at categorizing, prioritizing, and routing the evaluated IT requests. The application still defaults to `mock` when no provider is configured; the Dell deployment explicitly selects `AI_PROVIDER=ollama`.

## Evaluation context and evidence provenance

The completed comparison used **50 synthetic IT tickets, two models, and 100 total real LLM assessments** on the target server. Both models assessed the same tickets with predefined expected category, priority, and recommended team. No real organizational or customer data was used.

| Target component | Recorded environment |
| --- | --- |
| Server | Dell OptiPlex 3050 |
| Processor | Intel Core i3-6100T |
| CPU topology | 2 physical cores / 4 logical processors |
| Memory | 8 GB RAM |
| Dedicated GPU | None |
| Operating system | Ubuntu Server |
| Local model runtime | Ollama |

The measurements below were supplied by the project owner from the completed Dell benchmark. They are recorded without adjustment; this documentation task did not rerun the benchmark. The underlying per-ticket CSV is not currently included in the repository. The supplied result summary does not specify the execution date, exact command/model order, software versions, model digests, or model loading state. Those details have not been inferred or fabricated.

## Measured comparison

| Metric | Qwen3 1.7B | Gemma 3 1B |
| --- | --- | --- |
| Category accuracy | 88.0% | 74.0% |
| Priority accuracy | 92.0% | 64.0% |
| Routing accuracy | 88.0% | 78.0% |
| Valid structured-output rate | 100.0% | 100.0% |
| Average latency | 8.108 s | 5.138 s |
| Median latency | 7.608 s | 4.632 s |

Gemma's lower latency is useful on this limited hardware. Qwen's stronger task accuracy supports the business objective of giving an analyst a more reliable starting recommendation. The decision favors that accuracy benefit while retaining explicit human review; these latency observations do not establish a response-time service level or concurrent-user capacity.

## Qwen findings

Category accuracy is calculated within each **expected category**, rather than among predictions carrying that label. Ticket counts below come from the existing [synthetic dataset](../evaluation/tickets.json).

| Expected category | Tickets | Qwen category accuracy |
| --- | --- | --- |
| Network | 9 | 100% |
| Hardware | 8 | 50% |
| Software | 9 | 100% |
| Account Access | 8 | 87.5% |
| Security | 8 | 87.5% |
| Other | 8 | 100% |

| Expected priority | Tickets | Qwen priority accuracy |
| --- | --- | --- |
| Low | 10 | 100% |
| Medium | 15 | 73.3% |
| High | 17 | 100% |
| Critical | 8 | 100% |

Hardware classification and Medium-priority decisions remain weaknesses in this sample. The supplied aggregate results do not identify which alternative labels Qwen predicted, so no specific confusion pattern is claimed. The perfect observed High and Critical scores apply only to the 17 and 8 corresponding synthetic tickets.

## Gemma limitations

| Expected group | Tickets | Measured accuracy |
| --- | --- | --- |
| Low priority | 10 | 20% |
| Critical priority | 8 | 0% |
| Security category | 8 | 50% |
| Other category | 8 | 12.5% |

Gemma's results show substantial difficulty applying the priority policy at both ends of the impact range and identifying Security and Other requests. In particular, none of the eight expected Critical cases received the correct priority. The supplied summary does not establish which incorrect priorities were assigned. Faster responses did not offset these task-specific weaknesses for this PoC selection.

## Method and interpretation

The standalone [benchmark](../evaluation/benchmark.py) reads the labeled dataset without accessing application routes or `tickets.db`. Its existing settings and scoring are preserved:

- Requests use the local Ollama chat endpoint at `http://localhost:11434/api/chat`, with one fresh title/description pair per ticket. Expected labels and ticket IDs are not sent to the model.
- Both models use the same [business policy](../app/assessment_policy.txt), category guidance, team mapping, and [shared prompt builder](../app/assessment_policy.py). Critical requires widespread interruption or an obviously severe incident affecting multiple users or services; High covers blocked important work, meaningful time-sensitive impact, or suspicious security events; Medium covers ordinary single-user incidents; Low covers minimal impact without urgency. The source policy remains authoritative.
- Structured output is requested from the existing [AIAssessment schema](../app/assessment_schema.py): `category`, `priority`, `summary`, `recommended_team`, and `requires_human_review`. Responses must pass strict validation with no extra fields. The benchmark does not repair JSON or strip Markdown fences.
- Both models use `temperature: 0`, `seed: 0`, `num_ctx: 4096`, `num_predict: 512`, and `stream: false`. Qwen3 requests include `think: false`; the Gemma3 request omits the thinking option.
- Category, priority, and routing accuracy each use exact, case-sensitive matches divided by **all 50 attempted tickets for that model**. Routing compares the recommended team with the expected team. Invalid output and failed requests receive no accuracy credit. These are three separate scores, not a measured all-fields-correct rate.
- Valid structured-output rate is the number of responses passing `AIAssessment` validation divided by all attempts. **100% valid JSON/schema output does not mean 100% correct business decisions.** Summary factuality is not scored by the label-accuracy metrics. The schema accepts either boolean review flag; the business policy requests `true`, and the application provider additionally rejects `false` before saving. Benchmark scoring has not been changed to match that additional application check.
- Per-category results measure category correctness within the expected-category group. Per-priority results measure priority correctness within the expected-priority group. Incorrect or missing predictions remain in that group's denominator.
- Latency is client elapsed time around the HTTP request and reading its full response, before local scoring. Average and median include received responses, including invalid output, and exclude failed requests such as timeouts or connection errors. Failed-attempt elapsed times are still recorded in CSV.
- The script makes sequential requests with no explicit warmup, automatic retry, or unloading step. A first response may include model loading. Temperature zero does not guarantee identical results across runtime, model, or hardware changes.

The dataset contains 10 Low, 15 Medium, 17 High, and 8 Critical tickets, across all six categories. It includes planned requests, ordinary incidents with workarounds, important work affected by deadlines, suspicious events, and widespread disruption. These are authored expected labels against the reusable policy, rather than targets derived from the mock classifier or model predictions.

## Retaining and extending the evidence

The existing dataset, expected labels, prompts, business policy, and scoring logic were not modified after observing these results. Any future evaluation should retain this baseline and report a separate run; a changed dataset or prompt must not be presented as the same comparison.

To run a future comparison on the Dell, use the environment setup in the [deployment runbook](deployment-runbook.md). From the project directory, with Ollama running:

```bash
ollama pull qwen3:1.7b
ollama pull gemma3:1b
ollama --version
ollama list
.venv/bin/python -m evaluation.benchmark
```

This command performs 100 real inference requests: 50 for Qwen, followed by 50 for Gemma. It is separate from the offline unit-test suite. FastAPI does not need to be running. The benchmark writes a timestamped CSV under `evaluation/results/` and refuses to overwrite existing output. The console includes correct/incorrect totals, group accuracies, and misclassified or failed ticket IDs with expected and predicted values. CSV rows retain predictions, validation and correctness flags, latency, request status, errors, and raw responses.

Retain the real CSV alongside the run date, Git revision, exact command, Ollama version, model IDs, hardware details, server load, and whether models were already loaded. A separately recorded run with reversed model order can help assess loading effects; it must not replace the measured results above. The existing `--models`, `--output`, and `--timeout` options support that process. Model downloads require internet access during setup; inference stays local.

## Decision boundaries

This is a **synthetic 50-ticket PoC evaluation, not a claim of production-grade model accuracy**. Small groups, authored labels, one reported comparison, and missing detailed run metadata limit generalization. The benchmark does not measure sustained load, concurrent requests, analyst productivity, real organizational ticket distributions, or summary factuality.

Qwen's remaining accuracy limitations are recorded separately from the completed [UAT results](uat-results.md): **10 scenarios passed, with no open UAT defects**. UAT establishes the reported submission, review, persistence, and recovery workflows; it does not certify every model prediction as correct. The analyst can approve or override the recommendation, while the original and final human decision remain stored separately. These controls remain essential to the selected deployment.
