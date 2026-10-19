# Cogni-Routine
Cogni-Routine is a Chat-integrated conversational AI that acts as a daily cognitive check-in, passivemonitoring ly brealth parameters through natural chat aain hnd micro-games to aid in the early detection of cognitive decline.
📌 Project Overview

Cogni-Routine is an intelligent, chat-based daily companion designed to revolutionize how we study and monitor cognitive health in adults aged 40 and older.

Traditional cognitive screenings can be stressful, infrequent, and often occur after significant decline has already happened. Research shows that older adults frequently avoid complex medical apps but are highly active and comfortable using simple chat interfaces.

By meeting users where they are—in a familiar, easy-to-use daily chat—Cogni-Routine turns a 3-minute "good morning" checking-in routine into a powerful, non-invasive pattern recognition tool. Through natural conversation (voice and text) and custom brain-teaser games, the platform studies and tracks 5+ crucial cognitive parameters to detect subtle shifts in brain health over time.

⚠️ Important Disclaimer: Cogni-Routine is a Pattern Recognition and Study Tool, NOT a medical diagnostic device. It does not provide medical diagnoses or prescriptions. If persistent anomalies are detected, the system securely notifies family members with a recommendation to seek professional medical advice.

✨ Key Features & User Journey

Natural Chat Check-In: Everyday natural conversations in multiple regional languages using voice or text.

5+ Cognitive Parameters Evaluated: (Self-assessment based on 100+ research papers)

Typing & Writing Dynamics: Micro-analysis of keystroke patterns, hesitation, and backspace frequency.

Logical Reasoning: Conversational prompts that test daily reasoning and logic.

Multi-Tasking & Executive Function: Seamlessly introducing secondary conversational prompts to test distraction recovery.

Acoustic & Voice NLP: Analysing speech latency, hesitation, and vocabulary degradation in voice notes.

Visuospatial & Memory Function: Interactive in-chat games like pattern matching and spatial recall.

Brain Training Games: Customized brain-teasers tailored to the user’s specific daily baseline to stimulate neural pathways (e.g., speech exercises, logic-puzzles, and memory games).

Physician-Grade Reporting: A secure, structured dashboard translating unstructured chat data into actionable insights for doctors to study long-term trends.

Supportive Follow-up: If the AI engine identifies consistent deviations from the user's 30-day baseline, a supportive notification is sent to registered family members, advising them to schedule a check-up.

🛠️ The Technology Stack

Conversation Layer: Custom web-based Chat Application, designed to mimic familiar messaging workflows.

LLM Orchestration: LangChain coupled with 2-3 specialized Large Language Models (e.g., OpenAI/Gemini) to evaluate semantic logic, manage memory checkpoints, and generate safe, engaging conversation.

Audio & Speech Analysis: OpenAI Whisper API for multilingual voice-to-text transcription and measuring speech latency/pauses.

Micro-Analysis Edge Sensing: JavaScript event listeners (onKeyDown) and HTML5 DeviceMotionEvent (gyroscope) to capture typing dynamics and subtle hand tremors.

Data & Back baselines: PostgreSQL & Firebase for secure, longitudinal patterns tracking.

Visuals & Metrics: Recharts/Chart.js for the Clinician & Family Dashboard.

📂 Project Structure

├── client/                 # Frontend React/Next.js chat interface & games
│   ├── public/             # Static assets & custom games visual data
│   ├── src/
│   │   ├── components/     # ChatWindow, AudioRecorder, GameCards, Dashboard
│   │   ├── hooks/          # useKeystrokeDynamics, useGyroscopeTremor
│   │   └── pages/          # Main Chat, Family/Doctor Dashboard, BrainTrain
├── server/                 # Python FastAPI Backend
│   ├── api/                # Speech-to-Text, LLM routing, game state validation
│   ├── models/             # Local scoring algorithms & pattern metrics
│   ├── prompts/            # Complex LLM prompt templates for multi-domain analysis
│   └── database/           # PostgreSQL schematics for historical baseline tracking


🚀 Quick Start & Installation

Prerequisites

Node.js (v18+)

Python (3.9+)

Free API Keys for: OpenAI (or Gemini), Firebase (for live db).

1. Backend Setup

# Clone the repository
git clone https://github.com/yourusername/cogni-routine.git
cd cogni-routine/server

# Install dependencies
pip install -r requirements.txt

# Configure Environment
cp .env.example .env # Add your API keys here

# Run the API
uvicorn main:app --reload


2. Frontend Setup

cd ../client

# Install dependencies
npm install

# Start Development Server
npm run dev


Open http://localhost:3000 to interact with the chat interface.

📊 Evaluation & Clinical Rationale

Rooted in the analysis of over 100 clinical papers on digital biomarkers, our code focuses on everyday digital behaviors:

Keystroke Dynamics: Hesitation patterns and backspace usage are early indicators of motor and focus decline.

Speech Pause Analysis: Measuring millisecond gaps in voice speech (latency) acts as a non-intrusive test for aphasia, commonly seen in early Alzheimer’s.

Dual-Tasking: Conversational interruptions test cognitive flexibility (executive function).

🤝 Contributing

This project was built for a 2026 Innovation Ideathon. Contributions, issue reporting, and feedback are welcome!

Designed to empower older generations with respectful, seamless cognitive care.
