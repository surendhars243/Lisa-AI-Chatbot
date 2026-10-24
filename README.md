# Lisa: AI Voice Assistant (Python + Google Gemini)

Lisa is a simple, Jarvis-style personal assistant built with Python and the Google Gemini API.
You can chat with her by typing or by talking, and she can do real tasks on your computer, such as
checking the weather, opening websites and apps, searching YouTube, and saving notes.

> Built as a student project to learn how AI chatbots, APIs and tool calling work.

## Features

- **Smart conversation:** powered by Google Gemini, with memory of the current chat
- **Tool calling:** Gemini decides when to run Python functions (time, weather, Wikipedia and more)
- **Voice mode:** speak to Lisa and hear her reply (speech recognition + text-to-speech)
- **Wake word:** optional "Lisa ..." activation
- **Customizable:** change her name, greeting, voice, speed and personality
- **Safe by design:** apps can only be opened from an allow-list, and API keys stay out of the code

## What Lisa can do

| Ask                                  | What happens                                    |
| ------------------------------------ | ----------------------------------------------- |
| "What time is it?"                   | Reads the current date and time                 |
| "Weather in Chennai"                 | Fetches live weather                            |
| "Who was Alan Turing?"               | Gets a summary from Wikipedia                   |
| "Open YouTube"                       | Opens the website in your browser               |
| "Play lo-fi music on YouTube"        | Opens YouTube search results                    |
| "Search Google for Python tutorials" | Opens Google results                            |
| "Open calculator"                    | Launches an allow-listed app                    |
| "Note: submit assignment on Friday"  | Saves a note, and "read my notes" reads it back |
| "How is my computer doing?"          | Shows CPU, memory and battery status            |
| "Reset"                              | Clears the conversation memory                  |
| "Goodbye"                            | Shuts Lisa down                                 |

## Tech stack

- Python 3.9+ (3.12 recommended for easy PyAudio install)
- [Google Gemini API](https://ai.google.dev/) via the `google-genai` SDK
- `pyttsx3` for text-to-speech, and `SpeechRecognition` + `PyAudio` for voice input
- `requests`, `psutil` and `python-dotenv`

## Project structure

```
Lisa-AI-Chatbot/
├── lisa.py          # main program (chat, tools, voice)
├── requirements.txt   # Python dependencies
├── .env.example       # template for your settings (no real key!)
├── .gitignore         # keeps .env, venv and notes out of Git
└── README.md
```

Your private `.env` file (with the real API key) stays on your computer only.

## Setup

### 1. Clone the project

```bash
git clone https://github.com/surendhars243/Lisa-AI-Chatbot.git
cd Lisa-AI-Chatbot
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `PyAudio` fails to install, remove that line from `requirements.txt`. Text mode works without it.
See the voice notes below.

### 4. Add your API key

1. Get a free key at https://aistudio.google.com/app/apikey
2. Copy `.env.example` to a new file named `.env`
3. Paste your key into `.env`:

```
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-3.5-flash
USER_NAME=Boss
VOICE_LANG=en-IN
VOICE_INDEX=0
VOICE_RATE=175
```

**Never commit `.env` or share your key.** It is already listed in `.gitignore`.

### 5. Run

```bash
python lisa.py                 # text chat
python lisa.py --speak         # you type, Lisa speaks
python lisa.py --voice         # full voice conversation
python lisa.py --voice --wake  # reacts only when you say "Lisa ..."
```

Type `exit` (or say "goodbye") to quit.

## Configuration (`.env`)

| Variable         | Meaning                                   | Default            |
| ---------------- | ----------------------------------------- | ------------------ |
| `GEMINI_API_KEY` | Your Gemini API key (required)            | none               |
| `GEMINI_MODEL`   | Gemini model name                         | `gemini-3.5-flash` |
| `USER_NAME`      | The name Lisa calls you                   | `Boss`             |
| `VOICE_LANG`     | Language for speech recognition           | `en-IN`            |
| `VOICE_INDEX`    | Which installed voice Lisa speaks with    | `0`                |
| `VOICE_RATE`     | Speaking speed (about 150 slow, 200 fast) | `175`              |

### Finding your voice number

```bash
python -c "import pyttsx3; e=pyttsx3.init(); [print(i, v.name) for i, v in enumerate(e.getProperty('voices'))]"
```

Pick the number you like and set it as `VOICE_INDEX` in `.env`.

## Voice mode notes

Voice input needs a working microphone and an internet connection (Google's speech service).

- **Windows:** `pip install pyaudio` (if it fails: `pip install pipwin` then `pipwin install pyaudio`)
- **macOS:** `brew install portaudio` then `pip install pyaudio`
- **Linux:** `sudo apt install portaudio19-dev espeak` then `pip install pyaudio`

## Customize Lisa

- **Name and wake word:** change `LISA` / `Lisa` in `lisa.py` and set `WAKE_WORD = "lisa"`
- **Greeting:** edit the `return` line in the `greeting()` function
- **Personality:** edit `SYSTEM_PROMPT` near the top of `lisa.py`
- **Add apps she can open:** add entries to the `APPS` dictionary
- **Add a new skill:** write a Python function with type hints and a docstring, then add it to the `TOOLS` list. Gemini will call it automatically when it is relevant.

## Security

- The API key is read from the `.env` file and is never written in the code
- `.env`, `venv/` and `notes.json` are excluded by `.gitignore`
- Lisa can only launch apps listed in `APPS`, and cannot run arbitrary commands
- If you ever commit a key by mistake, delete it in Google AI Studio and create a new one

## Troubleshooting

| Problem                      | Fix                                                                                |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| `GEMINI_API_KEY missing`     | Make sure the file is named exactly `.env`, is in the project folder, and is saved |
| Model not found (404)        | Set `GEMINI_MODEL=gemini-2.5-flash` in `.env`                                      |
| API key not valid (400)      | Re-copy the key, with no extra spaces or quotes                                    |
| Quota exceeded (429)         | Wait a minute and try again (free tier limit)                                      |
| `ModuleNotFoundError`        | Activate the virtual environment and run `pip install -r requirements.txt`         |
| Lisa never hears me          | Check the default microphone in your system sound settings                         |
| `PyAudio` install fails      | Skip voice input, or follow the voice mode notes above                             |
| PowerShell blocks `activate` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once                     |

## Roadmap

- [ ] More natural voice (Gemini TTS or edge-tts)
- [ ] Web interface with Streamlit
- [ ] Answer questions from PDFs (RAG)
- [ ] Email, reminders and to-do tools

## Author

Made by **Surendhar** ([@surendhars243](https://github.com/surendhars243))

## License

Add a license of your choice (for example MIT) if you want others to reuse this project.
