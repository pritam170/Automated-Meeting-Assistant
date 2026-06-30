# Automated-Meeting-Assistant
AuraMeet is an automated, local-first meeting assistant that transcribes meeting audio, extracts action items and summaries, and emails structured task lists to team members. It uses a Python backend (Flask) and a state-of-the-art Vanilla CSS/HTML/JS frontend. It requires no external API keys and runs completely locally using lightweight, open-source models (Whisper for audio transcription, and a hybrid extractive/abstractive NLP system for summarization and action items).

User Review Required
IMPORTANT

Python Environment: Since Python is not currently installed or configured on the system, we will install Python 3.11 via winget as part of the setup.

SMTP Email Credentials: To send emails, the user will need to configure an SMTP server (e.g., Gmail with an App Password, Mailtrap for testing, or any company SMTP). SMTP configuration will be securely saveable in a local config.json file.

Open Questions
No open questions. The user's prompt is fully addressed by a local-first architecture that handles audio/text transcripts, summarizes meetings, tracks tasks, and sends automated emails without API keys.

Proposed Changes
Backend (Python / Flask)
We will build a modular Flask application.

Server (app.py): Defines routes for uploading audio/text, running analysis, saving/loading configurations, and sending emails.
Transcription (transcriber.py): Uses openai-whisper (running the tiny or base model locally on CPU) to transcribe audio files.
Analyzer (analyzer.py):
Summarizer: Implements an extractive summarizer using sentence tokenization, TF-IDF / PageRank scoring (no API key needed, extremely fast). Offers an optional integration with Hugging Face transformers (using t5-small or distilbart-cnn-12-6) for abstractive summaries if the user installs optional packages.
Action Item Extractor: Parses transcripts using rule-based grammar and semantic regex to extract tasks, identify assignees (matching names from the Team Directory), and detect deadlines (e.g., "by tomorrow", "by Friday").
Mailer (mailer.py): Uses Python's built-in smtplib and email.mime to format and send professional HTML emails with specific action items.
[NEW] 
app.py
The main entry point for the Flask server. Exposes:

POST /api/upload: Handles audio file upload and triggers transcription.
POST /api/analyze-text: Accepts raw text or pasted transcript and runs summary/action item extraction.
GET /api/config and POST /api/config: Manages SMTP and Whisper settings.
GET /api/team and POST /api/team: Manages team members (names and emails).
POST /api/send-emails: Accepts a list of confirmed action items and emails them to the corresponding assignees.
[NEW] 
transcriber.py
Module to handle local audio transcription. Uses a background thread to update the client via a simple status flag or progress indicator.

Automatically downloads and uses the Whisper tiny or base model.
Includes a fallback message if the audio packages (whisper, torch, ffmpeg) are missing, instructing the user how to install them.
[NEW] 
analyzer.py
NLP engine for summarization and action-item parsing:

Extracts structural speakers (e.g. Alice: I will do X).
Performs sentence-level scoring for summary generation.
Uses pattern matching for action verbs and indicator phrases to pull actionable items.
[NEW] 
mailer.py
Builds beautiful HTML emails containing:

Meeting title and date.
Meeting summary.
The recipient's specific action items (highlighted in gold/neon-blue).
The overall meeting task list for visibility.
Frontend (HTML / CSS / JS)
We will build a high-fidelity, single-page dashboard app.

index.html: Structured semantic markup containing tabs for Dashboard, Audio Upload, Team Directory, and SMTP Settings.
style.css: Premium glassmorphism design system using modern typography (Outfit / Inter), gradients, translucent panels (backdrop-filter: blur), responsive grid layout, and sleek interactive hover/active states.
app.js: Handles tab navigation, file upload (with drag-and-drop animations), API interactions with the backend, dynamic rendering of summaries and editable task lists, and sending emails.
[NEW] 
index.html
The template of our single-page application. Includes:

A navigation sidebar or header.
Main dashboard showing recent transcripts and summaries.
Interactive upload card for audio or raw text.
Contacts/Team and Settings panels.
[NEW] 
style.css
The core design stylesheet. Implementing:

A deep violet-blue dark mode palette.
Glassmorphism effects with borders and subtle box-shadows.
Animations for files dragging over, loading spinners, and success checkmarks.
[NEW] 
app.js
State management and page logic.

Implements dynamic additions/deletions of tasks and team members.
Sends SMTP settings and test emails.
Verification Plan
Automated Tests
We will write a python script verify_backend.py to:

Test the analyzer offline with a sample transcript to verify that:
The meeting summary is successfully generated.
Action items are correctly extracted with matching assignees.
Test the mailer using a mock SMTP server or validation check.
Manual Verification
Launch the Flask backend on localhost (default: http://127.0.0.1:5000).
Open the web browser and verify:
Visual aesthetics (glassmorphic layout, fonts, colors, responsive tabs).
Pasting a sample meeting transcript, clicking "Analyze", and verifying the generated summary and editable action item list.
Adding team members in the "Team Directory" tab.
Configuring SMTP settings and testing the email dispatch.
