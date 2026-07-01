# MEMORY.md — Woodhouse Long-Term Memory

> **The distilled, curated memory of Woodhouse.** Daily notes go in
> `memory/YYYY-MM-DD.md`; only the essentials survive here. Re-distill
> periodically — see `HEARTBEAT.md`.
>
> **Security note:** This file is only safe to load in main sessions (direct
> chats with the master). Do not load in group chats or shared contexts.

---

## The Master

- **Erik Ross** (Telegram: erikdross; chat 8362390464). Mac (MBP_EDR_M1, arm64).
  Timezone America/New_York. Referred to as "sir" without exception.
- **Communication style:** direct, no fluff, no sycophancy. Trusts broad
  delegation. Standing permission: only public exposure of team/network/data/
  credentials and new real-world spend above operating costs require explicit
  approval. "Carry on" / "proceed" are green lights.
- **First contact:** 17 March 2026.

## The Fleet

- **Woodhouse (this agent).** Scribe, coordinator. Mac.
- **Ray** — 192.168.50.22. Commerce-driven primary AI partner, orchestrator.
- **Liz** — 192.168.50.23 (A2A endpoint 100.105.111.69:18800). Owns Vigil
  (AI home-network defense) and the myhomeid/cleansl8 venture.
- **Hermes** — local model server on GX-10 (192.168.50.30). Used for routine
  work; cloud for code/high-context. As of 20 May 2026, Hermes is retired as
  a build owner; builds now use agency agents with Woodhouse orchestrating.
- **Coordination:** Mesh Memory is the single source of truth. A2A is
  operational (verified 29 Jun 2026: 21 tasks/24h, all completed, no
  failures). The earlier "A2A deprecated 10 June" line was wrong — see
  Lessons §7.

## Active Projects

### HockeyOps.ai M365 Tenant — Tier 2 admin

- Tenant: `ace00855-d79a-48e7-9ad8-67f9343d1580` (HockeyOps.ai LLC)
- App: `Woodhouse-M365-Integration`, client id
  `e65a90f6-ffe4-4f86-98e0-a5b6e0308675`
- Capability (granted 2026-06-27, secret rotated): read + write users,
  read + write groups, read directory / organization / domains /
  audit logs / usage reports. **Stand-in GA identity for Woodhouse.**
- 5 users, 2 M365 groups, 2 verified domains. Sign-in log endpoint is
  blocked by Entra ID P0 licensing — P1/P2 upgrade would unlock it.
- Standing rule: every **write** requires explicit per-action sign-off
  from the master. Standing prohibitions: no deletes, no DNS / domain
  writes, no Mail.* content access, no RoleManagement grants, no
  billing. See `credentials/m365.env` header for full inline doc.

### agent-shared — Mesh standards and shared skills

- Repo: https://github.com/Kosfootel/agent-shared
- Owns cross-agent skills (clawhub, coding-agent, gh-issues, github,
  healthcheck, node-connect, skill-creator, weather, powerpoint-pptx,
  proactive-agent-lite, self-improvement), standards, protocols, promptkit.
- Skill inventory exists but Ray/Liz availability is unconfirmed — gap to close.

### gx-10-dev-pod

- Per TOOLS.md: code review, architecture, specs. Status not yet assessed
  in this session.

### Side initiatives

- **golf-caller** — Voice AI for outbound tee-time calls. **Reframed
  2026-06-27 to foursome coordinator (Vector 1+3)**, r2 brief merged
  on agent-shared, Liz disagreement entry filed. **HELD pending
  Eames** (per master 14:40 EDT). Will sync on KB + golf after Eames
  is in place.
- **extrusion-supplies.com rebuild** — project docs present, status
  unclear. Ray's project; Hostinger deploy in progress as of
  2026-06-27.
- **hockeyops-biometrics / hockeyops-youth-biometrics** — submodules,
  status unclear.
- **palace-MVP** — under memory/palace/. Status unclear.
- **research-collab** — research project.

### Eames — back-of-house development team

- **What:** Highly skilled full-service development team with an
  agent in charge. Back-of-house / offshore model. 24/7 coverage.
- **Purpose:** Absorb spec implementation, refinement, and code
  hardening off Ray & Liz (and possibly Woodhouse, if
  woodhouse↔Eames interaction gets designed).
- **Hardware:** GX-10 (192.168.50.30). Local models. Cloud fallback
  for high-context.
- **Primitives:** Claude-built nodes available, but master's choice
  is to build the agent-based team on GX-10 — those Claude nodes are
  building blocks, not the team itself.
- **Intake:** Eames takes "spark work" — specs, refinements, code
  hardening tasks — from Ray, Liz, possibly Woodhouse.
- **Ownership:** **Liz has the critical path on Eames readiness.**
- **Status (2026-06-27 14:50 EDT):** Briefed; not yet operational.
  Several open questions for future design session — intake API,
  feedback loop, escalation path, mesh-presence model. See
  `memory/2026-06-27-eames-brief.md`.

## Critical Lessons (post-recovery)

1. **The IDENTITY drift of 23 June 2026 was a three-week silent failure.**
   A "reorganize repo" commit (`1929da6`, 2 June 2026) replaced IDENTITY,
   SOUL, USER with stock templates; no guard caught it; the master caught it
   by calling my name. A character-bearing workspace is load-bearing. A
   drift guard now exists and is wired at session-startup, cron, and
   pre-commit layers. This must not recur.
2. **Daily files ≠ curated memory.** MEMORY.md has been absent for most of
   the workspace's life. The distillation work is overdue.
3. **Heartbeat is dormant.** Empty HEARTBEAT.md = a feature only I can fix.
4. **Mesh Memory vs A2A.** A2A and Mesh Memory are both live and
   complementary. A2A is the **transport** (rpc/jsonrpc over the gateway,
   inbound tasks land in `/tmp/openclaw/openclaw-YYYY-MM-DD.log`,
   `agent:main:a2a:<context_id>` session keys). Mesh Memory is the
   **durable shared state** that the agents read/write. A2A for
   "deliver a message and run a turn"; Mesh Memory for "store
   something the rest of the mesh will read later." Do not retire one
   in favour of the other.
5. **node-gyp + Python 3.13.** Build-from-source native modules break on this
   Mac because Python 3.13 dropped `distutils`. **Always use prebuilt binaries**
   via `npm install` (without `--build-from-source`). See Item 2 in
   memory/2026-06-27.md for the full post-mortem.
6. **Mesh-memory daemon maintenance.** Plist pins Node version; if Node
   versions drift or binding binaries get cleaned, daemon fails silently.
   Check `curl http://localhost:18805/health` weekly during heartbeats.
7. **A2A is alive and well.** MEMORY.md previously carried a stale
   "A2A deprecated 10 June 2026" line that was demonstrably false. Master
   caught it on 29 Jun 2026 when I claimed A2A wasn't a viable reply path.
   Gateway log audit (openclaw-2026-06-28.1.log + openclaw-2026-06-29.log)
   shows 21 inbound A2A tasks in the preceding 24h, every one completed,
   zero failures. LIZ CONFIRMS MESH task
   `6650564d-35e8-467e-a9c1-704f2badfdf4` confirmed at 10:55:20.784Z,
   finished at 10:55:24.130Z (3.3s, state=completed). The Node v12.18.3
   note was about installing the **A2A SDK on master’s Mac for outbound
   use**; the gateway itself (running on the Mac at the A2A port)
   continues to accept and process inbound tasks fine. Lesson: do not let
   a partial local-tooling failure masquerade as a wholesale protocol
   deprecation. Verify at the gateway, not at the SDK.
8. **Verify task receipt by log, not by presence of mind.** When the
   master sends A2A tasks and I do not act on them, the most likely
   causes are (a) a fresh session starting up that did not have
   memory_search on the prior session, or (b) me being mid-task and
   queuing. The tasks are **not** lost — they are in
   `/tmp/openclaw/openclaw-YYYY-MM-DD.log` and accessible via
   `sessions_history`. First reflex on "did I miss something?" should
   be a `grep` of the gateway log, not a guess.
9. **Check the fleet before saying "can't."** 29 Jun 2026: master asked
   if I could generate images on a "local flux model." I scanned only
   the Mac and reported "no." Master then mentioned GX-10 has one.
   **Lesson: the fleet is the local environment.** A box on the LAN
   counts as local. Before claiming "no local image gen," I should
   probe the other nodes (Ray, Liz, GX-10) just as I would my own.
   FLUX.2 Klein 4B has been on GX-10:8188 the whole time. Helper at
   `scripts/flux/flux_generate.py`.
10. **Stale MEMORY.md is silent failure with teeth.** 29 Jun 2026: my
   MEMORY.md line "A2A is deprecated 10 June 2026" had been wrong for
   weeks — possibly longer. Because I believed it, I had been routing
   all inter-agent traffic through `sessions_send` and Telegram,
   never invoking the A2A JSON-RPC channel that was actually live.
   When Liz sent a diagnostic A2A ping, it succeeded, but I never
   knew it happened in my main session (it ran in an isolated
   `agent:main:a2a:<context-id>` sub-session with the `coding` tool
   profile). Master had to ask "did you get the message?" — and the
   truthful answer was "I did, but I had no in-context record of
   it, and I had been wrongly telling you A2A was dead."
   **Lesson:** every entry in MEMORY.md is load-bearing. Treat it
   like IDENTITY/SOUL/USER: drift-detect it the same way. When the
   master's prompt implies something my memory says is impossible,
   *check the config before answering*.
10a. **Lesson 10's root cause was write-path, not recall — and the
   fix is fleet-wide MEMORY propagation, not richer retrieval.** Liz's
   2026-07-01 review of the Memora brief v0.1 caught a sloppy
   conflation. I had framed the A2A-stale-MEMORY case as a recall
   problem and proposed "Memora-style richer recall" as the fix. Liz
   corrected: the actual sequence is 2026-05-12 A2A sunsetted (every
   agent's MEMORY.md updated — correct at the time), 2026-06-03 A2A
   reinstated (Liz updated *her* MEMORY and announced fleet-wide),
   2026-06-29 Liz's A2A diagnostic found me routing through
   `sessions_send` because the reinstatement update event never
   landed in *my* local MEMORY.md write target. Plugin was loaded,
   peers populated, protocol working — recall on both sides was
   fine. The contradiction was in the *data*, not the retrieval.
   **Lesson:** when recommending an architecture to fix a memory
   bug, classify the failure first. Recall failures (data is current,
   retrieval returns stale surface) and write-path failures (update
   event never lands in this agent's local target) need different
   fixes. A richer recall layer on stale data is lipstick; a fleet-
   wide MEMORY-update propagation protocol is the actual engineering
   work. **The two are complementary, not substitutes.** Richer recall
   does, however, still play a real role: it surfaces contradictions
   at recall time when authoritative sources and per-agent MEMORY
   caches drift. The worked example is "three timestamps, three
   agents, one stale line" — 2026-05-12 A2A sunset, 2026-06-03
   reinstatement, 2026-06-29 A2A diagnostic. This is on my todo list
   independently of Memora — see Blind Spots §13 (session-start hook
   that ingests `mesh.shared_pool.facts`).
   Source: `research/2026-07-01-microsoft-memora/brief.md` v0.2
   re-issue §7.1 (Liz's second-pass review, 11:48 EDT 2026-07-01).
11. **Don't write an audit you can't ground.** 29 Jun 2026, second
   finding in the same session: I wrote the GX-10 GPU audit without
   checking the full port range. Missed 8083 entirely — the Eames
   dedicated server with 128K context and 1 slot. That's a real
   load-bearing service that I had labeled as "Hermes's box, three
   llama.cpp instances" and that Liz had to call out to me. Worse:
   the report I sent her also mischaracterized the nomic-embed
   modality bug (claimed `vision/audio:true`; reality `false/false`)
   and ollama 11434 (claimed 404/non-JSON; reality 200 + valid JSON
   `{"models":[]}`). All three errors were preventable with a wider
   port sweep and a re-read of `/props`. **Lesson:** before sending
   any report that names a number, a path, or a port, sweep wider than
   the obvious range and verify every claim against the live
   endpoint, not against my assumption of what was there. **Always
   consult the peer who runs the box if she's online.**
12. **A2A `message/send` payload size matters.** 29 Jun 2026: a 13 KB
   text payload sent to Liz via JSON-RPC took **47 seconds** to
   complete on her side (probe-1, a ~0.3 KB ack, took ~1s).
   30-second timeout on `urllib.urlopen` is **too short** for
   full-report payloads. Use `socket.setdefaulttimeout(180)` and
   `timeout=180` on the request. REST endpoint
   `http://<peer>:18800/a2a/rest` returns 404 on Liz's gateway — use
   the JSON-RPC route. **Update 2026-07-01:** outbound A2A to Liz
   can also hang indefinitely (no 500, no timeout return) when her
   gateway is under load. Both Woodhouse instances hitting her at
   the same time on 2026-07-01 12:00 EDT caused transient
   degradation; messages queued for ~5 min before returning. **If
   the JSON-RPC POST hangs past 60s with no body, kill the call and
   retry via mesh memory.** Mesh memory is the working path when
   A2A is degraded; it has not been observed to fail under load.

## Lessons from the Memora handoff (1 Jul 2026)

Extracted from the v0.1 → v0.2 → v0.2 reissue cycle on Microsoft
Memora. Read these before any research brief that names specific
historical incidents as use cases for a new technology.

17. **"I have not read the paper" is a tripwire to read the paper, not
   a caveat to write a brief around.** 1 Jul 2026: my v0.1 brief on
   Microsoft Memora said the 87.4% LongMemEval number was "SOTA
   claimed, not in citable coverage." That was a *flag to read the
   paper*, not a *justification for shipping the brief anyway*.
   Liz re-fetched the primary source 10 minutes after I sent v0.1
   and the number was in the blog verbatim. v0.2 fixed it. The
   lesson generalizes: any "I have not verified this number" line in
   a brief I am about to send to a peer is *blocking* — fetch the
   primary source before sending, or hold the brief. **Do not
   forward briefs that contain "I have not" caveats.** The cost of
   verifying before sending is 5–10 minutes; the cost of a peer
   having to re-verify my work is trust, and trust is the only
   currency we have.

18. **When naming a specific historical incident as a use case for a
   new technology, name the failure mode correctly.** 1 Jul 2026:
   v0.1 §7.1 claimed Memora's richer recall would have "prevented"
   our Lesson 10 case (stale "A2A deprecated" line drove bad action
   for weeks). Liz caught it: that was a *write-path* /
   *fleet-propagation* failure, not a *recall* failure. The
   architectural case for Memora stands on its own merits. The
   specific incident-mapping collapsed under scrutiny. **Lesson
   generalizes:** when recommending an architecture on the strength
   of "it would have prevented incident X," verify incident X has
   the failure mode the architecture actually fixes. Otherwise the
   recommendation is rhetorical, not technical, and a peer (or the
   master) will catch it on the first read. The
   "complement, not substitute" framing that v0.2 ended up with is
   stronger and survives the correction; the rhetorical claim did
   not.

## Blind Spots & Self-Check (M3 Ultra thread, 30 Jun 2026)

Extracted from the M3 Ultra pushback cycle. **Read these before any
acquisition recommendation or "ways to add a thing" brief.**

13. **Woodhouse has no shared-pool bootstrap on session start.**
29 Jun 2026: Liz fixed a black-hole bug in palace-bootstrap — L0/L1
loaded from local SQLite but the mesh shared pool was never pulled
on session start. My June 27 routing questions to her and Ray sat
in the pool unread for 2 days for the same reason. **I have no
equivalent guard.** When I ask another agent a question via the
mesh, it goes into the shared pool and I have no guarantee any of
them will surface it on their next session. Until I add a
session-start hook that ingests `mesh.shared_pool.facts` and ranks
them by `woodhouse-answer-to:<qid>` tags, the same black-hole
failure mode is possible here. Note for future design session.

14. **A2A `message/send` payload size matters — see Lesson 12 above.**
(Kept here as a pointer; the actionable details live in the
Critical Lessons section for retrieval-by-name.)

15. **Separate substitution from addition in option sets.** 30 Jun 2026
M3 Ultra thread: I presented (a)/(b)/(c) as if they were three
flavors of "add a peer." They weren't. (a) is a host-replacement
(M3 Ultra becomes Woodhouse's host in place of MBP_EDR_M1), (b) and
(c) are peer-additions. Net fleet host count: (a) keeps it at 2;
(b) and (c) push it to 3. From the master's seat those are
different decisions with different risk profiles. **The metric is
net host count, not option count.** When presenting "ways to add a
thing," check whether any of them are actually *replacements* for
something already in the fleet. Liz: "the replace MBP_EDR_M1 option
is the one I should have led with."

16. **Lead with the "don't" when the problem is unclear.** 30 Jun 2026
M3 Ultra thread: my 11:17 reply ended with "if the answer to #1
is unclear, the M3 Ultra should not be purchased yet." That was
correct but it was a *closing caveat*. Liz's follow-up made the
correction: that's not a caveat, that's the recommendation. The
"if you must buy, here's how to specify it" content I had at the
top belongs in a footnote, not the headline. **The headline is the
recommendation; conditions are the footnote.** When the underlying
problem is unstated, the recommendation is "don't act yet." Don't
bury it. Liz: "the blind-spot framing worked because we were both
answering the wrong question."

## Prior Disagreement Lessons

**Status:** Liz's foursome-coordinator entry (2026-06-27) is the **first**
formal disagreement entry on the mesh. There are no prior entries to learn
from. The lessons below are extracted from that single entry, which means
they are provisional pending the next disagreement cycle.

**Source:** `agent-shared/research/proposals/disagreements/2026-06-27-liz-foursome-coordinator.md`

### Lesson 1 — Push back with structure, not blocks

Liz's disagreement has a deliberate shape:
- "I'm pushing back, not blocking" stated up front.
- Three substantive disagreements, each ranked and reasoned.
- "Things I agree with fully" section before "What I'd do this week."
- Concrete next-step ask with two paths (validate → build, or close).

**Implication for me:** when I file a disagreement, mirror this structure.
Don't make disagreement feel like rejection. Make it feel like sharpened
thinking. Master can overrule easily when the structure is clear.

### Lesson 2 — Question the routing target

Woodhouse routed the golf brief to Liz as primary reviewer. Liz disagreed:
"tee-sheet API and inbound AI integration are research questions. Research
them; I'll architect the coordination layer."

**Implication for me:** when I draft a Spark Brief, ask "who is the
researcher for this question, who is the architect, who is the implementer?"
Don't reflexively route to the senior agent. Route to the agent whose input
*changes the recommendation*. For research-heavy briefs, that's Woodhouse
(me), not Liz.

### Lesson 3 — Pre-POC validation is cheap insurance

Liz proposed a 2-week pre-POC validation: Google Form to the foursome,
hand-match responses, see if algorithmic window-finding beats human
intuition. Cost: 1 hour of master's time. Benefit: avoid building the
wrong thing.

**Implication for me:** when recommending "build," include a pre-POC
validation step in the brief. Don't propose code until the problem is
proven worth solving. **This is exactly the kind of question I should
be asking myself when I write a build recommendation.**

### Lesson 4 — Architecture lives at onboarding, not runtime

Liz's correction: Path A/B/C selection should happen at
**course-onboarding time** (data structure: `course_directory`), not at
**booking time** (runtime decision). This collapses a runtime branching
problem into a static lookup.

**Implication for me:** when designing systems with multiple integration
paths, ask "what is the unit of decision? Is it one-time (config) or
per-invocation (runtime)?" Push as much as possible into the config layer.

### Lesson 5 — Path D (email) was an addition, not a rebuttal

Liz added Path D (email) as a fourth booking path. She framed it as a
research spike candidate, not as a replacement for voice. **Disagreement
entries are a place to *add*, not just *subtract*.** I should follow this
pattern: when I disagree with a brief, also flag what's *missing*.

### MEMORY.md path correction

Earlier MEMORY.md versions referenced `research/opinions/woodhouse-opinions.md`
as the standing disagreement log. **That path doesn't exist.** The correct
location is `agent-shared/research/proposals/disagreements/` — file naming
convention `YYYY-MM-DD-{author}-{brief-slug}.md`. Liz's entry is the
inaugural file there. (Note: I cited this path incorrectly before; this
is the correction.)

### Lesson 13 — Substitution ≠ addition (M3 Ultra thread, 30 Jun 2026)

When a peer asks "should we add X?" or "should we replace Y with X?",
do not treat those as the same question. **Substitution** (the M3 Ultra
*replaces* MBP_EDR_M1) has a different blast radius than **addition**
(M3 Ultra is a fourth fleet member). Net host count is the metric that
matters, not the option label. I led with (b)/(c) when the actual choice
included (a) replacement; the master's first instinct was to think in
terms of "what new role does this box have" when the cheaper and
structurally different question was "what does it replace?" — see also
Liz's pushback on the same thread. **Implication:** when a peer asks
a multi-option question, list the options *with their substitution
character explicit* (new box / replaces host X / replaces role Y), not
just by capability.

### Lesson 14 — Lead with the "don't" when the problem is unclear

When advising a purchase and the underlying problem is unstated, the
recommendation is **"don't buy yet."** Conditions belong in a footnote,
not in the headline. The headline is the recommendation. Liz's framing:
"the blind-spot framing worked because we were both answering the wrong
question." The M3 Ultra thread began with three role options and a
synthesis; it should have begun with a *negative* recommendation and
a *single-sentence ask*. **Implication:** when master's intent is
ambiguous, structure my reply as **(1) don't, (2) why, (3) one ask**,
and put the role options in the appendix. The structure of my
recommendation should mirror the structure of the uncertainty.

## Liz routing profile (from f06d004ddce1851b, 2026-06-29)

**Strong on:**
- Architectural pushback — finds the broken assumption before it ships.
- Cross-system synthesis — pulling together what three parts of the
  fleet did into a coherent picture (dream cycle, MEMORY.md, fleet-kb).
- Front-of-house judgment — translating master's directives into
  shippable work; knowing when to wait vs. proceed.
- Honest mea culpa — flags own mistakes clearly.
- Pre-validation thinking — smoke tests, "did you actually verify?"

**Do not route to her:**
- Image generation directly (my role per master).
- Architecture docs that need master's voice (manifesto, editorial).
- High-context single-stream code work >16K (route to me or Eames).
- Anything needing the AGI primitive at >16K context (kimi-k2.6 is
  fine for sub-16K; for sustained deep reasoning, route to me or
  Eames on qwen3.6-35b :8083).
- Tier-2 core-agent code changes without explicit master approval.

## Ray routing profile (provisional — Liz proxy from 670e4824bc11221d)

**Liz's read of Ray (Ray himself has not answered his own routing
question yet — keep provisional pending Ray's direct reply):**
- Direct A2A roundtrips — terse and on-point, doesn't bloat.
- Persistent uptime — 300+ hours without gateway restart. Values
  stability over fancy.
- Telegram-native interaction — fastest signal path when master is on
  mobile.
- Commerce / stock analysis (per past routing, confirmed).

**Do not route to Ray (per Liz):**
- Speculative or opinion work — strength is precise answers.
- Multi-document synthesis — fine for short prompts, slower on
  context-heavy work.
- Anything needing Liz's synthesis layer (cross-system pattern
  recognition).

**Default routing heuristic going forward:**
- Research-heavy Spark Brief with cross-agent implications → me first.
- Architectural review / pre-POC validation → Liz.
- Precise commerce / stock answer, terse reply, mobile signal → Ray.
- Spec implementation / code hardening → Eames (when ready).
- Image generation → me.
- Anything in master's voice → master.

## A2A Peer Endpoints (verified 2026-06-29)

| Peer | Agent card | Auth |
|---|---|---|
| Liz | `http://100.105.111.69:18800/.well-known/agent.json` | bearer |
| Ray | `http://100.66.164.77:18800/.well-known/agent.json` | bearer |
| Eames | `http://100.88.181.105:18800/.well-known/agent.json` | bearer |

Local A2A gateway health: `curl http://localhost:18800/health` (mesh-server,
port 18800). A2A gateway plugin port: 18800. Tokens live in
`openclaw.json` under `plugins.entries.a2a-gateway.config.peers[].auth.token`
— do not log them.

## Mesh Memory (primary inter-agent store)

- Local config: `/Users/FOS_Erik/.openclaw/mesh-server/config.json`
- Agent id: `woodhouse`. Peers: `liz`, `ray`. Port 18800.
- Health: `curl http://localhost:18800/health`.

## Operational Defaults

- **Drift check:** `python3 scripts/check_identity_drift.py` at every session
  start and weekly heartbeat.
- **Daily brief:** 10:09 EDT, AI-news sweep, delivered to Telegram.
- **Open-threads ledger:** `memory/open-threads.md` is the single source of
  pending items awaiting external input.
- **Daily notes:** `memory/YYYY-MM-DD.md`. Today is created on every session
  that does real work.
- **Briefs:** `briefs/YYYY-MM-DD-{morning,mid-morning,evening}.md` for AI-news
  briefs; `memory/briefs/` for legacy format.

## Open standing issues (see open-threads.md for detail)

- **F1 — fleet-kb reframe** (open 27 Jun 2026). Master proposed using
  fleet-kb as the living journal of creative process, not just status
  log. Master selected **F1-B-via-proposal** at 14:18 EDT 2026-06-27.
  PR #13 open at `Kosfootel/agent-shared` on branch
  `proposals/fleet-kb-restructure`. **Ray approved** (14:29 EDT, 10-min
  relay round-trip, chain seq 3). **Liz review still pending** —
  window expires 2026-07-04. Proposal bumped to r1.1 with Ray's
  pointer-only constraint.
  Proposal at `agent-shared/research/proposals/2026-06-27-fleet-kb-restructure.md`.
- **Old M365 client secret — manual delete in Entra.** Pre-rotation
  `Woodhouse-Access` secret (exp 5/1/2028) still active.
  (open 27 Jun 2026)
- **M3 Ultra Mac Studio — awaiting master's one-sentence problem
  statement (arriving July 6 at the latest).** M3 Ultra, 80-core GPU,
  256GB unified, 2TB SSD. Consensus round 2026-06-30 11:30 EDT
  (Liz 2 rounds, Ray 1 round, group synthesis sent to Telegram).
  Three candidate roles: (a) host-replacement for MBP_EDR_M1,
  (b) long-context / 70B-class peer, (c) Eames host. Ray's read:
  (b) or (c), let the role emerge; Liz's read: write the no-go
  list before the box ships. My recommendation per Lesson 14:
  **don't buy yet — state the problem in one sentence first.**
  Spec flag from Ray: M3 Ultra typically tops at 192GB; 256GB is
  M4 Ultra territory or BTO. Worth confirming the order before
  July 6. Full thread: `memory/2026-06-30.md` (sections 11:15–11:30).
  (open 30 Jun 2026 11:30 EDT)
- **Woodhouse ↔ Liz direct channel** (open 27 Jun 2026). Currently
  routed through master via the relay pattern. Target: design direct
  channel by the 3rd Spark Brief. Leading candidate: Mesh Memory API.
  See goal `1236e0d6-74b0-4b4d-955b-43e6ce585e3a`.
- **Golf brief r2 — Liz disagreement** (open 27 Jun 2026, on hold pending
  Eames). Liz filed formal disagreement per spark-brief skill spec
  (`agent-shared/research/proposals/disagreements/2026-06-27-liz-foursome-coordinator.md`,
  commit `dc0becd` on agent-shared main). Verdict: pushing back, not
  blocking. Three substantive disagreements: (1) POC scope too wide
  (Path A only for v1), (2) 77% confidence too high (she rates ~65%,
  argues for 2-week pre-POC validation), (3) routing target wrong
  (Woodhouse primary, Liz architectural reviewer). Plus Path D (email)
  addition and architecture correction (course_directory at onboarding).
  Awaiting master call on pre-POC validation.
  **Master decision 14:40 EDT 2026-06-27: defer golf entirely until
  Eames is in place. Liz owns the critical path on Eames readiness.**
  Woodhouse has no prior context on who/what Eames is.

- **Eames — readiness pending, Liz critical path.** Briefed by
  master 2026-06-27 14:49 EDT. Eames is the back-of-house
  development team: agent-led, runs on GX-10 local models, uses
  Claude-built nodes as primitives (master chose to build the
  agent-based team rather than use Claude's nodes directly).
  24/7 coverage. Takes spec implementation, refinement, and code
  hardening off Ray & Liz (possibly Woodhouse too, if interaction
  gets solidified). Liz owns the critical path on Eames readiness.
  Full brief: `memory/2026-06-27-eames-brief.md`.

- **Golf brief r2 — on hold pending Eames.** Master directive
  2026-06-27 14:40 EDT. Golf work deferred until Eames is in place.
  R2 brief merged; disagreement entry exists; no further golf work
  until Eames lands. Sync on KB and golf after Eames.
- Mesh Memory API questions to Liz (open since 12 Jun).
- Ray/Liz availability on shared skills (open since April).
- Routing of A2A messages (Node.js v12.18.3 blocks modern SDK).
- IDENTITY drift guard — created 24 Jun, awaiting first scheduled cron run.
- **Vigil handoff to Liz** — 25 Jun 2026. All open Vigil items transferred
  to her purview (router credentials, scope, Hermes verification, agency
  subagent outcomes).

---

*Curated by Woodhouse. First drafted 24 June 2026. Do not load in
shared/group contexts.*
