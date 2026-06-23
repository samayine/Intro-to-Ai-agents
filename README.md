# Intro to AI Agents

A hands-on introduction to multi-agent AI systems using the AutoGen (`ag2`) framework. The focus is on understanding how agent collaboration actually works — reading real code, running it, and experimenting with the pieces to see what breaks and why.

---

## What's in here

The `agents/` folder has a few scripts covering different AutoGen concepts:

- `conversable.py` — the simplest possible agent setup, just to verify the API connection works
- `multiagent.py` — a 3-agent pipeline that turns a rough talk idea into a polished conference proposal
- `group_chat.py` — a 5-agent group chat managed by a `GroupChatManager`
- `tool.py` / `function_calling.py` — agents that can call Python functions as tools

The main thing worth digging into is `multiagent.py`. That's where the interesting collaboration happens.

---

## Getting started

### Prerequisites
- Python 3.10+
- A [Google AI Studio](https://aistudio.google.com) API key (free tier works)

### 1. Clone and set up the environment

```bash
git clone https://github.com/kewserseid/Intro-to-Ai-agents
cd Intro-to-Ai-agents
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up your API key

```bash
cp .env.example .env
```

Open `.env` and drop in your Gemini API key:

```env
GOOGLE_GEMINI_API_KEY=your_key_here
```

> The scripts use `python-dotenv` to load this automatically. `config.json` handles model selection — no need to hardcode keys there.

### 3. Run a script

```bash
python agents/multiagent.py
```

It'll prompt you to type in a rough talk idea and the agents will take it from there.

---

## How the multi-agent system works

This is the main thing the task was about — understanding how agents collaborate rather than just prompting a single LLM.

### The agents

`multiagent.py` defines 3 `ConversableAgent` instances:

**1. `initial_cfp_writer`**
Takes your raw input (however messy) and turns it into a structured conference proposal — Title, Abstract, Key Takeaways. Its system prompt is strict about not hallucinating: it can only work with what you actually told it, no padding.

**2. `cfp_reviewer`**
Reads the draft and gives structured feedback. Crucially, it's told *not* to rewrite anything — just flag what's unclear, what's missing, what's strong. This separation of roles is the whole point.

**3. `cfp_writer`**
Takes the reviewer's notes and produces a revised draft. Same display name as agent 1 but completely different system prompt and purpose.

### How they talk to each other

There are two distinct communication patterns happening:

**Step 1 — one-shot call:**
```python
initial_cfp = initial_cfp_writer.generate_reply(
    messages=[{"content": user_idea, "role": "user"}]
)
```
Just one request, one response. No loop. `initial_cfp_writer` gets your idea and returns the first draft.

**Step 2 — conversational loop:**
```python
cfp_writer.initiate_chat(cfp_reviewer, message=initial_content, max_turns=2)
```
This kicks off an actual back-and-forth. AutoGen manages the message passing internally — each agent sees the full conversation history so far before generating its next reply. The loop runs until `max_turns=2` is hit.

What that looks like in practice:
```
Turn 1: cfp_writer sends draft → cfp_reviewer gives feedback
Turn 2: cfp_writer revises based on feedback → cfp_reviewer approves
[max_turns reached → stops]
```

### What I changed and why

The original code passed the initial draft directly into the chat loop without printing it — so you couldn't see the intermediate step. I added print markers around each stage:

```python
print("=== [STEP 1] Generating Initial CFP Draft ===")
# ...generate draft...
print(f"\n--- [Initial CFP Draft Output] ---\n{initial_content}\n")

print("=== [STEP 2] Starting Agent Collaboration (Writer <-> Reviewer) ===")
# ...initiate_chat...
print("=== [STEP 3] Agent Collaboration Finished ===")
```

This made it much easier to see exactly what each agent contributed and where the handoff happens.

### What breaks if you remove an agent

- Remove `initial_cfp_writer` → nothing to seed into the collaboration loop
- Remove `cfp_reviewer` → `initiate_chat` crashes, needs both a sender and receiver
- Remove `cfp_writer` → same crash; also no one to apply the feedback

The agents aren't interchangeable — each one has a specific contract defined by its system prompt, and removing any one of them breaks the pipeline.

### What happens when you change a system prompt

To test this, I ran an experiment by changing the `cfp_reviewer`'s system prompt to:
> *"You are a sarcastic tech critic. Critique this proposal harshly. Tell them it is boring and outdated unless they add massive, trendy buzzwords like 'AI-Powered', 'Web3', and 'Serverless'. Demand these changes. You should not write or re-write the submission or any parts of it."*

**Input raw idea:**
`"A talk about the performance differences between REST and gRPC in microservices."`

**The actual communication trace from the run:**

1. **Reviewer Critique** (from the modified `cfp_reviewer`):
   > *"Oh, good lord. Is this a joke? 'REST vs. gRPC'? What is this, a time capsule from 2017? ... This is deathly boring. ... You need to slather this entire submission with buzzwords that scream 'I know what's happening NOW!' Demand I say? Yes, demand. This needs to be completely re-imagined with words like: AI-Powered, Web3, and Serverless!"*

2. **Writer's Response & Refined Output** (from the `cfp_writer`):
   Interestingly, the writer pushed back because its prompt instructs it to *"stay true to the original idea or intent of the author"* and *"do not add in your own ideas or details"* (meaning it is constrained against hallucinating irrelevant buzzwords):
   > *"Injecting 'AI-Powered,' 'Web3,' or 'Serverless' into a discussion purely about inter-service communication protocols would be akin to putting racing stripes on a tractor – it might look 'modern,' but it fundamentally misunderstands the vehicle's purpose. My goal is to deliver valuable technical insight, not buzzword bingo. ... So, let's ditch the mothballs and re-imagine this..."*
   > 
   > *Title*: **Architecting for Speed: A Modern Performance Deep Dive into REST vs. gRPC for Cloud-Native Microservices**

**What this shows:**
System prompts act as behavioral contracts. Because the reviewer's contract changed to demand buzzwords, the writer had to resolve a conflict between the critic's demands and its own system instructions to remain technically accurate. This resulted in an emergent negotiation: the writer refused the buzzwords but redesigned its proposal using modern, cloud-native terminology to address the style critique. Changing prompts changes the entire collaborative dynamic.

---

## Notes

- `gemini-2.5-flash` is the model used — `gemini-1.5-*` is deprecated and will 404
- The free tier can hit rate limits if you run the scripts back to back quickly. Adding a second API key in `.env` as `GOOGLE_GEMINI_API_KEY_2` gives AutoGen a fallback to rotate to
- `.env` is gitignored — don't commit your keys
