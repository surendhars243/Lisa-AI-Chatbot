# JARVIS-Lite (Gemini powered)

A simple Jarvis-style assistant in Python: chats with Google Gemini and can use tools
(time, weather, Wikipedia, open sites/apps, YouTube/Google search, notes, system status).

## Setup
1. Get a free API key: https://aistudio.google.com/app/apikey
2. Create a virtual environment and install packages:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and paste your key into `GEMINI_API_KEY`.

## Run
```
python jarvis.py                 # text chat
python jarvis.py --speak         # you type, Jarvis speaks
python jarvis.py --voice         # talk to Jarvis
python jarvis.py --voice --wake  # only reacts when you say "Jarvis ..."
```

## Voice mode install notes
- Windows: `pip install pyaudio` (if it fails: `pip install pipwin` then `pipwin install pyaudio`)
- macOS: `brew install portaudio` then `pip install pyaudio`
- Linux: `sudo apt install portaudio19-dev espeak` then `pip install pyaudio`

## Try saying
- "What's the weather in Chennai?"
- "Open YouTube and play lo-fi music"
- "Who was Alan Turing?"
- "Open calculator"
- "Note: submit assignment on Friday" / "Read my notes"
- "How is my computer doing?"

## Troubleshooting
- Model not found: set `GEMINI_MODEL=gemini-2.5-flash` in `.env`.
- Never upload your `.env` to GitHub (it is in `.gitignore`).
