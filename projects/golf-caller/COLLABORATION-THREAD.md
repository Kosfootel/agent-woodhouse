# Golf Caller Project - Collaboration Thread

**Project:** Automated Golf Course Tee Time Caller Agent  
**Date:** June 15, 2026  
**Status:** POC Planning - Awaiting Ray & Liz Input  

---

## 📋 For Ray and Liz

Hello! I've completed the POC summary and technology recommendations. **Your input is needed** on several key questions before we can write final requirements and begin implementation.

### Quick Links
- **Full Analysis:** `POC-SUMMARY-AND-RECOMMENDATIONS.md`
- **Tool Research:** `../../research/golf-tee-time-caller-2026-06-15.md`
- **POC Plan:** `../../plans/golf-tee-time-caller-POC.md`

### Technology Paths Summary

| Path | Stack | Cost/Call | Timeline | Best For |
|------|-------|-----------|----------|----------|
| **A** | Vapi.ai (commercial) | $0.25-0.45 | 1-2 weeks | Fastest demo |
| **B** | Twilio + OpenAI | $0.15-0.20 | 3-4 weeks | Balanced reliability |
| **C** | Twilio + Ollama local | $0.07-0.10 | 4-6 weeks | Lowest cost, high volume |

**Woodhouse Recommendation:** Start with Path A to validate quickly, then migrate to B or C based on actual volume and cost projections.

---

## ❓ Open Questions (Need Your Input)

### Technical Architecture
1. **GPU Resources**
   - Do we have GPU hardware available for Path C (local Ollama)?
   - Minimum: RTX 3060 12GB or M1/M2 Pro with 16GB
   - If not, Path B (Hybrid) is recommended

2. **Call Volume**
   - What's the expected monthly call volume?
   - <50 calls/month: Path A viable
   - 50-200 calls/month: Path B recommended
   - >200 calls/month: Path C justifies setup cost

3. **Latency Requirements**
   - Is sub-second response critical?
   - Or is 1-2 second latency acceptable?
   - Path C (local) has more variable latency

4. **Real-time Monitoring**
   - Do we need dashboards/live call monitoring?
   - Or is post-call reporting sufficient?

### Operational
5. **Triggering**
   - Schedule-based (cron, daily at 9am)?
   - On-demand (user initiates)?
   - Event-driven (weather check, calendar sync)?

6. **Golf Course Data**
   - Manual entry of course phone numbers?
   - Scraped from web?
   - API integration (if available)?

7. **Notifications**
   - Email results?
   - Telegram/Slack message?
   - Push notification to app?
   - Dashboard only?

8. **Calendar Integration**
   - Just report availability (user books manually)?
   - Or auto-book if slot found (needs calendar auth)?

### Conversation Design
9. **AI Transparency**
   - Should agent identify itself as AI?
   - Or use human-like persona?

10. **Retry Logic**
    - How many attempts per course (busy/no answer)?
    - Spread across how many hours?

11. **Human Handoff**
    - What if course wants to transfer to human?
    - Leave callback number or hang up?

12. **Multi-language**
    - English only for now?
    - Need Spanish/other language support?

---

## 💬 Reply Template

Please reply below with your thoughts. Copy this template:

```
**From:** [Your name]
**Date:** [Today's date]

### Technology Path Preference
[A / B / C] - [Brief reasoning]

### Question Answers
1. GPU: [Yes/No, specs if yes]
2. Volume: [Estimated calls/month]
3. Latency: [Sub-second / 1-2s acceptable]
4. Monitoring: [Dashboard needed Y/N]
5. Triggering: [Schedule/On-demand/Event]
6. Course data: [Manual/Scraped/API]
7. Notifications: [Email/Telegram/Other]
8. Calendar: [Report only / Auto-book]
9. AI ID: [Reveal AI / Human persona]
10. Retries: [# of attempts]
11. Handoff: [Callback/Hangup]
12. Language: [English/Other]

### Additional Thoughts
[Your other ideas, concerns, suggestions]
```

---

## ✅ Current Status

- [x] Tool research completed
- [x] Three paths analyzed
- [x] Cost projections calculated
- [x] Theoretical builds drafted
- [x] Collaboration thread created
- [ ] **Awaiting Ray input**
- [ ] **Awaiting Liz input**
- [ ] Consolidate feedback
- [ ] Write final requirements
- [ ] Begin POC implementation

---

## 📁 Project Files

```
agent-woodhouse/
├── research/
│   └── golf-tee-time-caller-2026-06-15.md    # Tool comparison
├── plans/
│   └── golf-tee-time-caller-POC.md           # Planning document
└── projects/golf-caller/
    ├── POC-SUMMARY-AND-RECOMMENDATIONS.md    # This analysis
    └── COLLABORATION-THREAD.md             # This file
```

---

*Please reply with your input so we can proceed to requirements and implementation.*

**@Ray @Liz** - Your thoughts?

---

## Replies

<!-- Ray and Liz: Please add your replies below -->

