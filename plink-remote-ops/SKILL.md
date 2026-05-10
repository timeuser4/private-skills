---
name: plink-remote-ops
description: Use when the user wants Codex to connect from Windows to a specified remote host through PuTTY plink and perform remote inspection or administration with non-interactive commands. Covers saved PuTTY sessions, explicit SSH targets, key or Pageant auth, host key pinning, and repeatable remote command execution.
---

# Plink Remote Ops

## Overview

Use this skill when work must be performed on a remote host through `plink.exe` from the local Windows machine. It is optimized for one-shot remote commands and repeatable remote workflows, not long-lived interactive terminal sessions.

## When To Use

- The user explicitly asks to use `plink`.
- The task must run on a remote Linux or Unix host reachable by SSH from this machine.
- The remote target is provided as a PuTTY saved session or as `host`, `user`, `port`, and auth details.
- You need repeatable remote inspection, deployment, log collection, service management, or command execution.

## Preconditions

- Verify `plink` is available with `Get-Command plink -ErrorAction SilentlyContinue`, or use the helper script which resolves common PuTTY install paths automatically.
- Prefer a saved PuTTY session, Pageant, or `-i <key.ppk>` over inline passwords.
- If password auth is unavoidable, ask the user to set a temporary local environment variable such as `PLINK_PASSWORD` and use `--password-env PLINK_PASSWORD`. Do not ask the user to paste passwords into chat unless they explicitly choose that risk.
- Ask for missing target details when they cannot be inferred safely:
  - saved session name, or host and username
  - port if not `22`
  - remote shell type, default `bash`
  - key path or other auth method
  - optional host key fingerprint for first-time connections

## Workflow

1. Confirm the target and auth mode.
2. Prefer `scripts/invoke_plink.py` over hand-built `plink` commands because it handles quoting, saved sessions, key auth, host key pinning, and `-batch`.
3. Smoke-test the connection with a narrow command such as `hostname && uname -a && pwd`.
4. Run read-only inspection as small, explicit remote commands.
5. File size strategy for edits:
   - Large files: download to local workspace first, edit locally, then upload back to remote.
   - Small files: direct remote edits are acceptable.
   - Default heuristic: treat files over ~200 lines or ~8 KB as large unless the user specifies otherwise.
6. For any multi-line script, complex quoting, heredoc, JSON/YAML generation, or remote file edits, do not pass the script body directly as `--command`. Encode the script as base64 locally and run a short remote decoder command instead.
7. For remote writes, create backups first, write idempotently, and verify the resulting file contents with a second read-only command.
8. Report the exact remote command intent, the output, and any state changes.

## Remote Development Rules

- Treat PowerShell, Python `argparse`, plink, the remote shell, and the remote program as separate quoting layers. A command that looks like one string in PowerShell can still be split before it reaches `invoke_plink.py`.
- Do not pass PowerShell here-strings, heredocs, multi-line Python, embedded YAML, or nested quotes directly to `--command`. This can make `argparse` report `unrecognized arguments` and may leave the remote task unexecuted.
- When a target file is large, prefer local round-trip editing (`pscp`/download -> local edit -> upload) over inline remote patching.
- Use base64 for complex remote work. Build the script locally, base64 encode it locally, then remotely run `printf '%s' '<base64>' | base64 -d > /tmp/codex_remote_task.sh && bash /tmp/codex_remote_task.sh`.
- Keep the remote decoder command short and single-line. The only complicated content should be inside the base64 payload.
- Prefer writing a temporary remote script under `/tmp` and executing it over trying to inline complicated commands.
- Avoid remote commands with unescaped pipes, regex alternation, command substitutions, redirections, or wildcard-heavy expressions when using shell tools that may split or inspect command segments. If needed, put those operations inside the base64 payload.
- For command output inspection, prefer simple commands such as `sed -n '1,120p' file`, `cat file`, `find dir -maxdepth N -type f`, and separate `grep` calls.
- For long-running services, do not start an interactive process over plink unless the user explicitly asked for it. Use `nohup`, `systemd`, `tmux`, or write a start command to a log file for the user to run manually.
- After remote file edits, verify with `sed`, `grep`, or checksums. Do not assume the edit happened just because the local command was submitted.
- If a local shell command fails before contacting the remote host, state that no remote change occurred unless evidence shows otherwise.
- For remote desktop pop-up requests (GUI apps on the remote Linux desktop), launch commands with the desktop session environment by default:
  - `DISPLAY=:1`
  - `XAUTHORITY=/run/user/1000/gdm/Xauthority`
  - `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus`
  - Add `LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:/lib/aarch64-linux-gnu` when viewer tools depend on system OpenGL/USB libs.
  - Example pattern: `DISPLAY=:1 XAUTHORITY=/run/user/1000/gdm/Xauthority DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus <gui_command>`

## Guardrails

- Do not start a bare interactive session such as `plink user@host` from the shell tool. It can hang waiting for input.
- Default to `-batch` behavior.
- Do not bypass host key verification. If the host key is not already trusted, use a PuTTY saved session or provide `-hostkey`.
- For remote privilege escalation, prefer `sudo -n` so failures are explicit. If the remote host requires an interactive sudo password, stop and ask the user how they want to handle it.
- Keep remote writes scoped and explicit. Confirm destructive actions and target paths before running them.
- Start with read-only inspection if the remote system state is unclear.
- Never use remote destructive operations such as recursive delete, reset, or overwrite without an explicit target check and user approval.
- Do not store passwords in the skill, repo, log files, or remote scripts. Use local environment variables such as `PLINK_PASSWORD`.

## Command Patterns

- Saved session:
  - `python scripts/invoke_plink.py --session my-host --shell bash --command "hostname && uname -a"`
- Explicit host and key:
  - `python scripts/invoke_plink.py --host 192.168.1.50 --user nvidia --key C:\keys\board.ppk --shell bash --command "pwd && ls -la"`
- Explicit host and pinned host key:
  - `python scripts/invoke_plink.py --host 192.168.1.50 --user nvidia --hostkey "ssh-ed25519 255 SHA256:..." --shell bash --command "systemctl status my-service"`
- Password via environment variable:
  - `python scripts/invoke_plink.py --host 192.168.1.50 --user nvidia --password-env PLINK_PASSWORD --shell bash --command "df -h"`
- Complex remote script from PowerShell:
  - Encode locally with `[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script))`.
  - Run remotely with `--command "printf '%s' '<encoded>' | base64 -d > /tmp/codex_remote_task.sh && bash /tmp/codex_remote_task.sh"`.

See [references/usage.md](references/usage.md) for direct `plink` examples, first-use guidance, and troubleshooting patterns.

## Resources

- `scripts/invoke_plink.py`
  - Resolves `plink.exe`
  - Builds safe one-shot remote commands
  - Supports PuTTY saved sessions, explicit hosts, `-i` keys, `-hostkey`, env-based passwords, `bash`, `sh`, or `raw` shells, optional working directory, and optional `sudo -n`
- `references/usage.md`
  - Direct `plink` command patterns
  - Helper script examples
  - First-connection notes and troubleshooting

When the user wants this behavior explicitly, invoke the skill as `$plink-remote-ops`.
