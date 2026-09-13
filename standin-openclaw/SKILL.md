---
name: standin-openclaw
description: >
  Put an OpenClaw agent on a Microsoft Teams call with the StandIn SDK.
  Use when the user wants Microsoft Teams calling, StandIn, standin-sdk,
  @komaa/standin-sdk, OpenClaw, standin-msteams, or a Teams voice listener
  inside OpenClaw.
license: MIT
compatibility: >
  Requires OpenClaw 2026.6.10+, Node.js 20+, @komaa/standin-sdk installed
  next to the gateway, and a StandIn connection secret. Use setup-standin
  first if those are missing.
metadata:
  author: standin
  version: "0.1.0"
---

# Connect OpenClaw to Microsoft Teams

Give the OpenClaw agent a seat in a live Microsoft Teams call. StandIn joins
the call. This plugin loads **inside** the OpenClaw gateway.

```
Microsoft Teams call
        │
        ▼
StandIn                   joins the call, owns the Microsoft side
        │  one authenticated WebSocket per call
        ▼
@komaa/standin-sdk        answers the dial
        │
        ▼
plugins/openclaw          inside the gateway: resample, echo guard, barge-in
        │
        ▼
OpenClaw realtime         the voice provider and instructions
```

The caller talks to the realtime speech-to-speech provider OpenClaw is
configured with. OpenClaw tools, skills, and memory stay on chat. Recap is
the exception: it can post minutes after hang-up.

## Workflow

### Step 1: Confirm setup

Need `@komaa/standin-sdk` next to the gateway and a plain-string connection
secret. If either is missing, run [`setup-standin`](../setup-standin/) first.

The plugin id is `standin-msteams`. That is the key in `plugins.entries` and
the prefix on the boot log.

### Step 2: Point OpenClaw at the plugin directory

OpenClaw loads a plugin from a **directory**, not a package specifier:

```
node_modules/@komaa/standin-sdk/dist/plugins/openclaw
```

If the gateway's working directory is not the folder that owns
`node_modules`, use an absolute path.

### Step 3: Merge this into `~/.openclaw/openclaw.json`

`secret` must be a plain string. `inboundPolicy` defaults to `disabled`,
which refuses every call.

```json
{
  "plugins": {
    "load": {
      "paths": [
        "node_modules/@komaa/standin-sdk/dist/plugins/openclaw"
      ]
    },
    "entries": {
      "standin-msteams": {
        "enabled": true,
        "config": {
          "secret": "",
          "inboundPolicy": "allowlist",
          "allowFrom": [
            "00000000-0000-0000-0000-000000000000"
          ],
          "inboundGreeting": "Hi, this is your assistant. How can I help?",
          "callingPort": 9442,
          "bindAddress": "127.0.0.1",
          "path": "/msteams/calling",
          "maxConcurrentCalls": 4,
          "requireRecordingStatus": false,
          "sessionScope": "per-call",
          "meetingRecap": false,
          "realtime": {
            "provider": "openai",
            "providers": {
              "openai": {
                "apiKey": "",
                "voice": "alloy"
              }
            },
            "instructions": "You are on a Microsoft Teams call. Keep answers short and spoken."
          }
        }
      }
    }
  }
}
```

Leave `"secret"` empty in what you write here (or a host env reference if
the gateway supports them). The user fills it on disk. Keep live secrets
and provider keys off this chat, off git, and out of logs.

Laptop plus Tailscale Funnel: `bindAddress` `127.0.0.1`. A container behind
ingress can leave the SDK default `0.0.0.0`.

### Step 4: Restart the gateway

```bash
openclaw gateway
```

Success:

```
standin-msteams: listening on 127.0.0.1:9442/msteams/calling (max 4 concurrent)
```

If that line is missing, the secret is empty or not a string. If it warns
that no realtime voice provider resolved, every call is refused with
`realtime-unavailable`. The provider is resolved **once at boot**. A new API
key needs another restart.

### Step 5: Publish the listener

Follow [`expose-standin`](../expose-standin/). Do not invent a second funnel
command. Register the public `wss://` URL as the identity's agent calling URL
in the portal, then call the StandIn number.

## Who may call

`inboundPolicy` is `disabled`, `allowlist`, `pairing`, or `open`. Unset or
unknown **refuses**.

`allowFrom` takes the caller's **AAD object id**, not their email. Copy it
from `session.start.caller.aadId` on an inbound call. A refused call still
logs the id. Guest and anonymous callers have an empty id, so they cannot be
allowlisted.

`open` accepts every caller StandIn routes to this connection. Use it only
when the whole organization may call.

`pairing` is enforced as a plain allowlist on calls. There are no pairing
codes on this path.

## Meeting recap

Off unless `meetingRecap` is exactly `true`. Hang-up returns while the
minutes post.

`meetingRecap` posts through the OpenClaw consult integration and the
managed outbound chat lane on StandIn's bot. That is the recap path for
this plugin.

Unfinished recaps sit in `STANDIN_RECAP_DIR`, else `STANDIN_STATE_DIR/recap`,
else `~/.standin/state/recap`. Point that directory at disk that survives a
restart if you want unfinished minutes to send after one.

`sessionScope` (`per-call`, `per-thread`, `per-aad`) keys the consult that
writes the minutes, not the voice session. Voice is always per call.

## Scope

This plugin covers the call and the voice: realtime session, barge-in, echo
guard, recording gate, inbound policy. It does not drive OpenClaw tools or
memory on the call. It does not wire vision or the avatar into the realtime
session.

`requireRecordingStatus` waits for the Teams recording banner before the
agent speaks or listens. Leave it `false` unless the tenant records calls.

## Prefer Autopilot instead

If they would rather not run a gateway, turn on StandIn Autopilot in the
portal and skip this plugin.

## Gotchas

- **Do not write a worker process.** The plugin is a host-managed background
  service. OpenClaw starts and stops the listener.
- **A STT+TTS-only provider cannot drive this plugin.** The model must hear
  the caller directly.
- **Echo on speakerphone:** caller input is dropped while the agent is
  speaking, plus a short window after, unless it is loud enough to barge in.
  Tune `realtime.echoSuppressionWindowMs` (default 600) and
  `realtime.echoBargeInRms` (default 0.04), or set
  `realtime.suppressInputDuringPlayback` to `false`.
- **Call 5 is `busy`** at the default `maxConcurrentCalls` of 4.

## Common errors

| Symptom | Fix |
|---|---|
| No boot line | `secret` missing or not a string. |
| `realtime-unavailable` | Provider key missing at boot. Set it and restart. |
| `not-allowed` | Policy refused the caller. Log has the AAD object id. Add it to `allowFrom`. Emails never match. |
| `busy` | At `maxConcurrentCalls`. |
| Calls never reach the worker | Listener is up, URL is wrong. [`expose-standin`](../expose-standin/) |
| Agent greets itself | Echo guard too weak, or `suppressInputDuringPlayback` is off on a speakerphone. |

## Related skills

- [`setup-standin`](../setup-standin/): portal secret and `npm install`
- [`expose-standin`](../expose-standin/): funnel, probe, register URL
- [`standin-hermes-agent`](../standin-hermes-agent/): Python twin

## References

- OpenClaw plugin: <https://docs.komaa.com/typescript-sdk/plugins/openclaw>
- Example: <https://github.com/komaa-com/standin/tree/main/examples/openclaw-msteams-connector>
- Recap: <https://docs.komaa.com/typescript-sdk/minutes>
