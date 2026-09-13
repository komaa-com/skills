---
name: setup-standin
description: >
  Install the StandIn SDK and create a Microsoft Teams connection in the
  StandIn portal. Use when the user wants StandIn, Microsoft Teams calling,
  standin-sdk, @komaa/standin-sdk, a connection secret, OpenClaw on Teams,
  Hermes on Teams, or StandIn Autopilot, even if they do not say "setup".
license: MIT
compatibility: >
  Requires a StandIn account. OpenClaw needs Node.js 20+ and OpenClaw
  2026.6.10+. Hermes needs Python 3.11+ and a Hermes Agent install.
  Autopilot needs no local SDK.
metadata:
  author: standin
  version: "0.1.0"
---

# Set up StandIn

Give the user's agent a seat in a live Microsoft Teams call. StandIn joins
the call. This skill gets the connection and the SDK in place. The plugin
skills wire the agent afterwards.

## Workflow

### Step 1: Pick the path

Ask which runtime they want. Do not install both.

| Path | When | Next skill |
|---|---|---|
| **OpenClaw** (TypeScript) | They already run an OpenClaw gateway | [`standin-openclaw`](../standin-openclaw/) |
| **Hermes Agent** (Python) | They already run Hermes | [`standin-hermes-agent`](../standin-hermes-agent/) |
| **StandIn Autopilot** | They do not want to run a gateway | Stop here. Turn Autopilot on in the portal. |

If they are unsure, default to whichever language the rest of the project is
in. Autopilot is the right answer only when they say they do not want to
operate a worker.

Install the SDK and connect. In the
[portal](https://standin.komaa.com/dashboard) you choose a plan, set how
long the teammate can talk, and turn on a knowledge base when you want
it to answer from your docs.

### Step 2: Create the connection in the portal

StandIn gives you the connection secret in the portal.

1. Open <https://standin.komaa.com/dashboard>
2. Add **StandIn** from the Microsoft Teams Store (Managed Bot), or use their
   own Azure bot if they already have one. Managed Bot is the default.
3. Create or open the identity. The portal shows the **connection secret
   once**, on the completion screen.
4. Have them save it locally: `export STANDIN_SECRET=...` in their own
   terminal, a secret manager, or the gateway config on disk. Keep it off
   this chat, off git, and out of logs.

`secret` / `STANDIN_SECRET` must be a **plain string**. An object or an
unresolved reference becomes an empty secret, and the listener never starts.

They will also register an **agent calling URL** after the listener is
exposed. That step belongs to [`expose-standin`](../expose-standin/). Do not
invent a URL here.

### Step 3: Install the SDK next to the host

Install where the gateway or Hermes process can import the package.

**OpenClaw:**

```bash
npm install @komaa/standin-sdk
```

Needs OpenClaw 2026.6.10 or newer. `openclaw` is an optional peer: the plugin
runs inside the gateway and uses the host's realtime session, provider
registry, and logger.

**Hermes:**

```bash
pip install "standin-sdk[hermes-agent]"
```

Install into the same Python environment that runs Hermes. Hermes is not on
PyPI. It is the application the plugin loads into.

### Step 4: Hand off

- OpenClaw → [`standin-openclaw`](../standin-openclaw/)
- Hermes → [`standin-hermes-agent`](../standin-hermes-agent/)
- After the plugin is configured → [`expose-standin`](../expose-standin/)

## Gotchas

- **Do not `npx skills add` from inside a skill.** This repo is already
  installed. The work now is the SDK and the portal connection.
- **OpenClaw does not load a plugin by package name.** `plugins.load.paths`
  must point at a directory. The OpenClaw skill has the path.
- **Autopilot skips the SDK.** If they chose Autopilot, do not install
  `@komaa/standin-sdk` or merge `openclaw.json`.
- **The Azure Bot calling webhook is not the worker URL.**
  `https://<identity>.standin.komaa.com/api/calling` is set in Azure. The
  worker URL is what [`expose-standin`](../expose-standin/) registers in the
  StandIn dashboard.

## Common errors

| Symptom | Fix |
|---|---|
| Listener never logs that it is listening | Secret missing, not a string, or unresolved. Re-copy from the portal completion screen. |
| `Cannot find module '@komaa/standin-sdk'` | SDK installed in a different directory than the OpenClaw gateway. Install next to the gateway. |
| `ModuleNotFoundError: standin` | Wrong venv. `pip install "standin-sdk[hermes-agent]"` into the Hermes interpreter. |
| User has a secret but no calls | Plugin not configured yet, or the calling URL is not registered. Continue with the plugin skill, then expose. |

## Related skills

- [`standin-openclaw`](../standin-openclaw/): OpenClaw plugin
- [`standin-hermes-agent`](../standin-hermes-agent/): Hermes Agent plugin
- [`expose-standin`](../expose-standin/): publish `/msteams/calling`

## References

- Portal: <https://standin.komaa.com/dashboard>
- Docs: <https://docs.komaa.com>
- Connection modes: <https://docs.komaa.com/teams/connection-modes>
- SDK: <https://github.com/komaa-com/standin>
