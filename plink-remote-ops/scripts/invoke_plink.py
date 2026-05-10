#!/usr/bin/env python3
"""
Run non-interactive remote commands through PuTTY plink.

Examples:
  python scripts/invoke_plink.py --session my-linux --shell bash --command "hostname && uname -a"
  python scripts/invoke_plink.py --host 192.168.1.50 --user nvidia --key C:\\keys\\board.ppk --shell bash --command "pwd && ls -la"
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_plink(explicit_path: str | None) -> str:
    if explicit_path:
        candidate = Path(explicit_path).expanduser()
        if candidate.is_file():
            return str(candidate)
        raise FileNotFoundError(f"plink not found at {candidate}")

    found = shutil.which("plink") or shutil.which("plink.exe")
    if found:
        return found

    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "PuTTY" / "plink.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "PuTTY" / "plink.exe",
        Path(os.environ.get("LocalAppData", r"")) / "Programs" / "PuTTY" / "plink.exe",
        Path(os.environ.get("USERPROFILE", r"")) / "scoop" / "apps" / "putty" / "current" / "plink.exe",
        Path(r"C:\ProgramData\chocolatey\bin\plink.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    raise FileNotFoundError(
        "plink.exe was not found in PATH or common PuTTY install locations."
    )


def build_remote_command(shell_name: str, command: str, cwd: str | None, sudo: bool) -> str:
    if shell_name == "raw":
        if cwd:
            raise ValueError("--cwd is not supported with --shell raw")
        if sudo:
            raise ValueError("--sudo is not supported with --shell raw")
        return command

    inner_command = command
    if cwd:
        inner_command = f"cd {shlex.quote(cwd)} && {inner_command}"
    if sudo:
        inner_command = f"sudo -n {shell_name} -lc {shlex.quote(inner_command)}"

    return f"{shell_name} -lc {shlex.quote(inner_command)}"


def build_plink_args(args: argparse.Namespace) -> list[str]:
    plink = resolve_plink(args.plink)

    if bool(args.session) == bool(args.host):
        raise ValueError("Specify exactly one of --session or --host")

    plink_args = [plink, "-batch"]

    if args.hostkey:
        plink_args.extend(["-hostkey", args.hostkey])

    if args.key:
        key_path = Path(args.key).expanduser()
        if not key_path.is_file():
            raise FileNotFoundError(f"PPK key not found: {key_path}")
        plink_args.extend(["-i", str(key_path)])

    if args.password_env:
        password = os.environ.get(args.password_env)
        if password is None:
            raise ValueError(
                f"Environment variable {args.password_env} is not set"
            )
        plink_args.extend(["-pw", password])

    if args.session:
        plink_args.extend(["-load", args.session])
    else:
        plink_args.append("-ssh")
        if args.port:
            plink_args.extend(["-P", str(args.port)])
        target = args.host
        if args.user:
            target = f"{args.user}@{target}"
        plink_args.append(target)

    remote_command = build_remote_command(
        shell_name=args.shell,
        command=args.command,
        cwd=args.cwd,
        sudo=args.sudo,
    )
    plink_args.append(remote_command)
    return plink_args


def mask_args(argv: list[str]) -> list[str]:
    masked: list[str] = []
    hide_next = False
    for item in argv:
        if hide_next:
            masked.append("******")
            hide_next = False
            continue
        masked.append(item)
        if item == "-pw":
            hide_next = True
    return masked


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a non-interactive remote command through PuTTY plink.",
    )
    parser.add_argument("--plink", help="Explicit path to plink.exe")
    parser.add_argument("--session", help="PuTTY saved session name")
    parser.add_argument("--host", help="SSH host or IP address")
    parser.add_argument("--user", help="SSH username for explicit host mode")
    parser.add_argument("--port", type=int, default=22, help="SSH port")
    parser.add_argument("--key", help="Path to a PuTTY .ppk key")
    parser.add_argument("--hostkey", help="Pinned SSH host key fingerprint")
    parser.add_argument(
        "--password-env",
        help="Environment variable name that contains the SSH password",
    )
    parser.add_argument(
        "--shell",
        choices=("bash", "sh", "raw"),
        default="bash",
        help="Remote shell wrapper. Use raw to send the command verbatim.",
    )
    parser.add_argument("--cwd", help="Remote working directory for bash/sh mode")
    parser.add_argument(
        "--sudo",
        action="store_true",
        help="Wrap the remote command with sudo -n",
    )
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print the local plink command before execution",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command and exit without executing it",
    )
    parser.add_argument(
        "--command",
        required=True,
        help="Remote command to execute",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plink_args = build_plink_args(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.print_command or args.dry_run:
        print(" ".join(shlex.quote(part) for part in mask_args(plink_args)))

    if args.dry_run:
        return 0

    completed = subprocess.run(
        plink_args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
