# Golf Tee Time Caller Agent - POC Plan

## Project: Automated Golf Course Tee Time Inquiry System

### Objective
Create a voice-enabled AI agent that can:
- Make outbound phone calls to golf courses
- Ask about tee times and availability on specific dates
- Handle dynamic human responses
- Extract and structure booking information
- Report results back

---

## Phase 1: Research & Tool Selection (In Progress)

See subagent report at: `agent-woodhouse/research/golf-tee-time-caller-YYYY-MM-DD.md`

Key considerations:
- **Latency**: Natural conversation requires <500ms response time
- **Cost**: Per-minute pricing vs flat-rate options
- **Voice Quality**: Human-like vs robotic affects success rate
- **Integration**: WebSocket vs HTTP, callback handling

---

## Phase 2: Core Workflows

### Workflow A: Outbound Call Initiation
```
1. Schedule trigger (cron or manual)
2. Load golf course list from database
3. Queue calls with rate limiting (avoid overwhelming courses)
4. Initiate voice call via API
5. Handle connection / voicemail detection
```

### Workflow B: Conversation Flow
```
1. Greeting + intent statement
   "Hi, I'm calling to ask about tee time availability..."

2. Ask specific question (date, time range, players)
   "Do you have any openings for Friday, June 20th around 10 AM?"

3. Handle responses:
   - YES with details → Extract time, price, conditions
   - NO / booked → Ask about alternatives
   - QUESTIONS → Answer common queries
   - TRANSFER → Handle human handoff

4. Confirmation & wrap-up
5. Store results
```

### Workflow C: Data Extraction & Reporting
```
1. Parse conversation transcript
2. Extract structured data:
   - Course name
   - Date requested
   - Available times (if any)
   - Pricing
   - Restrictions (cart rules, dress code)
3. Update booking database
4. Generate summary report
5. Send notification to user
```

---

## Phase 3: Technical Architecture

### Recommended Stack (TBD based on research)

**Option A: Commercial APIs (Fastest setup)**
- Voice: Vapi.ai or Bland.ai (built for AI voice agents)
- LLM: Claude/OpenAI for conversation handling
- Orchestration: OpenClaw agent with custom skill

**Option B: Open Source (Lower cost, more control)**
- Voice: Twilio + Pipecat (open-source voice framework)
- STT: Whisper (local or API)
- TTS: ElevenLabs or open alternatives
- LLM: Local model via Ollama

**Option C: Hybrid (Balance)**
- Voice: Twilio (reliable, pay-per-minute)
- AI layer: Custom WebSocket handling + LLM

---

## Phase 4: POC Implementation

### MVP Features
1. Single golf course hardcoded
2. One specific date inquiry
3. Simple conversation (3-5 exchanges max)
4. Email/SMS result notification

### Success Metrics
- Call completion rate >80%
- Successful information extraction >60%
- Cost per call <$0.50
- Latency <2 seconds per response

---

## Phase 5: Future Enhancements

- Multi-course scheduling
- Calendar integration (auto-book if available)
- Preferences learning (favorite times, courses)
- SMS fallback
- Real-time dashboard

---

## Files to Create

1. `research/golf-tee-time-caller-tools.md` - Tool comparison (subagent)
2. `specs/golf-caller-architecture.md` - Technical design
3. `poc/vapi-integration/` or `poc/twilio-integration/` - Working code
4. `skills/golf-caller/SKILL.md` - Reusable OpenClaw skill

---

## Open Questions

1. Which voice API to prioritize? (Waiting on research)
2. Should this be a scheduled cron job or on-demand?
3. Golf course list source? (User provided, scraped, API?)
4. Preferred notification method? (Email, Telegram, app?)
5. Need calendar integration for auto-booking?

---

## Status

- [ ] Research complete
- [ ] Tool selection finalized
- [ ] POC architecture defined
- [ ] Working demo created
- [ ] Documentation committed

---

*Created: 2026-06-15*
*Owner: Woodhouse for Mr. Ross*
