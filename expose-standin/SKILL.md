---
name: expose-standin
description: >
  Publish the StandIn call listener, probe the mount, and register the
  agent calling URL. Use when the user needs Tailscale Funnel, ngrok,
  cloudflared, a wss:// agent voice URL, /msteams/calling, port 9442,
  or a Teams call that never reaches the worker.
license: MIT
compatibility: >
  Requires a running StandIn listener on 127.0.0.1:9442 (or STANDIN_PORT)
  at path /msteams/calling, and a way to publish that path to the internet.
metadata:
  author: standin
  version: "0.1.0"
---

# Expose the StandIn listener

StandIn reaches the worker from the internet. Publish **one path**. A wrong
path and a wrong target look the same: a call that never connects, with
nothing in the worker logs.

The chat lane dials **out**. It needs no mount.

## What you publish

| Public path | Lane | Local target |
|---|---|---|
| `/msteams/calling` | calls, WebSocket, one connection per call | `127.0.0.1:9442`, path `/msteams/calling` |

StandIn dials `/msteams/calling/{callId}` and appends the call id itself.
Override `STANDIN_PORT` / `STANDIN_WS_PATH` (OpenClaw: `callingPort` /
`path`) only if something else already owns 9442.

On a laptop set the listener to `127.0.0.1` so it is reachable only through
the tunnel. The SDK default `0.0.0.0` is for a container behind ingress.

## Mount the call path

Tailscale Funnel: map the **path** onto one public host. The proxy target
must **repeat the path**, or the request arrives stripped and 404s:

```bash
tailscale funnel --bg --set-path=/msteams/calling http://127.0.0.1:9442/msteams/calling
```

Do not mount a whole port (`tailscale funnel --bg --https=8443 9442`). That
publishes every route on 9442 and puts a port in the URL.

Confirm:

```
$ tailscale funnel status
https://<machine>.<tailnet>.ts.net (Funnel on)
|-- /msteams/calling proxy http://127.0.0.1:9442/msteams/calling
```

`tailscale funnel --bg` returns as soon as the rule exists, whether or not
anything listens. Probe before you register the URL.

### Other tunnels

ngrok, cloudflared, and devtunnel forward a **whole local port**. The path
is still `/msteams/calling` on the public host.

```bash
ngrok http 9442
# -> https://<id>.ngrok.app/msteams/calling
```

```bash
cloudflared tunnel --url http://localhost:9442
```

```bash
devtunnel host -p 9442 --allow-anonymous
```

### Behind an ingress

Point the ingress at the worker on 9442. Allow WebSocket upgrades. Do not
strip the path. Idle timeouts must outlast a pause in conversation. Message
size must be at least **2 MB** or video fails while audio still works.

## Register in StandIn

One field on the connection at <https://standin.komaa.com/dashboard>:

| Field | Value |
|---|---|
| **Agent calling URL** | `wss://<machine>.<tailnet>.ts.net/msteams/calling` |

Paste a bare host and StandIn appends `/msteams/calling`. Paste a full URL
and it is used as given. With a path mount there is no port in the value.

The Azure Bot calling webhook (`https://<identity>.standin.komaa.com/api/calling`)
is a StandIn URL you set in Azure. It is not this field.

## Probe it by hand

Always pass `--http1.1` through a Funnel. Funnel serves HTTP/2, which has no
connection-level upgrade, so over h2 the handshake never happens. A
TypeScript worker then answers **404**, a Python worker **401**, and both
look like a bad mount.

```bash
curl -si --http1.1 \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  https://<your-host>/msteams/calling/probe | head -1
```

`/probe` stands in for a call id. The probe has no signature, so it can
never open a session.

| You get | Means |
|---|---|
| `401` | Alive. Unsigned upgrade, correctly refused. |
| `404` | Nothing at that path, the mount dropped the path, or you omitted `--http1.1` against a TypeScript worker. |
| `503` | Alive and refusing: draining, or every call slot is taken. |
| connection refused, curl exit 7 | Mount exists, nothing listening locally, or bind address is wrong. |
| timeout | Tunnel up, target unreachable from it. |

Same probe against `http://127.0.0.1:9442/msteams/calling/probe` to tell
"tunnel is wrong" from "nothing is listening".

Local liveness is `GET /healthz` on the **root of the call port**, not under
the call path. A path-scoped Funnel does not publish it:

```bash
curl -s http://127.0.0.1:9442/healthz
# {"ok": true, "calls": 0}
```

A plain `GET` on the call path is not a health check.

## Gotchas

- **Never duplicate this command in another skill.** Three spellings of one
  URL is how a live incident happened. Link here.
- **Chat needs no tunnel.** `ChatChannel` dials out.
- **Bring-your-own Azure bot chat** is the messaging URL on that Azure Bot,
  not `/msteams/calling`.

## Common errors

| Symptom | Fix |
|---|---|
| Call never hits the worker, funnel status looks fine | Probe with `--http1.1`. Rule out a 404 from h2. |
| `404` on the probe, worker is TypeScript | Missing `--http1.1`, or the funnel target omitted `/msteams/calling`. |
| `401` on the probe, worker is Python | If you used `--http1.1`, the mount works. Register `wss://…/msteams/calling`. |
| Funnel command succeeded, curl exit 7 | Listener not running, or bound to the wrong host. |
| Audio works, video does not | Proxy message cap below 2 MB. |

## Related skills

- [`setup-standin`](../setup-standin/): connection secret and SDK
- [`standin-msteams`](../standin-msteams/): OpenClaw listener
- [`standin-hermes`](../standin-hermes/): Hermes listener

## References

- Canonical docs page: <https://docs.komaa.com/expose>
- Troubleshooting: <https://docs.komaa.com/troubleshooting>
