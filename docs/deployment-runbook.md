# Dell deployment and operations runbook

This runbook installs and operates the completed PoC as a systemd service on
the dedicated Ubuntu Server. It changes process supervision and deployment
configuration; the application's workflow, policy, model contract, and database
schema remain unchanged. The service examples have not yet been installed or
validated on the Dell as part of this documentation task.

The target is a Dell OptiPlex 3050 with an Intel Core i3-6100T, 2 physical cores /
4 logical processors, 8 GB RAM, and no dedicated GPU. Qwen3 1.7B runs locally
through the existing Ollama Linux service. See [model selection](model-selection.md)
for the measured benchmark and [UAT results](uat-results.md) for the completed
10/10 manual scenarios. Those results do not establish that this new systemd
deployment has been tested.

## Deployment layout

| Component | Deployment value |
| --- | --- |
| SSH / application account | `farhad` |
| Project directory | `/home/farhad/ai-service-triage-poc` |
| Python interpreter | `/home/farhad/ai-service-triage-poc/.venv/bin/python` |
| Web process | FastAPI served by one Uvicorn worker, without `--reload` |
| Web address | `http://<server-ip>:8000` on the trusted local network |
| SQLite file | `/home/farhad/ai-service-triage-poc/tickets.db` |
| Application service | `/etc/systemd/system/ai-triage.service` |
| Provider configuration | `/etc/ai-triage.env` |
| Ollama service / HTTP endpoint | `ollama.service` / `http://localhost:11434` |

Use synthetic data for this PoC. The web application has no authentication or
HTTPS and should be reachable only by intended users on the trusted network.
Do not configure router port forwarding or expose Ollama to the LAN. Binding
Uvicorn to `0.0.0.0` permits local-network access; clients use the server's actual
address. [Uvicorn settings](https://uvicorn.dev/settings/)

Commands below run in Bash on the Dell unless explicitly stated otherwise.
Replace quoted placeholders such as `'<repository-url>'`, `'<server-ip>'`, and
`'<deployment-branch>'` with the intended values before running them. No
repository URL, password, key, token, or home LAN address is embedded here.
Execute command blocks in order and inspect their output. Stop after a failed
installation, configuration change, or test. Diagnostic `systemctl status`
commands return a nonzero status for an inactive service; that is expected after
a deliberate stop and should be interpreted with the displayed state.

## 1. Connect and prepare the checkout

From the administrator's computer:

```bash
ssh 'farhad@<server-ip>'
```

On the Dell, confirm the account, Python version, and existing services:

```bash
whoami
python3 --version
git --version
systemctl --version
sudo systemctl status ollama --no-pager
```

Use Python 3.10 or newer. If Git, Python/venv, or curl is missing, install the
required Ubuntu packages:

```bash
sudo apt update
sudo apt install git python3 python3-venv curl
```

For a **new checkout only**, run this as `farhad`; do not clone over an existing
project directory:

```bash
git clone '<repository-url>' /home/farhad/ai-service-triage-poc
cd /home/farhad/ai-service-triage-poc
git status --short
git branch --show-current
git rev-parse HEAD
```

Record the branch and commit for the deployment. If the project already exists,
inspect `git status --short` and `git diff` there and use the update procedure
below. Keep local modifications and saved data intact. The service account must
own or have write access to the project directory and `tickets.db`; SQLite also
needs to create journal files beside the database. Do not run the application or
install project packages with `sudo`.

## 2. Create the virtual environment and run the offline suite

Create a Linux virtual environment on the Dell; a Windows `.venv` cannot be
copied over. Skip the creation command if this checkout already has its working
Linux environment.

```bash
cd /home/farhad/ai-service-triage-poc
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
deactivate
```

The baseline is **68 tests passing**. All tests run offline with mocked Ollama
responses; no real-model benchmark is needed for deployment. Workflow tests use
their own temporary database files and leave saved tickets unchanged. Record the
actual Dell test result before continuing. No additional Python dependency is
needed for systemd, Ollama HTTP calls, or SQLite.

## 3. Check the existing Ollama service and model

Ollama already runs as its own Linux service on the Dell. Keep that installation
and service; do not launch a second `ollama serve` process or create another
Ollama unit. If provisioning a replacement server, follow the
[official Linux installation instructions](https://docs.ollama.com/linux).

```bash
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama --no-pager
ollama --version
ollama list
curl --fail --show-error --silent http://localhost:11434/api/tags
```

If `qwen3:1.7b` is missing, download it and list the models again:

```bash
ollama pull qwen3:1.7b
ollama list
```

Model downloads need internet access during provisioning. Inference uses the
local API. Record the Ollama version and model ID printed by `ollama list`;
model tags alone are not a complete version record. Pulling/listing commands
are described in the [Ollama CLI reference](https://docs.ollama.com/cli).

## 4. Install the provider configuration and web service

From the project directory, install the environment file on first deployment:

```bash
cd /home/farhad/ai-service-triage-poc
if sudo test -e /etc/ai-triage.env; then
    sudo cat /etc/ai-triage.env
else
    sudo install -o root -g root -m 0600 deploy/ai-triage.env.example /etc/ai-triage.env
fi
sudoedit /etc/ai-triage.env
```

The intended contents are:

```ini
AI_PROVIDER=ollama
OLLAMA_MODEL=qwen3:1.7b
OLLAMA_TIMEOUT=60
```

The application default remains `AI_PROVIDER=mock` and an Ollama timeout of
120 seconds when those values are omitted. This deployment explicitly selects
Ollama and a 60-second HTTP timeout. The model default is already `qwen3:1.7b`.
The HTTP address is fixed in the provider at `http://localhost:11434/api/chat`;
there is no configurable remote API URL. `localhost` means the Dell running the
web process.

The environment file contains `KEY=value` entries, without shell `export`
commands. systemd reads it before starting the application; shell activation or
a dotenv package is not required. Restart the web service after changes to
this file. Provider changes affect only tickets without a saved assessment.
[systemd execution environment](https://github.com/systemd/systemd/blob/main/man/systemd.exec.xml)

Stop any manually started Uvicorn process using `Ctrl+C` in its terminal before
starting the managed service. Check port 8000 and preserve an existing service
file before replacing it:

```bash
sudo ss -ltnp 'sport = :8000'
if sudo test -e /etc/systemd/system/ai-triage.service; then
    sudo cp -a /etc/systemd/system/ai-triage.service "/etc/systemd/system/ai-triage.service.before-$(date -u +%Y%m%dT%H%M%S%N)"
fi
sudo install -o root -g root -m 0644 deploy/ai-triage.service.example /etc/systemd/system/ai-triage.service
sudo systemd-analyze verify /etc/systemd/system/ai-triage.service
sudo systemctl daemon-reload
sudo systemctl enable ai-triage
sudo systemctl start ai-triage
sudo systemctl status ai-triage --no-pager
sudo journalctl -u ai-triage -n 50 --no-pager
```

Resolve verification errors before enabling/starting. Verify with the installed
`.service` filename rather than the repository's `.service.example` extension.
`enable` schedules startup at boot; `start` starts it now. Neither the venv nor
the environment file is installed automatically by the unit.

The unit runs as `farhad`, uses an explicit venv interpreter and one worker,
and restarts after an application process failure. A deliberate `systemctl stop`
keeps it stopped. Logs go to the journal. `Wants=network-online.target` and
`After=network-online.target` provide boot ordering; they do not continuously
monitor connectivity. The unit has no `Requires=ollama.service` or
`BindsTo=ollama.service`: ticket submission, saved records, and review remain
available when Ollama is down. New analysis attempts report the existing visible
failure. See the [systemd service reference](https://github.com/systemd/systemd/blob/main/man/systemd.service.xml)
and [network-online guidance](https://systemd.io/NETWORK_ONLINE/).

## 5. Verify access and the live workflow

On the Dell:

```bash
curl --fail --show-error --silent http://127.0.0.1:8000/
curl --fail --show-error --silent http://127.0.0.1:8000/tickets
sudo ss -ltnp 'sport = :8000'
sudo ss -ltnp 'sport = :11434'
```

Expect the homepage HTML to include `AI Service Triage PoC` and
`System Status: Running`, the ticket-list page to load, and port 8000 to listen
on `0.0.0.0`. Ollama should remain bound to loopback. The homepage status is a
page rendering check; it does not prove that Ollama or model inference is ready.

From a browser on the intended local-network client, open
`http://<server-ip>:8000/` and `/tickets`. If needed, use a client terminal:

```bash
curl --fail --show-error --silent 'http://<server-ip>:8000/'
```

Submit a new synthetic ticket, record its ID, analyze it, and confirm the five
assessment fields are displayed. Approve it or save a human override, then
confirm both original and final decisions. An already assessed ticket skips
inference, so it is unsuitable for checking the live provider. Use `ollama ps`
and the Ollama journal to help confirm the selected model was used.

If local HTTP works but client access fails, check the address, LAN reachability,
listener, and existing Ubuntu firewall rules (`sudo ufw status verbose`, if UFW
is installed). Where an active firewall blocks the intended client, a scoped
rule can be added by the administrator:

```bash
sudo ufw allow from '<trusted-client-ip>' to any port 8000 proto tcp
```

Replace the placeholder first. Preserve the existing SSH rule and firewall
configuration; do not disable the firewall or enable it remotely without an
established SSH allowance. Port 11434 does not need an inbound LAN rule.

## Routine operation and troubleshooting

| Action | Web application | Existing Ollama service |
| --- | --- | --- |
| Enable at boot | `sudo systemctl enable ai-triage` | `sudo systemctl enable ollama` |
| Start | `sudo systemctl start ai-triage` | `sudo systemctl start ollama` |
| Stop | `sudo systemctl stop ai-triage` | `sudo systemctl stop ollama` |
| Restart | `sudo systemctl restart ai-triage` | `sudo systemctl restart ollama` |
| Status | `sudo systemctl status ai-triage --no-pager` | `sudo systemctl status ollama --no-pager` |
| Recent logs | `sudo journalctl -u ai-triage -n 100 --no-pager` | `sudo journalctl -u ollama -n 100 --no-pager` |
| Follow logs | `sudo journalctl -u ai-triage -f` | `sudo journalctl -u ollama -f` |

Exit following logs with `Ctrl+C`; that stops the log viewer, not the service.
After editing the unit, run `sudo systemctl daemon-reload` and then restart the
web app. After editing only `/etc/ai-triage.env`, restart the web app.
[Ollama Linux service operations](https://docs.ollama.com/linux)

| Symptom | Check / response |
| --- | --- |
| Web service exits immediately | Read its journal; verify `farhad`, project path, venv interpreter, installed requirements, and environment file. Resolve the cause before restarting. |
| Port 8000 already in use | Inspect `ss` output and stop the identified old development server. Avoid running manual and systemd copies together. |
| SQLite cannot open/write the database | Check ownership and write access to the project folder and exact `tickets.db`; check free disk space. Do not delete the database as a troubleshooting step. |
| Visible Ollama unavailable error (HTTP 503) | Check/start `ollama.service`, then check `/api/tags`. The failed ticket has no assessment and may be retried. |
| Missing model or Ollama HTTP error (HTTP 502) | Check the Ollama journal and `ollama list`; provision `qwen3:1.7b` if missing and confirm `/etc/ai-triage.env`. |
| Analysis timeout (HTTP 504) | Check CPU/RAM pressure, concurrent work, model loading, and Ollama logs. The configured 60 seconds is an HTTP timeout, not a guaranteed response-time SLA. Resolve the cause and retry. |
| Invalid model output (HTTP 502) | The existing schema/human-review checks rejected it; no assessment is saved. Record the failure and check installed model/version; do not edit policy or substitute mock output to conceal it. |
| Wrong provider after a configuration change | Inspect `/etc/ai-triage.env` and restart the web service. A saved recommendation remains unchanged by design; test configuration with a new unassessed ticket. |
| Repeated service startup failures | After fixing the logged cause, use `sudo systemctl reset-failed ai-triage` and `sudo systemctl start ai-triage`. |

To verify service recovery during a planned synthetic test, stop Ollama, analyze
a new ticket, and record the visible error and absence of a recommendation.
Confirm the web app still serves tickets and existing reviews. Start Ollama,
check `/api/tags`, then select **Analyze ticket** on that same failed ticket.
It should now save a validated recommendation. There is no silent mock fallback
and no automatic retry. These checks repeat UAT-08/UAT-09 under systemd; retain
the original completed UAT results and record new deployment evidence separately.

## Update after a Git push

Use this procedure only after the intended revision has been reviewed and pushed
to the repository by its owner. This runbook does not perform a commit or push.
Schedule a short maintenance window because updating the single checkout and
virtual environment requires stopping the app.

1. In `/home/farhad/ai-service-triage-poc`, inspect the checkout:

   ```bash
   git status --short
   git diff
   git branch --show-current
   git rev-parse HEAD
   git fetch origin
   git log --oneline HEAD..'origin/<deployment-branch>'
   ```

   Record the old commit, branch, Python/package versions (`.venv/bin/python -m
   pip freeze`), and installed unit/environment settings privately with the
   deployment record. Stop if there are local modifications or unexpected
   commits. Preserve/reconcile them before updating; do not use `reset --hard`,
   `clean`, or a forced checkout. Fast-forward-only updates refuse divergent
   history. [Git pull documentation](https://git-scm.com/docs/git-pull)

2. Make a verified SQLite backup using the procedure below. Stop the app, ensure
   no manually launched copy is running, then update and test:

   ```bash
   sudo systemctl stop ai-triage
   sudo systemctl status ai-triage --no-pager
   git pull --ff-only origin '<deployment-branch>'
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python -m unittest discover -s tests -v
   git rev-parse HEAD
   ```

   An inactive service status is expected during maintenance. Proceed only if
   Git, installation, and all tests succeed. Take the backup after stopping if
   it must include every write immediately preceding the update.

3. Review any changes to `deploy/`. Repository examples do not automatically
   change installed files. If needed, preserve the existing installed files,
   deliberately apply the reviewed settings/unit, verify the unit, and reload
   systemd as in initial deployment. Keep `/etc/ai-triage.env` set to the intended
   provider. This documentation release has no database migration.

4. Start and verify:

   ```bash
   sudo systemctl start ai-triage
   sudo systemctl status ai-triage --no-pager
   sudo journalctl -u ai-triage -n 50 --no-pager
   curl --fail --show-error --silent http://127.0.0.1:8000/tickets
   ```

   Repeat the browser/local-network check, confirm an existing ticket and review
   are intact, and analyze a new synthetic ticket. Record the new commit, test
   result, and any operational issue.

## Rollback guidance

A code rollback should keep `tickets.db` at the same project path and preserve
all submitted tickets and human decisions. This documentation/deployment change
does not require restoring an older database.

Stop the web app and inspect `git status --short` and `git diff` first. If local
work exists, keep it and stop the rollback procedure until it has been preserved
and reconciled. For a clean checkout, use the recorded previous commit:

```bash
cd /home/farhad/ai-service-triage-poc
sudo systemctl stop ai-triage
git status --short
git diff
git switch --detach '<previous-commit>'
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

Detached HEAD leaves the deployment branch and newer commits intact. Return to
that branch with `git switch '<deployment-branch>'` only when ready to redeploy.
Requirements are not a fully pinned environment lock: if a later update changed
packages, use the recorded previous versions to restore them and verify tests;
reinstalling broad requirements alone does not guarantee identical dependencies.
Restore any deliberately changed installed unit/environment from its recorded
backup, then verify/reload systemd if the unit changed. Start the app only after
tests pass and repeat persistence and live-provider checks. Do not force Git to
discard local work or move the application to a second path that would create
another `tickets.db`.

## SQLite backup and restore

The application creates `tickets.db` at the project root on first startup. It
contains `tickets`, `ai_assessments`, and `human_reviews`. Git does not protect
this runtime data. Keep backups outside the checkout and retain an additional
copy on an approved separate device; one copy on the Dell does not cover disk
failure. Keep submitted data and backups out of the public repository.

Use Python's standard-library SQLite backup API for a consistent copy, including
when the app is running. Do not copy only the live database file while writes
are possible. [Python SQLite backup API](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup)

Run as `farhad` from the project directory:

```bash
cd /home/farhad/ai-service-triage-poc
umask 077
.venv/bin/python - <<'PY'
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

source = Path('/home/farhad/ai-service-triage-poc/tickets.db')
backup_dir = Path('/home/farhad/ai-triage-backups')
backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup = backup_dir / f'tickets-{stamp}.db'
with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as src:
    backup.touch(mode=0o600, exist_ok=False)
    with closing(sqlite3.connect(backup)) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise RuntimeError('Backup failed integrity check; do not use it.')
print(f'Verified backup: {backup}')
PY
```

Record the printed path and backup time. A missing source fails instead of
silently creating an empty database. The backup filename is new for each run;
an unsuccessful copy must not be marked as a verified backup.

**Restore only when data recovery is intended.** Restoring an earlier backup
replaces current data with that snapshot and removes records created afterward.
Stop the service and all manual app processes. Make a new verified backup of
the current database first, if it exists. Then select the exact verified backup
to restore; this example never deletes or moves the checkout, venv, or test files:

```bash
sudo systemctl stop ai-triage
sudo systemctl status ai-triage --no-pager
sudo ss -ltnp 'sport = :8000'
cd /home/farhad/ai-service-triage-poc
export TRIAGE_RESTORE_FILE='/home/farhad/ai-triage-backups/<verified-backup-filename>.db'
umask 077
.venv/bin/python - <<'PY'
import os
import sqlite3
from contextlib import closing
from pathlib import Path

source = Path(os.environ['TRIAGE_RESTORE_FILE']).resolve(strict=True)
target = Path('/home/farhad/ai-service-triage-poc/tickets.db')
if source == target:
    raise ValueError('Choose a backup file, not the active database.')
with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as src:
    if src.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
        raise RuntimeError('Backup is invalid; restore stopped.')
    tables = {row[0] for row in src.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )}
    if not {'tickets', 'ai_assessments', 'human_reviews'} <= tables:
        raise RuntimeError('Required PoC tables are missing; restore stopped.')
    with closing(sqlite3.connect(target)) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise RuntimeError('Restore verification failed; keep the app stopped.')
print(f'Restored and verified: {target}')
PY
```

Only after a successful restore, start `ai-triage` and verify representative
ticket IDs, original recommendations, and final decisions from the snapshot.
Retain the pre-restore backup and execution record. Test recovery during a
planned maintenance window before relying on the procedure for an incident.

## Manual Dell validation still required

The existing 68-test suite and 10/10 manual UAT results remain the application
evidence. The following checks are pending for the new systemd deployment;
record their real results without changing completed UAT expected outcomes:

1. Transfer the reviewed revision through Git when the owner is ready; confirm
   the checkout path/account, clean worktree, venv, and 68 passing tests on Ubuntu.
2. Verify the installed Ollama service, its version, and the `qwen3:1.7b` model ID.
3. Install `/etc/ai-triage.env` and `/etc/systemd/system/ai-triage.service`; run
   `systemd-analyze verify`, reload, enable, and start. Confirm the unit has one
   Uvicorn worker and no development reload process.
4. Check status/journals, loopback and LAN HTTP access, and a fresh synthetic
   assessment followed by human approval/override.
5. Restart the web service and confirm the same saved ticket, original
   recommendation, and human review. During a planned server reboot, confirm
   both services start and those records persist. Reboot validation has not
   been claimed by the earlier application-restart UAT result.
6. Stop Ollama deliberately, verify a new failed analysis has a visible error
   and no saved assessment while other pages/reviews work, then start Ollama
   and retry the same ticket successfully.
7. If repeating provider-switch validation, record an existing recommendation,
   temporarily set `AI_PROVIDER=mock`, restart the web app, and confirm it is
   preserved. Restore `AI_PROVIDER=ollama` and restart before finishing.
8. Create and verify a SQLite backup; perform a controlled restore/recovery
   exercise with a retained current snapshot and confirm records. Record the
   deployed commit and configuration alongside the evidence.

These steps remain manual. No remote deployment, service interruption, reboot,
database restore, model download, or real benchmark was executed while creating
this runbook.
