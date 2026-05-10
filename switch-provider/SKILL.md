# switch-provider

Switch the Codex `config.toml` and `auth.json` to use different model providers (e.g., OpenAI, local proxies, third-party gateways).

## When to Use

- The user asks to switch model providers, API endpoints, or API keys.
- The user mentions `/switch_url` or wants to point Codex at a different `base_url`.
- The user wants to see available provider templates.

## How to Use

### List Available Providers

```bash
python3 ~/.codex/skills/switch-provider/scripts/switch_provider.py --list
```

Output shows current active provider and all available templates in `~/.codex/configs/`.

### Switch to a Provider

```bash
python3 ~/.codex/skills/switch-provider/scripts/switch_provider.py --switch <template_name>
```

This overwrites `~/.codex/config.toml` and `~/.codex/auth.json` with the template files. Requires sandbox escalation for writing.

### Add a New Provider Template

```bash
python3 ~/.codex/skills/switch-provider/scripts/switch_provider.py --add <name> --config <config_content> [--auth <auth_content>]
```

### Create a Template Manually

Create a directory `~/.codex/configs/<name>/` with:

- `config.toml` — provider configuration (model_provider, base_url, etc.)
- `auth.json` (optional) — API key mapping

## Directory Structure

```
~/.codex/configs/<template_name>/
├── config.toml      # Provider config template
└── auth.json        # Auth template (optional)
```

## Safety Notes

- Switching providers **replaces** `~/.codex/config.toml` and `~/.codex/auth.json`.
- Always ask the user before switching if the target provider is unclear.
- The script requires escalation to write to `~/.codex/`.
