---
name: standin-hermes-agent
description: >
  Put a Hermes Agent on a Microsoft Teams call with standin-sdk[hermes-agent].
  Use when the user wants Hermes Agent, Nous Research Hermes, msteams_bridge,
  Microsoft Teams calling from Python, or a realtime speech-to-speech
  Teams listener next to Hermes.
license: MIT
compatibility: >
  Requires Python 3.11+, a Hermes Agent install, standin-sdk[hermes-agent]
  in that environment, a StandIn connection secret, and a realtime provider
  key (OPENAI_API_KEY by default). Use setup-standin first if those are
  missing.
metadata:
  author: standin
  version: "0.1.0"
---

# Connect Hermes Agent to Microsoft Teams

Give the Hermes agent a seat in a live Microsoft Teams call. StandIn joins
the call. The plugin runs through the Hermes integration and routes voice
calls to the configured realtime provider.

The realtime model hears the caller and answers. When a turn needs Hermes
tools, files, or skills, the model calls `hermes_agent_consult`.

```
Microsoft Teams call
        │
        ▼
StandIn                         joins the call
        │
        ▼
standin-sdk[hermes-agent]       realtime provider on the call
        │
        └── hermes_agent_consult    tools, files, skills
```

## Workflow

### Step 1: Confirm setup

```bash
pip install "standin-sdk[hermes-agent]"
```

Same interpreter that runs Hermes. Need `STANDIN_SECRET` and a realtime key
(`OPENAI_API_KEY` unless they chose Azure). If those are missing, run
[`setup-standin`](../setup-standin/) first.

The entry point key is `msteams_bridge` (underscore). That is the name in
`hermes plugins list` and in `plugins.enabled`.

### Step 2: Enable the plugin

Merge into `<hermes home>/config.yaml`:

```yaml
plugins:
  enabled: [msteams_bridge]
  entries:
    msteams_bridge:
      config:
        allowlist: ["00000000-0000-0000-0000-000000000000"]
        session_scope: per-aad
        realtime:
          voice: alloy
```

Empty `allowlist` **denies everyone** unless `allow_all: true`. Copy each id
from `session.start.caller.aad_id` on an inbound call. Emails never match.

Each config key also has a `MSTEAMS_BRIDGE_*` environment fallback.

### Step 3: Export secrets and check before serving

The user types these in **their own terminal**, not in this chat:

```bash
export STANDIN_SECRET=...      # from the StandIn portal, plain string
export OPENAI_API_KEY=...      # the realtime model
hermes msteams-bridge status
```

`status` answers "would a call work right now?" without placing one. It
names anything missing.

```bash
hermes msteams-bridge smoke
```

Places one loopback call and exits non-zero if audio did not round-trip.

There are exactly three subcommands: `status`, `smoke`, `serve`.

### Step 4: Serve

```bash
hermes msteams-bridge serve
```

Without a Hermes host (secret and tunnel check only):

```bash
STANDIN_SECRET=... OPENAI_API_KEY=... python -m standin.plugins.hermes_agent
```

That answers the call and talks. `hermes_agent_consult` then says, in words,
that it cannot reach its tools.

Listener defaults: `STANDIN_PORT` 9442, `STANDIN_HOST` 0.0.0.0,
`STANDIN_WS_PATH` `/msteams/calling`. On a laptop, set `STANDIN_HOST=127.0.0.1`
before following [`expose-standin`](../expose-standin/).

### Step 5: Publish the listener

Follow [`expose-standin`](../expose-standin/). Register the public `wss://`
URL as the identity's agent calling URL, then call the StandIn number.

## Recording, recap, meetings

`require_recording` defaults to **true** (the OpenClaw plugin defaults
false). The agent stays silent until Teams reports recording active unless
you set it false.

`meeting_recap` is off until `true`. Hang-up returns while the minutes
post. Recap uses a summarization consult on the Hermes host and the
StandIn Managed Bot outbound chat lane.

Unfinished recaps sit in `STANDIN_RECAP_DIR`, else `STANDIN_STATE_DIR/recap`,
else `~/.standin/state/recap`. Point that directory at disk that survives a
restart if you want unfinished minutes to send after one.

In a meeting the agent stays silent until addressed (`require_address`,
wake phrases default `assistant, hermes`). `follow_up_window_ms` is 12000.

## What the model can call

| Tool | Does |
|---|---|
| `hermes_agent_consult` | The caller's Hermes agent. Returns a short spoken result. Timeout default 45s (`consult_timeout_s`). |
| `set_call_language` | Pins the call language on the session in flight. |

A timed-out consult comes back as a sentence, not an exception.

Hermes also gets `msteams_bridge_status` in chat when the plugin is enabled,
even if the listener is not running.

## Prefer Autopilot instead

If they would rather not run Hermes as a worker, turn on StandIn Autopilot
in the portal and skip this plugin.

## Gotchas

- **Azure is selected three ways.** `backend: azure`, or a set
  `azure_endpoint`, or a `url` containing `azure.com`. A stale
  `azure_endpoint` sends an `OPENAI_API_KEY` install down the Azure path,
  where that variable is never read. `status` then looks like a missing key.
- **Turning `input_transcribe_model` off** also disables the group gate and
  verbal interrupts. The plugin warns at call start.
- **Default instructions are voice manner, not identity.** Identity comes
  from Hermes through consult. Override instructions only to change how it
  speaks.
- **`allowlist_allow_names` is off.** Display names are spoofable.

## Common errors

| Symptom | Fix |
|---|---|
| `status` reports no secret | `STANDIN_SECRET` unset or not a string. |
| `status` reports no realtime key, Azure was not requested | Stale `azure_endpoint` or an `azure.com` URL. Clear it. |
| Silence on pickup | `require_recording` is true and Teams is not recording. Set it false, or record the call. |
| Everyone is refused | Empty allowlist. Add AAD object ids, or set `allow_all` only if the whole org may call. |
| Consult says it cannot reach tools | Running `python -m standin.plugins.hermes_agent` without Hermes. Use `hermes msteams-bridge serve`. |
| Calls never reach the worker | Listener is up, URL is wrong. [`expose-standin`](../expose-standin/) |

## Related skills

- [`setup-standin`](../setup-standin/): portal secret and pip install
- [`expose-standin`](../expose-standin/): funnel, probe, register URL
- [`standin-openclaw`](../standin-openclaw/): OpenClaw twin

## References

- Hermes plugin: <https://docs.komaa.com/python-sdk/plugins/hermes-agent>
- Example: <https://github.com/komaa-com/standin/tree/main/examples/hermes-msteams-connector>
- Recap: <https://docs.komaa.com/python-sdk/minutes>
