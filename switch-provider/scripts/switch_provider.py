#!/usr/bin/env python3
"""Switch Codex config by applying a template from ~/.codex/configs/<name>/."""
import argparse, os, sys, re

CONFIG_DIR  = os.path.expanduser("~/.codex/configs")
TARGET_TOML = os.path.expanduser("~/.codex/config.toml")
TARGET_AUTH = os.path.expanduser("~/.codex/auth.json")

def read(path):
    with open(path) as f:
        return f.read()

def write(path, content):
    with open(path, "w") as f:
        f.write(content)

def extract_projects_section(content):
    projects = []
    pat = r'(\[projects\."[^"]*"\]\s*\n(?:(?!\n\[).)*)'
    for m in re.finditer(pat, content, re.S):
        projects.append(m.group(1).rstrip('\n'))
    return projects

def list_configs():
    if not os.path.isdir(CONFIG_DIR):
        print("No configs directory found.")
        return []
    names = []
    for entry in sorted(os.listdir(CONFIG_DIR)):
        path = os.path.join(CONFIG_DIR, entry)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "config.toml")):
            names.append(entry)
    return names

def get_current_info(content):
    m1 = re.search(r'^model_provider\s*=\s*"([^"]+)"', content, re.M)
    m2 = re.search(r'^model\s*=\s*"([^"]+)"', content, re.M)
    return m1.group(1) if m1 else "unknown", m2.group(1) if m2 else "unknown"

def do_list():
    names = list_configs()
    if not names:
        print("No config templates found in ~/.codex/configs/")
        return
    try:
        cur_provider, cur_model = get_current_info(read(TARGET_TOML))
    except Exception:
        cur_provider = cur_model = "unknown"
    print(f"\nCurrent: provider={cur_provider}, model={cur_model}\n")
    print("Available templates:")
    for name in names:
        tpl_path = os.path.join(CONFIG_DIR, name, "config.toml")
        tpl_content = read(tpl_path)
        p, m = get_current_info(tpl_content)
        has_auth = os.path.exists(os.path.join(CONFIG_DIR, name, "auth.json"))
        marker = " <-- ACTIVE" if p == cur_provider else ""
        auth_info = " (auth.json included)" if has_auth else ""
        print(f"  {name}: provider={p}, model={m}{marker}{auth_info}")
    print()

def do_switch(name):
    tpl_dir = os.path.join(CONFIG_DIR, name)
    tpl_toml = os.path.join(tpl_dir, "config.toml")
    tpl_auth = os.path.join(tpl_dir, "auth.json")
    if not os.path.isdir(tpl_dir):
        avail = list_configs()
        print(f"Error: Template '{name}' not found.")
        if avail:
            print(f"Available: {', '.join(avail)}")
        sys.exit(1)
    if not os.path.exists(tpl_toml):
        print(f"Error: {tpl_toml} not found.")
        sys.exit(1)
    try:
        current_content = read(TARGET_TOML)
        projects = extract_projects_section(current_content)
    except FileNotFoundError:
        projects = []
    tpl_content = read(tpl_toml)
    tpl_content = re.sub(r'\n?\[projects\."[^"]*"\]\s*\n(?:(?!\n\[).)*', '', tpl_content, flags=re.S)
    if projects:
        tpl_content = tpl_content.rstrip('\n') + '\n\n' + '\n\n'.join(projects) + '\n'
    write(TARGET_TOML, tpl_content)
    print(f"Switched config.toml to template '{name}'")
    if os.path.exists(tpl_auth):
        auth_content = read(tpl_auth)
        write(TARGET_AUTH, auth_content)
        print(f"Switched auth.json to template '{name}'")
    p, m = get_current_info(tpl_content)
    print(f"Active: provider={p}, model={m}")

def main():
    p = argparse.ArgumentParser(description="Switch Codex config template")
    p.add_argument("--list", action="store_true", help="List available templates")
    p.add_argument("--switch", metavar="NAME", help="Switch to a template by name")
    args = p.parse_args()
    if args.list:
        do_list()
    elif args.switch:
        do_switch(args.switch)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
