# StandIn Skills

<p align="center">
  <a href="https://www.skills.sh/komaa-com/skills"><img src="https://img.shields.io/badge/skills.sh-komaa--com%2Fskills-blue" alt="skills.sh" /></a>
  <a href="https://github.com/komaa-com/standin"><img src="https://img.shields.io/badge/SDK-standin--sdk-success" alt="standin-sdk" /></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License" /></a>
</p>

<p align="center">
  <a href="#install">Install</a> •
  <a href="#skills">Skills</a> •
  <a href="#compatible-agents">Compatible agents</a> •
  <a href="https://github.com/komaa-com/standin">SDK</a> •
  <a href="https://docs.komaa.com">Docs</a>
</p>

---

[Agent Skills](https://agentskills.io) for the StandIn SDK. Give your AI agent a seat in a live Microsoft Teams call. StandIn joins the call. These skills connect the SDK so the agent can talk.

## Install

```bash
# Install all skills
npx skills add komaa-com/skills

# Or install one
npx skills add komaa-com/skills --skill standin-openclaw
```

Skills land in `~/.agents/skills/<skill-name>/` (global) or `./.agents/skills/<skill-name>/` (project-local), with symlinks into each detected agent's skills directory.

## Skills

| Skill | What it teaches the agent |
|---|---|
| [`setup-standin`](./setup-standin) | Get a StandIn connection from the portal, install the SDK, and pick OpenClaw, Hermes, or Autopilot. |
| [`standin-openclaw`](./standin-openclaw) | Load the OpenClaw plugin, merge `openclaw.json`, and bring the realtime voice provider onto a Teams call. |
| [`standin-hermes-agent`](./standin-hermes-agent) | Enable the Hermes Agent plugin, set allowlist and realtime keys, and serve the call listener. |
| [`expose-standin`](./expose-standin) | Publish `/msteams/calling`, probe the mount, and register the agent voice URL in the portal. |

The tunnel commands live in `expose-standin` only. The plugin skills link there instead of inventing a second spelling.

## Compatible agents

Compatible with [Agent Skills](https://agentskills.io) consumers, including
Claude Code, Cursor, GitHub Copilot, Codex, Cline, Goose, Amp, Windsurf,
OpenClaw, and Hermes Agent.

The `skills` CLI auto-detects agents on the machine and installs the symlinks in one shot.

## Requirements

- **OpenClaw** 2026.6.10 or newer, or a **Hermes Agent** install, unless the user turns on StandIn Autopilot and skips a local worker
- **Node.js 20+** for `@komaa/standin-sdk`, or **Python 3.11+** for `standin-sdk`
- A StandIn connection secret from [the portal](https://standin.komaa.com/dashboard)
- A public URL for `/msteams/calling` (see [`expose-standin`](./expose-standin))

`setup-standin` walks the user through the portal and the install. Keep the
connection secret on their machine.

## Check

```bash
python3 check.py
```

Confirms skill names, relative links, secret-handling wording, and that the
OpenClaw plugin id stays `standin-msteams`.

## License

MIT, same as the [StandIn SDK](https://github.com/komaa-com/standin).

## Links

- **SDK source**: <https://github.com/komaa-com/standin>
- **SDK docs**: <https://docs.komaa.com>
- **Portal**: <https://standin.komaa.com>
- **skills.sh page**: <https://www.skills.sh/komaa-com/skills>
- **Agent Skills spec**: <https://agentskills.io/specification>
- **Skills CLI**: <https://github.com/vercel-labs/skills>
