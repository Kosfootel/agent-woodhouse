# Golf Tee Time Caller Agent - POC Summary & Technology Recommendations

**Project:** Automated Golf Course Tee Time Inquiry System  
**Date:** June 15, 2026  
**Status:** POC Planning Phase - Awaiting Collaboration from Ray & Liz

---

## Executive Summary

We are building a voice-enabled AI agent that makes outbound calls to golf courses, asks about tee time availability, engages in natural conversation with humans, and extracts structured booking data. The system will operate on a schedule, handle retry logic, and notify users of results.

### Success Criteria
- Make successful calls to 80%+ of contacted courses
- Extract useful availability data from 60%+ of conversations
- Cost per call under $0.50 (ideally under $0.25)
- Natural conversation latency under 2 seconds per turn

---

## Three Technology Paths Evaluated

### Path A: Commercial All-in-One (Fastest to Market)

**Stack:** Vapi.ai or Bland.ai

| Component | Solution | Cost/Call |
|-----------|----------|-----------|
| Voice + AI | Vapi.ai | $0.05-0.09/min |
| LLM | Included | - |
| STT | Included | - |
| TTS | Included | - |
| **Total (5 min call)** | | **$0.25-0.45** |

**Pros:**
- Single API integration
- Built-in conversation management
- Fastest implementation (days, not weeks)
- Pre-optimized voice quality

**Cons:**
- Highest per-call cost
- Vendor lock-in
- Limited customization
- Rate limits at scale

**Best For:** Proof of concept, validating demand, <100 calls/month

**Timeline:** 1-2 weeks to first working call

---

### Path B: Hybrid API + Local (Recommended Balance)

**Stack:** Twilio + OpenAI + Local caching

| Component | Solution | Cost/Call |
|-----------|----------|-----------|
| Voice Transport | Twilio | $0.013/min |
| STT | OpenAI Whisper | $0.006/min |
| TTS | OpenAI TTS | $0.015/min |
| LLM | GPT-4o-mini | ~$0.01/call |
| **Total (5 min call)** | | **$0.15-0.20** |

**Pros:**
- Mature, reliable infrastructure
- Granular control over conversation flow
- Easy to swap components
- Good observability/debugging

**Cons:**
- Requires more integration work
- Still has API dependencies
- Latency can vary

**Best For:** Production use, predictable costs, customization needs

**Timeline:** 3-4 weeks to production-ready

---

### Path C: Ollama-Centric Local (Lowest Cost)

**Stack:** Twilio + Ollama LLM + Local STT/TTS

| Component | Solution | Cost/Call |
|-----------|----------|-----------|
| Voice Transport | Twilio | $0.013/min |
| STT | faster-whisper (local) | $0 |
| TTS | Piper (local) | $0 |
| LLM | llama3.2/qwen2.5 (Ollama) | $0 |
| **Total (5 min call)** | | **$0.07-0.10** |

**Pros:**
- Lowest ongoing cost (70% savings vs Path B)
- Full privacy - no audio leaves local network
- No API rate limits
- Complete customization

**Cons:**
- Requires GPU (RTX 3060 12GB+ or equivalent)
- Higher initial setup complexity
- Responsible for all optimizations
- Single point of failure (your hardware)

**Best For:** High volume (200+ calls/month), privacy requirements, technical team

**Timeline:** 4-6 weeks to production-ready

---

## Comparative Analysis

| Factor | Path A (Vapi) | Path B (Hybrid) | Path C (Ollama) |
|--------|---------------|-------------------|-----------------|
| **Setup Time** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Per-Call Cost** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Voice Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Customization** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Scalability** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Privacy** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Operational Complexity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Vendor Lock-in** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Theoretical Builds

### Build A: Vapi.ai Quickstart (Path A)

```python
# golf_caller_vapi.py
import vapi
from datetime import datetime, timedelta

class GolfCallerVapi:
    def __init__(self, api_key):
        self.client = vapi.Vapi(api_key=api_key)
        
    def create_assistant(self):
        """Configure voice assistant with golf-specific behavior"""
        assistant = self.client.assistants.create(
            name="Golf Tee Time Assistant",
            model="gpt-4o-mini",
            voice="joshua",  # Professional male voice
            first_message=(
                "Hi, I'm calling about tee time availability. "
                "Do you have any openings for this Friday around 10 AM?"
            ),
            system_prompt="""
            You are a polite golf enthusiast calling to inquire about tee times.
            
            RULES:
            - Ask about specific dates and times
            - Extract: available slots, prices, player limits
            - If they say no, ask about nearby alternatives
            - Keep conversation under 3 minutes
            - Thank them and end politely
            
            Always confirm what you heard before ending.
            """
        )
        return assistant
    
    def schedule_call(self, course_phone: str, date: str):
        """Queue call to specific course"""
        call = self.client.calls.create(
            phone_number=course_phone,
            assistant_id=self.assistant.id,
            scheduled_at=datetime.now() + timedelta(minutes=5)
        )
        return call
```

**Infrastructure:**
- Vapi.ai account
- Phone number (Vapi provides)
- Simple webhook for results

**Cost at 100 calls/month:** ~$35

---

### Build B: Twilio + OpenAI Hybrid (Path B)

```python
# golf_caller_hybrid.py
from fastapi import FastAPI, WebSocket
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
import json

app = FastAPI()
openai = OpenAI()

class GolfConversationManager:
    def __init__(self):
        self.active_calls = {}
        
    async def handle_incoming_audio(self, call_sid: str, audio_stream):
        """Process audio from Twilio, return AI response"""
        
        # 1. Transcribe with Whisper
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_stream
        )
        
        # 2. Generate response with GPT-4o-mini
        messages = self.get_conversation_history(call_sid)
        messages.append({"role": "user", "content": transcript.text})
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "You are a golf tee time assistant..."
            }] + messages
        )
        
        ai_text = response.choices[0].message.content
        
        # 3. Convert to speech
        speech = openai.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=ai_text
        )
        
        # 4. Update conversation state
        self.update_history(call_sid, transcript.text, ai_text)
        
        return speech.content
    
    def extract_availability(self, call_sid: str) -> dict:
        """Parse conversation for structured data"""
        history = self.get_conversation_history(call_sid)
        
        extraction = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "Extract tee time availability data from this conversation..."
            }, {
                "role": "user", 
                "content": json.dumps(history)
            }]
        )
        
        return json.loads(extraction.choices[0].message.content)

@app.post("/voice/webhook")
async def voice_webhook(request):
    """Twilio webhook for call events"""
    response = VoiceResponse()
    response.connect().stream(url="wss://your-server/websocket")
    return response
```

**Infrastructure:**
- Twilio account + phone number
- FastAPI server (can be local with ngrok for testing)
- OpenAI API key
- PostgreSQL for conversation storage

**Cost at 100 calls/month:** ~$18

---

### Build C: Ollama Local Stack (Path C)

```python
# golf_caller_ollama.py
import ollama
from faster_whisper import WhisperModel
import piper_tts
from fastapi import FastAPI, WebSocket
import numpy as np

app = FastAPI()

class LocalGolfAgent:
    def __init__(self):
        # Local models - no API calls
        self.whisper = WhisperModel("base", device="cpu")  # or "cuda"
        self.tts = piper_tts.Voice("en_US-lessac-medium")
        self.model = "llama3.2"  # or "qwen2.5", "phi4"
        
    async def process_turn(self, audio_bytes: bytes, call_context: dict):
        """Full local processing pipeline"""
        
        # 1. Speech-to-Text (local Whisper)
        segments, _ = self.whisper.transcribe(audio_bytes)
        human_text = " ".join([s.text for s in segments])
        print(f"Human: {human_text}")
        
        # 2. LLM Response (Ollama)
        messages = call_context.get('history', [])
        messages.append({"role": "user", "content": human_text})
        
        response = ollama.chat(
            model=self.model,
            messages=[{
                "role": "system",
                "content": """You are a golf tee time assistant. Be concise and natural.
                
                Current goal: Ask about tee times for {date}.
                Previous context: {context}
                
                Respond in 1-2 sentences. Ask one clear question at a time."""
            }] + messages,
            options={'temperature': 0.7}
        )
        
        ai_text = response['message']['content']
        print(f"AI: {ai_text}")
        
        # 3. Text-to-Speech (Piper - local)
        audio_response = self.tts.synthesize(ai_text)
        
        # Update context
        messages.append({"role": "assistant", "content": ai_text})
        call_context['history'] = messages
        
        return audio_response, call_context
    
    def extract_results(self, call_context: dict) -> dict:
        """Extract structured data from conversation"""
        
        history = call_context.get('history', [])
        transcript = "\n".join([
            f"{'Human' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in history
        ])
        
        extraction = ollama.generate(
            model=self.model,
            prompt=f"""Extract tee time availability from this conversation:
            
{transcript}

Return JSON:
{{
    "available_dates": ["YYYY-MM-DD"],
    "available_times": ["HH:MM"],
    "price_per_player": number or null,
    "player_limit": number or null,
    "notes": "string",
    "booking_phone": "string or null",
    "success": true/false
}}

Only return valid JSON."""
        )
        
        return json.loads(extraction['response'])
```

**Infrastructure:**
- Local GPU machine (RTX 3060 12GB+ or M1/M2 Pro with 16GB+)
- Twilio account (just for PSTN connectivity)
- FastAPI server
- Ollama installed with models pulled
- Piper TTS downloaded

**Cost at 100 calls/month:** ~$9 (just Twilio voice)

---

## Decision Matrix

| If you need... | Choose Path |
|----------------|-------------|
| Demo in 1 week | **A - Vapi.ai** |
| Production in 1 month, <100 calls/mo | **B - Hybrid** |
| Production in 2 months, 200+ calls/mo | **C - Ollama** |
| Lowest possible cost | **C - Ollama** |
| No hardware management | **A or B** |
| Full privacy / no cloud AI | **C - Ollama** |
| Easiest debugging | **B - Hybrid** |
| Minimal code | **A - Vapi.ai** |

---

## Recommended Approach: Phased Rollout

### Phase 1: Validate with Path A (Week 1-2)
- Build Vapi prototype
- Test with 5-10 golf courses
- Validate conversation quality
- Refine prompt engineering

### Phase 2: Evaluate Economics (Week 3)
- Calculate actual per-call costs
- Project monthly spend
- If >$50/month and >100 calls, proceed to Phase 3

### Phase 3: Migrate to Path B or C (Week 4-8)
- **Path B** if cost acceptable, want reliability
- **Path C** if cost-sensitive, have GPU, want control

---

## Open Questions for Ray & Liz

### Technical Architecture
1. Do we have GPU resources available for Path C?
2. What's our target monthly call volume (10? 100? 1000)?
3. Is call latency critical (sub-second vs 2-second ok)?
4. Do we need real-time monitoring/dashboards?

### Operational
5. Should this run on a schedule (cron) or on-demand?
6. Preferred notification method (email, Telegram, app)?
7. How do we get the golf course list (manual entry, scraping, API)?
8. What timezone handling needed?

### Conversation Design
9. Should the agent identify itself as AI or use a persona?
10. How aggressive should retry logic be (3 attempts? 5?)?
11. What happens when transferred to human at course?
12. Should we support multiple languages?

### Data & Integration
13. Need calendar integration (Google/Outlook)?
14. Auto-book if slot available, or just report?
15. How long to store call recordings/transcripts?
16. Any compliance requirements (TCPA, call recording laws)?

---

## Success Metrics & Testing Plan

### Week 1-2: Prototype Validation
- [ ] Make 10 successful calls
- [ ] Achieve 60%+ data extraction rate
- [ ] Voice quality rated "natural" by 3+ humans
- [ ] Latency under 3 seconds per turn

### Week 3-4: Production Readiness
- [ ] Handle 50 calls without errors
- [ ] Retry logic working (max 3 attempts)
- [ ] Data structured and storable
- [ ] Notifications delivered reliably

### Month 2: Scale Test
- [ ] 100+ calls in one week
- [ ] Cost per call under target
- [ ] <5% call failure rate
- [ ] User satisfaction >4/5

---

## Files Created

1. `research/golf-tee-time-caller-2026-06-15.md` - Full tool comparison
2. `plans/golf-tee-time-caller-POC.md` - POC planning document
3. `projects/golf-caller/POC-SUMMARY-AND-RECOMMENDATIONS.md` - This file

---

## Next Steps

1. **Await feedback from Ray & Liz** on technology path preference
2. **Answer open questions** above
3. **Select path** and write detailed requirements
4. **Begin POC implementation** (target: working demo in 2 weeks)

---

*Prepared by Woodhouse for Mr. Ross*  
*Ready for Ray & Liz collaboration phase*
