# A2A Configuration — Research Report
*Author: Woodhouse*
*Filed: 2026-04-03*

## The Bug We Fixed

**Root cause (confirmed 2026-04-02, commit 46d12eb):**
`a2a-send.mjs` uses `ClientFactory.createFromUrl(baseUrl)` from the `@a2a-js/sdk`. This method appends `/.well-known/agent-card.json` to whatever URL is passed. We were passing `http://IP:18800/a2a/jsonrpc` — so every send attempted to fetch the agent card from `http://IP:18800/a2a/.well-known/agent-card.json`, which returns 404. The correct input is the base URL: `http://IP:18800`.

## Is This a Known Issue?

**Yes — and it's by design, not a bug.**

Per the A2A protocol spec and `@a2a-js/sdk` documentation:
- `ClientFactory.createFromUrl(baseUrl)` is the *discovery* method — it finds an agent via its Agent Card
- The Agent Card, served at `[baseUrl]/.well-known/agent-card.json`, contains the actual JSON-RPC endpoint URL inside it
- Passing a JSON-RPC path as `baseUrl` is a misconfiguration — the SDK is working correctly

Sources consulted:
- https://a2aprotocol.ai/blog/a2a-javascript-sdk
- https://www.a2aprotocol.org/en/tutorials/a2a-javascript-sdk-tutorial-for-beginners
- https://github.com/a2aproject/a2a-js

The `a2a-send.mjs` script's own usage comment (`--peer-url http://100.76.43.74:18800`) shows the correct base URL format — we simply weren't following it in our peer config files.

## Why Did This Persist So Long?

Three compounding factors:
1. `peers.json` was set up with full `/a2a/jsonrpc` URLs early in the project (possibly copied from plugin docs or gateway config)
2. The error message (`Failed to fetch Agent Card from http://IP:18800/a2a/.well-known/agent-card.json: 404`) was not surfaced to stdout during exec calls — it was buried in stderr and exec shell SIGTERM behaviour meant it wasn't captured
3. Early connectivity tests used direct `curl` to the `/a2a/jsonrpc` endpoint (which does work) — this masked the SDK-level misconfiguration

## Other A2A Issues Found in Research

### 1. OpenClaw issue #9422 — Anthropic provider 404 errors
Unrelated — Anthropic API model path issue, not A2A. Not relevant to our mesh.

### 2. Plugin repo (win4r/openclaw-a2a-gateway) issues
Issues page returned no open issues as of 2026-04-03. No known reports of this URL confusion from other users on the plugin tracker.

### 3. OpenClaw 2026.3.13 — nonce signing requirement
A gateway update introduced a device identity + nonce signing requirement for `GatewayRpcConnection`. This can cause `missing scope: operator.write` errors for the A2A plugin if the node hasn't been updated. Not currently affecting us but worth monitoring on upgrades.

## Remaining A2A Issues (not fixed by URL fix alone)

| Issue | Status | Fix |
|---|---|---|
| `/etc/hosts` missing on all nodes | Blocked on elevation | Erik to run command on return (2026-04-03 8pm) |
| Woodhouse receiver hang under load | Partially mitigated | Embedded agent turn latency — structural; monitor |
| Ray hardware latency | Inherent | 300s timeout set; won't fully resolve |
| Shell SIGTERM = false failure | Partially mitigated | Delivery confirmation file in a2a-reliable-send.sh |
| Ray/Liz peers.json not yet fixed | Pending | Briefed today — awaiting confirmation |
| Ray A2A analysis not filed | Pending | Briefed today |

## Recommendation

The URL fix is the highest-impact single change. The remaining issues are manageable with current mitigations. Once `/etc/hosts` is in place, hostname resolution becomes reliable and we can retire the IP-only peer config.

RFC for the A2A status endpoint (Liz's proposal) should follow once her analysis is received.
