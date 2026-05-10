# Plink Usage

## Preconditions

- `plink.exe` must be installed locally.
- Preferred auth order:
  - PuTTY saved session
  - Pageant
  - `-i <key.ppk>`
  - password from an environment variable
- For first-time connections, prefer a saved PuTTY session or a pinned `-hostkey` fingerprint.

## Quick Checks

```powershell
Get-Command plink -ErrorAction SilentlyContinue
python .codex/skills/plink-remote-ops/scripts/invoke_plink.py --session my-host --command "hostname" --dry-run
```

## Helper Script Examples

Saved session:

```powershell
python .codex/skills/plink-remote-ops/scripts/invoke_plink.py `
  --session my-host `
  --shell bash `
  --command "hostname && uname -a && pwd"
```

Explicit host and key:

```powershell
python .codex/skills/plink-remote-ops/scripts/invoke_plink.py `
  --host 192.168.1.50 `
  --user nvidia `
  --key C:\keys\board.ppk `
  --shell bash `
  --command "ls -la /opt && df -h"
```

Pinned host key:

```powershell
python .codex/skills/plink-remote-ops/scripts/invoke_plink.py `
  --host 192.168.1.50 `
  --user nvidia `
  --hostkey "ssh-ed25519 255 SHA256:..." `
  --shell bash `
  --command "systemctl status docker"
```

Password via environment variable:

```powershell
$env:PLINK_PASSWORD = "example-password"
python .codex/skills/plink-remote-ops/scripts/invoke_plink.py `
  --host 192.168.1.50 `
  --user nvidia `
  --password-env PLINK_PASSWORD `
  --shell bash `
  --command "whoami && id"
Remove-Item Env:PLINK_PASSWORD
```

Remote command with `sudo -n`:

```powershell
python .codex/skills/plink-remote-ops/scripts/invoke_plink.py `
  --session my-host `
  --shell bash `
  --sudo `
  --command "systemctl restart my-service && systemctl status --no-pager my-service"
```

## Complex Remote Scripts

Do not pass multi-line scripts, here-strings, heredocs, YAML/JSON generation, or nested Python directly to `--command`. PowerShell and Python `argparse` can split the payload before it reaches the remote host, producing errors such as `unrecognized arguments`. Use a local base64 payload and a short remote decoder command.

PowerShell template:

```powershell
$env:PLINK_PASSWORD = "example-password"

$script = @'
set -euo pipefail
hostname
date

# Put complex remote work here: heredocs, Python, YAML edits, pipes, redirects.
python3 - <<'PY'
from pathlib import Path
p = Path.home() / "remote_test.txt"
p.write_text("hello from codex\n")
print(p)
PY
'@

$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script))
$remote = "tmp=/tmp/codex_remote_task_`$(date +%s).sh; printf '%s' '$encoded' | base64 -d > `$tmp && bash `$tmp"

python .codex/skills/plink-remote-ops/scripts/invoke_plink.py `
  --host 192.168.1.50 `
  --user nvidia `
  --password-env PLINK_PASSWORD `
  --hostkey "ssh-ed25519 255 SHA256:..." `
  --shell bash `
  --command $remote
```

Verification pass:

```powershell
python .codex/skills/plink-remote-ops/scripts/invoke_plink.py `
  --host 192.168.1.50 `
  --user nvidia `
  --password-env PLINK_PASSWORD `
  --hostkey "ssh-ed25519 255 SHA256:..." `
  --shell bash `
  --command "sed -n '1,40p' ~/remote_test.txt"
```

Use this pattern for remote file edits, config generation, package patching, and any command containing multiple quoting layers.

## Direct plink Patterns

Saved session:

```powershell
plink -batch -load my-host "bash -lc 'hostname && uname -a'"
```

Explicit host and key:

```powershell
plink -batch -ssh -i C:\keys\board.ppk nvidia@192.168.1.50 "bash -lc 'pwd && ls -la'"
```

Pinned host key:

```powershell
plink -batch -ssh -hostkey "ssh-ed25519 255 SHA256:..." nvidia@192.168.1.50 "bash -lc 'journalctl -n 50 --no-pager'"
```

## Notes

- Avoid bare `plink host` interactive sessions when using the shell tool.
- Use `bash -lc` when the remote target is Linux and the command needs shell features.
- Use `--shell raw` only when the remote side should receive the command exactly as written.
- If `sudo -n` fails, the remote host likely requires a password prompt. Stop and ask the user how they want to proceed.
- If the local invocation fails with `invoke_plink.py: error: unrecognized arguments`, the remote command was probably not executed. Fix local quoting first, then rerun.
- Prefer simple read-only inspection commands outside the base64 pattern: `hostname`, `pwd`, `sed`, `cat`, `find`, and narrow `grep`.
- Put pipes, redirections, command substitutions, heredocs, and multi-line edits inside the base64 payload.
- For remote writes, back up target files first and verify with a separate read-only command.
