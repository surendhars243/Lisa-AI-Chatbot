# Lisa: AI Voice Assistant (Python + Ollama & Google Gemini)

Lisa is a simple, Jarvis-style personal assistant built with Python, **Ollama** (for free, unlimited local AI), and the **Google Gemini API** (for cloud AI).
You can chat with her by typing or by talking, and she can do real tasks on your computer, such as
checking the weather, opening websites and apps, searching YouTube, and saving notes.

> Built as a student project to learn how AI chatbots, APIs and tool calling work.

## Features

- **Dual AI engine:** chat locally & 100% offline using **Ollama** (free, private, unlimited) OR connect to **Google Gemini** in the cloud
- **Tool calling:** both Gemini and Ollama can decide when to run Python functions (time, weather, Wikipedia, web search, system status, and more)
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

- Python 3.9+ (Python 3.11 or 3.12 recommended for pre-built `PyAudio` wheels)
- [Ollama](https://ollama.com/) for local, private, and offline language models (e.g., Llama 3.2, Mistral, Qwen)
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

### 4. Configure your `.env` file

1. Copy `.env.example` to create your own `.env` file:

   ```bash
   # Windows
   copy .env.example .env

   # macOS / Linux
   cp .env.example .env
   ```

2. Open `.env` and set your preferred AI engine:
   - **For Google Gemini (Cloud):**
     Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey) and set:
     ```env
     LLM_PROVIDER=gemini
     GEMINI_API_KEY=your_real_key_here
     GEMINI_MODEL=gemini-3.5-flash
     ```
   - **For Ollama (Local & Offline):**
     No API key needed! Set:
     ```env
     LLM_PROVIDER=ollama
     OLLAMA_MODEL=llama3.2
     ```

> [!NOTE]
> **Never commit `.env` or share your key.** It is already listed in `.gitignore`. Even when using Ollama, you can optionally provide a `GEMINI_API_KEY` to enable real-time Google web search tool calling.

### 5. Install and Set up Ollama (for Local AI)

If you chose Ollama for free, unlimited, and offline conversation:

Step 1: Install Ollama
Go to https://ollama.com and download the Windows installer.
Run it and finish the installation. Ollama then runs in the background, and you’ll see its icon in the taskbar tray.
Step 2: Download a model

Open a terminal and run:

ollama pull llama3.2

This downloads about 2 GB, so it needs some time and disk space. It works on most laptops with 8 GB RAM. If your PC is old or slow, use the smaller llama3.2:1b instead, and set that name in .env later.

Step 3: Test the model alone
ollama run llama3.2

Type hello. If it answers, Ollama works. Type /bye to leave.

Step 4: Install the Python package

In your project terminal, with (venv) showing:

pip install -U ollama

### 6. Run

```bash
python lisa.py                 # text chat
python lisa.py --speak         # you type, Lisa speaks
python lisa.py --voice         # full voice conversation
python lisa.py --voice --wake  # reacts only when you say "Lisa ..."
```

Type `exit` (or say "goodbye") to quit.

## Ollama Guide (Local & Offline AI)

Ollama allows Lisa to run powerful Large Language Models directly on your machine without needing an internet connection for chat or paying for API usage.

### 1. Install Ollama

- **Windows / macOS:** Download the one-click installer from [ollama.com/download](https://ollama.com/download) and run it.
- **Linux:** Run in terminal:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

### 2. Pull an AI Model

Once Ollama is installed and running, open your command prompt / terminal and pull a model:

```bash
ollama pull llama3.2
```

### 3. Recommended Models for Lisa

| Model Tag              | Download Size | Minimum RAM | Notes                                                                               |
| :--------------------- | :------------ | :---------- | :---------------------------------------------------------------------------------- |
| `llama3.2` _(Default)_ | ~2.0 GB       | 4 GB        | Fast, intelligent, handles tool calling smoothly. Recommended for most PCs/laptops. |
| `llama3.2:1b`          | ~1.3 GB       | 2 GB        | Super lightweight; ideal for older machines or low-RAM environments.                |
| `mistral` (7B)         | ~4.1 GB       | 8 GB        | Higher reasoning quality and very strong general knowledge.                         |
| `qwen2.5:3b`           | ~2.0 GB       | 4 GB        | Excellent multilingual support and tool reasoning.                                  |
| `deepseek-r1:1.5b`     | ~1.1 GB       | 2 GB        | Lightweight reasoning model.                                                        |

### 4. Useful Ollama Commands

- **List all downloaded models:**
  ```bash
  ollama list
  ```
- **Test the model in your terminal:**
  ```bash
  ollama run llama3.2
  ```
- **Remove a model to free disk space:**
  ```bash
  ollama rm llama3.2
  ```
- **Switching models in Lisa:**
  After pulling any model (e.g. `ollama pull mistral`), update `.env`:
  ```env
  OLLAMA_MODEL=mistral
  ```

---

## Configuration (`.env`)

| Variable         | Meaning                                                 | Default            |
| :--------------- | :------------------------------------------------------ | :----------------- |
| `LLM_PROVIDER`   | Which AI engine to use: `ollama` or `gemini`            | `gemini`           |
| `OLLAMA_MODEL`   | Ollama model tag to chat with                           | `llama3.2`         |
| `GEMINI_API_KEY` | Your Gemini API key (required if `LLM_PROVIDER=gemini`) | none               |
| `GEMINI_MODEL`   | Gemini model name                                       | `gemini-3.5-flash` |
| `USER_NAME`      | The name Lisa calls you                                 | `Boss`             |
| `VOICE_LANG`     | Language for speech recognition                         | `en-IN`            |
| `VOICE_INDEX`    | Which installed voice Lisa speaks with                  | `0`                |
| `VOICE_RATE`     | Speaking speed (about 150 slow, 200 fast)               | `175`              |

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

| Problem                                       | Fix                                                                                                               |
| :-------------------------------------------- | :---------------------------------------------------------------------------------------------------------------- |
| `Cannot reach Ollama`                         | Make sure the Ollama application is launched and running in the background. On Linux, run `ollama serve`.         |
| `The model is missing`                        | The model has not been pulled yet. Run `ollama pull <model_name>` (e.g. `ollama pull llama3.2`) in your terminal. |
| `GEMINI_API_KEY missing`                      | Make sure `.env` exists in the project root with `GEMINI_API_KEY=...` when using `LLM_PROVIDER=gemini`.           |
| Model not found (404)                         | In `.env`, set `GEMINI_MODEL=gemini-2.5-flash` or check your `OLLAMA_MODEL` name.                                 |
| API key not valid (400)                       | Re-copy the key from Google AI Studio with no extra spaces or quotes.                                             |
| Quota exceeded (429)                          | Gemini daily quota reached. Switch to local offline mode by setting `LLM_PROVIDER=ollama` in `.env`.              |
| `ModuleNotFoundError`                         | Activate your virtual environment and run `pip install -r requirements.txt`.                                      |
| `PyAudio` install fails (`portaudio.h` error) | Python 3.14 lacks pre-built wheels. Use **Python 3.11 or 3.12**, or omit `PyAudio` if you only need text chat.    |
| Lisa never hears me                           | Check your default microphone in system sound settings.                                                           |
| PowerShell blocks `activate`                  | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once in an admin PowerShell window.                     |

## Roadmap

- [ ] More natural voice (Gemini TTS or edge-tts)
- [ ] Web interface with Streamlit
- [ ] Answer questions from PDFs (RAG)
- [ ] Email, reminders and to-do tools

## Author

Made by **Surendhar** ([@surendhars243](https://github.com/surendhars243))

## License

Add a license of your choice (for example MIT) if you want others to reuse this project.
