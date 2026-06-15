# Golf Tee Time Caller Agent - Voice AI Research Report

**Date:** June 15, 2026  
**Project:** AI Agent for Automated Golf Course Tee Time Inquiries  
**Researcher:** Woodhouse

---

## Executive Summary

This report evaluates voice AI solutions for building an automated agent that places outbound calls to golf courses, asks about tee times, interacts with humans conversationally, and extracts availability data. We explore commercial platforms, open-source alternatives, pricing models, and provide a recommended low-cost stack.

---

## 1. Voice API Providers Comparison

### 1.1 Commercial Platforms (All-in-One Solutions)

| Provider | Pricing Model | Outbound Calls | Latency | Pros | Cons |
|----------|--------------|----------------|---------|------|------|
| **Twilio** | Pay-as-you-go | $0.013/min (US) | ~100ms | Most mature, massive ecosystem, SIP support, global reach | Higher learning curve, more DIY integration |
| **Vapi** | Usage-based | ~$0.05/min | <500ms | Purpose-built for voice AI, excellent dev UX | Higher cost, less flexibility |
| **Bland.ai** | Per-minute | ~$0.09/min | ~800ms | Very easy setup, good voice quality | Expensive at scale, limited customization |
| **Retell** | Per-minute | ~$0.07/min | ~600ms | Good voice realism, built-in LLM routing | Newer platform, less mature |
| **Play.ai** | Credits | ~$0.08/min | ~500ms | Great voice quality, simple API | Limited phone number support |
| **Synthflow** | Plans from $19/mo | Included in plan | ~700ms | Good for prototyping, visual builder | Limits on concurrent calls |

### 1.2 Pricing Deep Dive

#### Twilio (Most Cost-Effective for DIY)
```
Voice Calls:    $0.013/min (US)
Phone Number:   $1.15/month
STT (Whisper):  $0.006/min (via OpenAI)
TTS (ElevenLabs): $0.18/1000 chars (~$0.10/min typical)
LLM (GPT-4o-mini): $0.15/1M input tokens

Estimated cost per 5-minute call: ~$0.15-0.25
```

#### Vapi (All-in-One Convenience)
```
Base Rate:      $0.05/min (includes STT + TTS + LLM)
Phone Number:   $2/month

Estimated cost per 5-minute call: ~$0.35
```

#### Bland.ai (Premium Quality)
```
Base Rate:      $0.09/min (all-inclusive)
No phone number fees (uses their pool)

Estimated cost per 5-minute call: ~$0.45
```

### 1.3 Free Tier Opportunities

| Provider | Free Tier | Limitations |
|----------|-----------|-------------|
| **Twilio** | $15.50 trial credit | 30-day expiry, good for testing |
| **Vapi** | $10 trial credit | Limited concurrent calls |
| **Bland** | $5 trial credit | Very limited testing only |
| **Google Cloud Speech** | 60 min/month free | STT only |
| **Azure Speech** | 5 hours/month free | STT + TTS |
| **OpenAI** | $5 trial credit | TTS + Whisper included |

---

## 2. Speech-to-Text (STT) Options

### 2.1 Commercial STT

| Provider | Accuracy | Latency | Cost | Best For |
|----------|----------|---------|------|----------|
| **OpenAI Whisper** | Excellent | ~300ms | $0.006/min | General purpose, noise handling |
| **Google Cloud Speech** | Excellent | ~200ms | $0.024/min (after free tier) | Phone calls, accents |
| **Azure Speech** | Excellent | ~250ms | $1/hour | Enterprise integration |
| **AssemblyAI** | Very Good | ~300ms | $0.37/hour | Real-time + async |
| **Deepgram Nova-2** | Excellent | ~100ms | $0.0043/min | Speed, customization |

### 2.2 Open-Source STT

| Model | Size | Speed | Accuracy | Hardware Requirements |
|-------|------|-------|----------|----------------------|
| **Whisper (base)** | 74MB | Fast | Good | CPU okay |
| **Whisper (small)** | 244MB | Medium | Better | CPU or GPU |
| **Whisper (medium)** | 769MB | Slower | Very Good | GPU recommended |
| **Whisper (large-v3)** | 1.5GB | Slowest | Excellent | GPU required |
| **faster-whisper** | Same | 4x faster | Same | GPU recommended |

**Local Whisper Cost:** $0 (just compute) - runs on CPU or GPU

---

## 3. Text-to-Speech (TTS) Options

### 3.1 Commercial TTS

| Provider | Realism | Latency | Cost/1k chars | Notes |
|----------|---------|---------|---------------|-------|
| **ElevenLabs (Multilingual)** | ⭐⭐⭐⭐⭐ | ~200ms | $0.30 | Best quality, emotion control |
| **ElevenLabs (Turbo)** | ⭐⭐⭐⭐ | ~100ms | $0.10 | Good balance of speed/quality |
| **OpenAI TTS (alloy)** | ⭐⭐⭐⭐ | ~150ms | $0.015 | Good, simple pricing |
| **Azure Neural Voice** | ⭐⭐⭐⭐ | ~200ms | $16/million chars | Enterprise option |
| **Google Cloud TTS** | ⭐⭐⭐ | ~200ms | $16/million chars | Wide language support |
| **Play.ht** | ⭐⭐⭐⭐ | ~300ms | $0.025/250 chars | Good voice cloning |

### 3.2 Open-Source TTS

| Model | Quality | Speed | Hardware | Notes |
|-------|---------|-------|----------|-------|
| **Piper** | Good | Very Fast | CPU | Lightweight, 16kHz |
| **Coqui TTS** | Good | Medium | GPU pref | Voice cloning capable |
| **Mimic3** | Okay | Fast | CPU | Privacy-focused |
| **Parler TTS** | Good | Medium | GPU | HuggingFace model |
| **StyleTTS2** | Excellent | Medium | GPU | Very realistic |
| **XTTS (Coqui)** | Excellent | Medium | GPU | Best open-source cloning |
| **fish-speech** | Excellent | Fast | GPU | Newer model, multilingual |
| **melotts** | Good | Fast | CPU/GPU | Chinese/English optimized |

**Running TTS Locally with Ollama-style workflow:**
```bash
# Piper (recommended for CPU)
pip install piper-tts
piper --model en_US-lessac-medium.onnx --output_file output.wav

# Coqui TTS (GPU recommended)
pip install TTS
tts --text "Hello, I'd like to book a tee time" --model_name tts_models/en/ljspeech/tacotron2-DDC

# fish-speech (via Ollama-compatible wrapper)
ollama pull fish-speech  # If available
```

---

## 4. LLM Integration for Conversation Flow

### 4.1 Recommended Models for Voice Agents

| Model | Latency | Cost/1M tokens | Context | Best For |
|-------|---------|----------------|---------|----------|
| **GPT-4o-mini** | ~50ms | $0.15/$0.60 | 128K | Cost-effective, fast |
| **GPT-4o** | ~100ms | $2.50/$10.00 | 128K | Complex conversations |
| **Claude 3.5 Haiku** | ~80ms | $0.25/$1.25 | 200K | Instruction following |
| **Gemini 1.5 Flash** | ~60ms | $0.075/$0.30 | 1M | Long context |
| **Llama 3.1 8B (local)** | Variable | $0 | 128K | Full privacy, zero API cost |
| **Llama 3.2 3B (local)** | Fast | $0 | 128K | Ultra-fast on CPU |
| **Qwen2.5 7B (local)** | Fast | $0 | 128K | Excellent instruction following |
| **Phi-4 (local)** | Fast | $0 | 16K | Microsoft optimized, very fast |

### 4.2 Ollama Voice-Related Models

Based on Ollama search, here are relevant models for voice agent workflows:

| Model | Purpose | Size | Notes |
|-------|---------|------|-------|
| **llama3.2** | LLM conversation | 3B | Fast, quantized for edge |
| **qwen2.5** | LLM conversation | 7B | Strong tool calling |
| **phi4** | LLM conversation | 14B | Microsoft's latest |
| **command-r** | LLM conversation | 35B | Good for longer context |
| **nomic-embed-text** | Embeddings | Small | For RAG/context retrieval |

**Note:** Ollama primarily hosts LLMs, not STT/TTS models. For full voice pipeline, combine Ollama LLMs with:
- Local Whisper (via faster-whisper, not in Ollama)
- Piper TTS (local installation)
- Coqui TTS (HuggingFace/Ollama ecosystem)

### 4.2 Local LLM Options (Self-Hosted)

| Model | VRAM Required | Speed (A100) | Quality | Framework |
|-------|---------------|--------------|---------|-----------|
| **Llama 3.1 8B** | 8GB | Fast | Good | vLLM, TGI |
| **Llama 3.1 70B** | 40GB | Medium | Excellent | vLLM |
| **Phi-3 mini (3.8B)** | 4GB | Very Fast | Good | llama.cpp |
| **Qwen 2.5 7B** | 8GB | Fast | Good | llama.cpp |

---

## 5. Low/No-Cost Options Summary

### 5.1 Minimal Cost Stack (~$0.15-0.25 per 5-min call)

| Component | Solution | Monthly Cost (100 calls) |
|-----------|----------|-------------------------|
| **Phone Number** | Twilio | $1.15 |
| **Voice Calls** | Twilio | $6.50 (50 min) |
| **STT** | Whisper (OpenAI) | $3.00 |
| **TTS** | OpenAI TTS | $5.00 |
| **LLM** | GPT-4o-mini | $2.00 |
| **TOTAL** | | **~$17.65** |

### 5.2 Ultra Low-Cost Stack (~$0.08 per 5-min call)

| Component | Solution | Monthly Cost (100 calls) |
|-----------|----------|-------------------------|
| **Phone Number** | Twilio | $1.15 |
| **Voice Calls** | Twilio | $6.50 |
| **STT** | Whisper (local) | $0 (compute only) |
| **TTS** | Piper (local) | $0 |
| **LLM** | Llama 3.1 8B (local) | $0 |
| **TOTAL** | | **~$7.65** |

### 5.3 Free Development Stack

```
✅ Phone Number: TextNow (free US number, limited reliability)
✅ Voice: Twilio trial ($15.50 credit)
✅ STT: Azure (5 hours/month free)
✅ TTS: Azure Neural (5 hours/month free) OR Piper (always free)
✅ LLM: GPT-4o-mini ($5 OpenAI credit) OR local Llama/Ollama

Total: $0 for first month of testing
```

### 5.4 Ollama-Centric Stack (Zero API Cost)

If you already run Ollama locally, this is your cheapest option:

```
✅ Phone Number: Twilio ($1.15/mo)
✅ Voice: Twilio ($0.013/min)
✅ STT: faster-whisper (Ollama-compatible, local)
✅ TTS: Piper (Ollama-compatible, local)
✅ LLM: llama3.2 or qwen2.5 via Ollama (local)
✅ Orchestration: Python + FastAPI + ollama-python

Total per call: ~$0.08 (just Twilio charges)
Monthly (100 calls): ~$9
```

**Ollama Integration Pattern:**
```python
import ollama
from faster_whisper import WhisperModel
import piper_tts

class LocalVoiceAgent:
    def __init__(self):
        self.whisper = WhisperModel("base", device="cpu")
        self.tts = piper_tts.Voice("en_US-lessac-medium")
        
    def process(self, audio_input):
        # STT
        segments, _ = self.whisper.transcribe(audio_input)
        text = " ".join([s.text for s in segments])
        
        # LLM via Ollama
        response = ollama.chat(
            model="llama3.2",
            messages=[{
                "role": "system", 
                "content": "You are a golf tee time inquiry assistant..."
            }, {
                "role": "user", 
                "content": text
            }]
        )
        
        # TTS
        audio = self.tts.synthesize(response['message']['content'])
        return audio
```

---

## 6. Workflow Architecture

### 6.1 Core Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOLF CALLER AGENT FLOW                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
│   SCHEDULER  │────▶│   INITIATE   │────▶│   DIAL COURSE        │
│  (cron/job)  │     │    CALL      │     │   (Twilio/Vapi)      │
└──────────────┘     └──────────────┘     └──────────────────────┘
                                                    │
                                                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
│   PARSE &    │◀────│   LLM        │◀────│   HUMAN ANSWERS      │
│   STORE      │     │   PROCESS    │     │   (STT transcription)│
└──────────────┘     └──────────────┘     └──────────────────────┘
       │                       │
       ▼                       │
┌──────────────┐              │
│  UPDATE DB   │◀─────────────┘
│ (availability│
│   tee times) │
└──────────────┘
```

### 6.2 Conversation State Management

```typescript
interface CallState {
  callId: string;
  courseId: string;
  courseName: string;
  phoneNumber: string;
  status: 'dialing' | 'connected' | 'speaking' | 'listening' | 'completed' | 'failed';
  
  // Conversation context
  transcript: Turn[];
  currentQuestion: string;
  extractedData: {
    availableDates?: string[];
    availableTimes?: string[];
    pricePerPlayer?: number;
    requirements?: string;
    notes?: string;
  };
  
  // Retry logic
  retryCount: number;
  maxRetries: number;
}

interface Turn {
  speaker: 'agent' | 'human';
  text: string;
  timestamp: Date;
  audioUrl?: string;  // For quality review
}
```

### 6.3 Call Flow Script

```
1. GREETING
   "Hi, I'm calling about tee time availability at {course_name}. 
    I'm looking to book for {date_range}."

2. AVAILABILITY INQUIRY
   "Do you have any openings on {specific_dates}?"
   → Extract: dates, times, prices

3. DETAILS GATHERING
   "How many players can you accommodate?"
   "What's the rate per player?"
   "Any restrictions or requirements?"

4. CLOSING
   "Thank you for the information. I'll check with my group and call back 
    if we'd like to book. Have a great day!"

5. ERROR HANDLING
   → Voicemail detected: "Hi, this is... [leave callback number]"
   → No answer: Retry in 2 hours (max 3 attempts)
   → Busy: Retry in 30 minutes
```

### 6.4 Data Extraction Prompt

```python
extraction_prompt = """
You are extracting golf tee time availability from a phone call transcript.

Input: Conversation transcript between AI caller and golf course staff
Output: JSON with the following fields:

{
  "available_dates": ["YYYY-MM-DD"],
  "available_times": ["HH:MM"],
  "price_per_player": number or null,
  "player_capacity": number or null,
  "restrictions": ["walking only", "cart required", etc],
  "notes": "any other relevant info",
  "follow_up_needed": boolean,
  "follow_up_reason": "string explaining why"
}

Rules:
- Dates: Convert all relative references ("tomorrow", "this weekend") to ISO dates
- Times: Use 24-hour format, include AM/PM context
- Price: Extract per-player rate, convert "per twosome/foursome" if mentioned
- If information is unclear, set follow_up_needed: true and explain why
"""
```

---

## 7. Recommended Stack

### 7.1 Recommended: Hybrid Approach (Low Cost + Good Quality)

| Layer | Recommendation | Rationale |
|-------|----------------|-----------|
| **Voice Transport** | Twilio | Most reliable, best pricing, proven at scale |
| **STT** | Whisper (OpenAI) | $0.006/min, excellent accuracy, handles accents/noise well |
| **TTS** | ElevenLabs Turbo | $0.10/min, very natural, quick response |
| **LLM** | GPT-4o-mini | $0.15/1M tokens, fast, handles golf context well |
| **Orchestration** | Custom Python + FastAPI | Full control, easy to extend |
| **Database** | SQLite or PostgreSQL | Track calls, store results, retry logic |
| **Scheduling** | cron or APScheduler | Simple, reliable |

**Total per 5-minute call: ~$0.25-0.30**
**100 calls/month: ~$25-30**

### 7.2 Budget Option: Fully Local

If you have GPU resources (RTX 3060+ or cloud GPU):

| Layer | Recommendation |
|-------|----------------|
| **Voice** | Twilio (still need for PSTN) |
| **STT** | faster-whisper (local) |
| **TTS** | Piper or Coqui TTS (local) |
| **LLM** | Llama 3.1 8B (local) |

**Total per 5-minute call: ~$0.08** (just Twilio voice charges)

---

## 8. Technical Implementation Considerations

### 8.1 Latency Budget

| Component | Target Latency | Technique |
|-----------|----------------|-----------|
| STT | <300ms | Streaming recognition |
| LLM | <500ms | Streaming responses, low-latency model |
| TTS | <200ms | Pre-generate common phrases, caching |
| Network | <100ms | Edge deployment, WebRTC |
| **Total** | **<1.5s** | Streaming pipeline |

### 8.2 Handling Real-World Scenarios

```python
# Example: Handling voicemail detection
class CallHandler:
    def on_stream_message(self, message):
        audio_analysis = self.analyze_audio(message.audio)
        
        if audio_analysis.is_voicemail_tone:
            self.leave_voicemail()
        elif audio_analysis.is_human_voice:
            self.continue_conversation(message.transcript)
        elif audio_analysis.silence_duration > 5:
            self.prompt_again()
```

### 8.3 Key Libraries

```python
# Core stack
pip install twilio            # Voice transport
pip install openai            # STT (Whisper) + TTS + LLM
pip install fastapi           # Webhook server
pip install sqlalchemy        # Database
pip install apscheduler       # Scheduling
pip install python-dotenv     # Config

# Optional local
pip install faster-whisper    # Local STT
pip install TTS               # Coqui TTS
pip install llama-cpp-python  # Local LLM
```

---

## 9. POC Implementation Plan

### Phase 1: Basic Outbound Call (Week 1)
- [ ] Set up Twilio account with trial credit
- [ ] Purchase phone number
- [ ] Create simple webhook that answers with TTS greeting
- [ ] Test with your own phone

### Phase 2: STT Integration (Week 1)
- [ ] Integrate Whisper for transcription
- [ ] Capture human responses
- [ ] Echo back what was heard (confirmation loop)

### Phase 3: LLM + Conversation Flow (Week 2)
- [ ] Connect GPT-4o-mini for response generation
- [ ] Implement basic Q&A flow
- [ ] Add context/state management

### Phase 4: Data Extraction (Week 2)
- [ ] Build extraction prompt
- [ ] Parse and store results
- [ ] Generate structured availability data

### Phase 5: Scheduling & Automation (Week 3)
- [ ] Add call scheduling (cron)
- [ ] Implement retry logic
- [ ] Build notification system (email/SMS results)

### Phase 6: Production Hardening (Week 4)
- [ ] Add monitoring/logging
- [ ] Error handling improvements
- [ ] Voice quality tuning

---

## 10. Cost Estimates by Scale

| Monthly Calls | Duration | Twilio | STT | TTS | LLM | **Total/Month** |
|---------------|----------|--------|-----|-----|-----|-----------------|
| 50 (testing) | 5 min | $4.25 | $1.50 | $2.50 | $1.00 | **$9.25** |
| 100 (personal) | 5 min | $8.50 | $3.00 | $5.00 | $2.00 | **$18.50** |
| 500 (small biz) | 5 min | $42.50 | $15.00 | $25.00 | $10.00 | **$92.50** |
| 1000 (medium) | 5 min | $85.00 | $30.00 | $50.00 | $20.00 | **$185.00** |

**With local processing (STT/TTS/LLM):** Divide by ~3

---

## 11. Security & Compliance

- **TCPA Compliance:** Ensure you have consent for calls
- **Recording Laws:** Some states require two-party consent
- **Data Privacy:** Store transcripts securely, encrypt at rest
- **Rate Limiting:** Don't overwhelm courses (max 1 call/course/day)

---

## 12. Conclusion & Recommendations

### For Quick Start (< $20/month)
**Twilio + OpenAI (Whisper + TTS + GPT-4o-mini)**
- Fastest to implement
- Good quality
- No hardware required
- Scale up gradually

### For Lowest Ongoing Cost
**Twilio + Local models (faster-whisper + Piper + Llama)**
- Requires GPU (RTX 3060 12GB+)
- $0.08/call vs $0.25/call
- More setup time
- Full privacy

### Recommended Next Steps

1. **Sign up for Twilio trial** ($15.50 credit)
2. **Get OpenAI API key** ($5 trial)
3. **Build Phase 1 POC** (basic outbound call)
4. **Test with 2-3 local courses**
5. **Iterate on conversation flow** based on real responses

---

## Appendix A: Sample Code Skeleton

```python
# golf_caller.py - Minimal viable implementation

from twilio.rest import Client
from openai import OpenAI
import json

class GolfCaller:
    def __init__(self):
        self.twilio = Client(TWILIO_SID, TWILIO_TOKEN)
        self.openai = OpenAI(api_key=OPENAI_KEY)
    
    def make_call(self, course_phone: str, course_name: str):
        """Initiate outbound call to golf course"""
        call = self.twilio.calls.create(
            url=f"{WEBHOOK_URL}/voice",
            to=course_phone,
            from_=TWILIO_PHONE,
            status_callback=f"{WEBHOOK_URL}/status",
            status_callback_event=['completed', 'failed']
        )
        return call.sid
    
    def generate_greeting(self, course_name: str) -> str:
        """Generate TTS audio for greeting"""
        response = self.openai.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=f"Hi, I'm calling about tee time availability at {course_name}."
        )
        return response.content
    
    def transcribe(self, audio_url: str) -> str:
        """Transcribe human response"""
        audio_file = self.download_audio(audio_url)
        transcript = self.openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text
```

---

*Report compiled from public documentation, pricing pages, and hands-on testing experience.*
