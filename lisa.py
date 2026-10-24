"""
LISA: a simple Jarvis-style AI assistant powered by Google Gemini.

Features
  * Chat with a local Ollama model (unlimited, offline) OR Google Gemini
    (choose with LLM_PROVIDER in .env)
  * Gemini can use "tools": time, weather, Wikipedia, web search that answers
    in the chat, open websites/apps, YouTube/Google in the browser, notes,
    system status
  * Optional voice mode (speech-to-text + text-to-speech)

Run:
  python lisa.py                 # text chat
  python lisa.py --speak         # text input, spoken replies
  python lisa.py --voice         # full voice mode (mic + speaker)
  python lisa.py --voice --wake  # only reacts when you say "Lisa ..."
"""

import argparse
import datetime
import json
import os
import platform
import re
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

import psutil
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Optional voice libraries -------------------------------------------------
try:
    import ollama
except ImportError:
    ollama = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

# Configuration ------------------------------------------------------------
load_dotenv()

# Which AI answers your chat: "ollama" (local, unlimited) or "gemini" (cloud, daily quota)
PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

API_KEY = os.getenv("GEMINI_API_KEY")  # needed for provider=gemini and for web search
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
USER_NAME = os.getenv("USER_NAME", "Boss")
VOICE_LANG = os.getenv("VOICE_LANG", "en-IN")
VOICE_INDEX = int(os.getenv("VOICE_INDEX", "0"))
VOICE_RATE = int(os.getenv("VOICE_RATE", "175"))

# Speech recognition often spells the name differently, so accept a few.
WAKE_WORDS = ("lisa", "liza", "leesa", "lyza")
WAKE_PATTERN = re.compile(r"\b(" + "|".join(WAKE_WORDS) + r")\b", re.IGNORECASE)

# Change this to whatever you want Lisa to say after "Good morning, <name>."
GREETING_TAIL = "Lisa online and ready."

NOTES_FILE = Path(__file__).with_name("notes.json")
HTTP_HEADERS = {"User-Agent": "LisaAssistant/1.0 (student project)"}

SYSTEM_PROMPT = f"""
You are LISA, a smart, polite and slightly witty personal AI assistant.
The user's name is {USER_NAME}; address them naturally (use their name or "sir/madam" sparingly).

Rules:
- Keep answers short and conversational (1-4 sentences) unless the user asks for detail.
- Do not use markdown, bullet symbols or emojis; your replies may be spoken aloud.
- Answer general knowledge questions directly from your own knowledge.
- For news, recent events, prices, scores or anything that may have changed, use the search_and_answer tool if you have it, and reply with the answer in the chat. If you do not have it, say you cannot check live information.
- Use search_google ONLY when the user explicitly says to search or open something in Google. Never open the browser otherwise.
- Use the other tools for time/date, weather, Wikipedia facts, opening websites or apps, YouTube, notes and system status.
- Never invent real-time data. If a tool fails, say so honestly.
- If a request is unclear, ask one short clarifying question.
""".strip()


# =========================================================================
# TOOLS (Gemini decides when to call these; docstrings + type hints matter!)
# =========================================================================
def get_current_datetime() -> str:
    """Get the current local date, day of the week and time."""
    now = datetime.datetime.now()
    return now.strftime("%A, %d %B %Y, %I:%M %p")


def get_weather(city: str) -> str:
    """Get the current weather for a city, for example 'Chennai' or 'London'.

    Args:
        city: Name of the city.
    """
    try:
        r = requests.get(
            f"https://wttr.in/{city}",
            params={"format": "%l: %C, %t (feels like %f), humidity %h, wind %w"},
            headers=HTTP_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        return r.text.strip()
    except requests.RequestException as e:
        return f"Could not fetch weather: {e}"


def wikipedia_summary(topic: str) -> str:
    """Look up a short factual summary of a topic, person or place on Wikipedia.

    Args:
        topic: The subject to look up, e.g. 'Alan Turing'.
    """
    try:
        search = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "opensearch", "search": topic, "limit": 1, "format": "json"},
            headers=HTTP_HEADERS,
            timeout=10,
        ).json()
        if not search[1]:
            return f"No Wikipedia article found for '{topic}'."
        title = search[1][0]
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}",
            headers=HTTP_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("extract", "No summary available.")
    except (requests.RequestException, ValueError, IndexError) as e:
        return f"Wikipedia lookup failed: {e}"


def search_and_answer(query: str) -> str:
    """Search the web for up-to-date information and return the answer.
    Use this for news, recent events, scores, prices, or any fact that may have changed.
    The answer is shown in the chat; it does NOT open a browser.

    Args:
        query: What to look up.
    """
    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model=MODEL,
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        return response.text or "I couldn't find anything on that."
    except Exception:
        return "Web search is unavailable right now (quota or network problem)."


def open_website(url: str) -> str:
    """Open a website in the default web browser.

    Args:
        url: The website address, e.g. 'youtube.com' or 'https://github.com'.
    """
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def search_google(query: str) -> str:
    """Open the Google results page in the web browser.
    Use this ONLY when the user explicitly asks to search or open something in Google,
    for example 'search this in google'. Never use it to answer questions.

    Args:
        query: What to search for.
    """
    webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
    return f"Showing Google results for '{query}'."


def play_on_youtube(query: str) -> str:
    """Search YouTube for a song or video and open the results in the browser.

    Args:
        query: Song or video name to search for.
    """
    webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
    return f"Showing YouTube results for '{query}'."


# Only apps in this allow-list can be launched (safety!). Add your own below.
APPS = {
    "windows": {
        "notepad": "notepad", "calculator": "calc", "paint": "mspaint",
        "file explorer": "explorer", "command prompt": "cmd",
        "chrome": "chrome", "vs code": "code",
    },
    "darwin": {
        "calculator": "Calculator", "notes": "Notes", "safari": "Safari",
        "chrome": "Google Chrome", "terminal": "Terminal", "vs code": "Visual Studio Code",
    },
    "linux": {
        "calculator": "gnome-calculator", "terminal": "gnome-terminal",
        "files": "nautilus", "chrome": "google-chrome", "vs code": "code",
        "text editor": "gedit",
    },
}


def open_application(app_name: str) -> str:
    """Open a desktop application such as calculator, notepad, chrome, vs code or terminal.

    Args:
        app_name: Name of the application to open.
    """
    system = platform.system().lower()
    apps = APPS.get(system, {})
    key = app_name.lower().strip()
    if key not in apps:
        return f"I'm not allowed to open '{app_name}'. Available: {', '.join(apps) or 'none'}."
    target = apps[key]
    try:
        if system == "windows":
            subprocess.Popen(f'start "" {target}', shell=True)  # target is from allow-list
        elif system == "darwin":
            subprocess.Popen(["open", "-a", target])
        else:
            subprocess.Popen([target])
        return f"Opening {app_name}."
    except OSError as e:
        return f"Could not open {app_name}: {e}"


def add_note(text: str) -> str:
    """Save a note or reminder for the user.

    Args:
        text: The content of the note.
    """
    notes = _load_notes()
    notes.append({"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "text": text})
    NOTES_FILE.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")
    return "Note saved."


def read_notes() -> str:
    """Read back all the notes the user has saved."""
    notes = _load_notes()
    if not notes:
        return "There are no saved notes."
    return "\n".join(f"{i}. [{n['time']}] {n['text']}" for i, n in enumerate(notes, 1))


def _load_notes() -> list:
    if NOTES_FILE.exists():
        try:
            return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def get_system_status() -> str:
    """Get the computer's current CPU usage, memory usage and battery level."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    text = f"CPU usage {cpu}%, memory usage {ram}%"
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    if battery:
        plugged = "charging" if battery.power_plugged else "on battery"
        text += f", battery {battery.percent:.0f}% ({plugged})"
    return text


TOOLS = [
    get_current_datetime, get_weather, wikipedia_summary, open_website,
    search_google, play_on_youtube, open_application,
    add_note, read_notes, get_system_status,
]
# Web search uses Gemini, so it is only offered when a Gemini key exists.
if API_KEY:
    TOOLS.append(search_and_answer)

TOOL_MAP = {fn.__name__: fn for fn in TOOLS}


# =========================================================================
# VOICE (optional)
# =========================================================================
class Voice:
    """Text-to-speech (pyttsx3) and speech-to-text (SpeechRecognition)."""

    def __init__(self, want_listen: bool):
        self.recognizer = None
        self.mic = None

        if pyttsx3 is None:
            print("[!] pyttsx3 not installed -> replies will not be spoken.")

        if want_listen:
            if sr is None:
                sys.exit("Voice input needs: pip install SpeechRecognition PyAudio")
            self.recognizer = sr.Recognizer()
            self.recognizer.pause_threshold = 0.8        # seconds of silence = you finished
            self.recognizer.dynamic_energy_threshold = True
            self.mic = sr.Microphone()
            with self.mic as source:
                print("Calibrating microphone... stay quiet for a second.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def speak(self, text: str) -> None:
        """Speak text. A fresh engine is created each time, because reusing one
        engine makes pyttsx3 go silent after the first message on Windows."""
        if pyttsx3 is None:
            return
        clean = re.sub(r"[*_`#>]", "", text)
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", VOICE_RATE)
            voices = engine.getProperty("voices")
            if 0 <= VOICE_INDEX < len(voices):
                engine.setProperty("voice", voices[VOICE_INDEX].id)
            engine.say(clean)
            engine.runAndWait()
            engine.stop()
            del engine
        except Exception as e:
            print(f"[!] Could not speak: {e}")

    def listen(self) -> str:
        """Listen once and return the recognised text ('' if nothing heard)."""
        with self.mic as source:
            try:
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
            except sr.WaitTimeoutError:
                return ""
        try:
            return self.recognizer.recognize_google(audio, language=VOICE_LANG)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"[!] Speech service error: {e}")
            return ""


# =========================================================================
# CHAT
# =========================================================================
class OllamaChat:
    """Chat with a local Ollama model, running our Python tools when it asks."""

    def __init__(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _trim(self) -> None:
        """Keep the history short so a small model stays fast."""
        rest = self.messages[1:][-20:]
        while rest and not (isinstance(rest[0], dict) and rest[0].get("role") == "user"):
            rest.pop(0)
        self.messages = [self.messages[0]] + rest

    def send(self, text: str) -> str:
        self.messages.append({"role": "user", "content": text})
        for _ in range(4):  # at most a few tool rounds per message
            response = ollama.chat(model=OLLAMA_MODEL, messages=self.messages, tools=TOOLS)
            message = response.message
            self.messages.append(message)
            if not message.tool_calls:
                self._trim()
                return (message.content or "").strip()
            for call in message.tool_calls:
                name = call.function.name
                args = call.function.arguments or {}
                func = TOOL_MAP.get(name)
                try:
                    result = func(**args) if func else f"Unknown tool: {name}"
                except Exception as e:
                    result = f"Tool error: {e}"
                self.messages.append({"role": "tool", "tool_name": name, "content": str(result)})
        self._trim()
        return "Sorry, I couldn't finish that request."


def create_chat(client):
    """Create a chat session for the chosen provider (history is kept automatically)."""
    if PROVIDER == "ollama":
        return OllamaChat()
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=TOOLS,  # the SDK runs the matching Python function automatically
        temperature=0.7,
    )
    return client.chats.create(model=MODEL, config=config)


def ask(chat, text: str) -> str:
    try:
        if isinstance(chat, OllamaChat):
            return chat.send(text) or "I'm sorry, I couldn't come up with a reply."
        response = chat.send_message(text)
        return (response.text or "").strip() or "I'm sorry, I couldn't come up with a reply."
    except Exception as e:
        message = str(e)
        lowered = message.lower()
        if "429" in message or "RESOURCE_EXHAUSTED" in message:
            return ("I've reached today's free Gemini limit. Try again later, "
                    "or set LLM_PROVIDER=ollama in the .env file.")
        if PROVIDER == "ollama":
            if "connect" in lowered or "refused" in lowered:
                return "I can't reach Ollama. Please open the Ollama app and try again."
            if "not found" in lowered:
                return f"The model is missing. Run this in a terminal: ollama pull {OLLAMA_MODEL}"
        return "Sorry, I had trouble thinking about that. Please try again."


def greeting() -> str:
    hour = datetime.datetime.now().hour
    part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    return f"Good {part}, {USER_NAME}. {GREETING_TAIL}"


def main() -> None:
    parser = argparse.ArgumentParser(description="LISA assistant")
    parser.add_argument("--voice", action="store_true", help="use microphone + speaker")
    parser.add_argument("--speak", action="store_true", help="speak replies (keyboard input)")
    parser.add_argument("--wake", action="store_true", help="in voice mode, require the wake word")
    args = parser.parse_args()

    if PROVIDER not in ("ollama", "gemini"):
        sys.exit("LLM_PROVIDER must be 'ollama' or 'gemini' (check your .env file).")

    if PROVIDER == "gemini" and not API_KEY:
        sys.exit("GEMINI_API_KEY missing. Copy .env.example to .env and add your key.")

    if PROVIDER == "ollama":
        if ollama is None:
            sys.exit("Ollama support needs: pip install ollama")
        try:
            ollama.list()  # is the Ollama app running?
        except Exception:
            sys.exit("Cannot reach Ollama. Install it from https://ollama.com and open the app.")

    client = genai.Client(api_key=API_KEY) if API_KEY else None
    chat = create_chat(client)
    voice = Voice(want_listen=args.voice) if (args.voice or args.speak) else None

    hello = greeting()
    brain = f"Ollama ({OLLAMA_MODEL})" if PROVIDER == "ollama" else f"Gemini ({MODEL})"
    print(f"\n[Brain: {brain}]")
    print(f"LISA: {hello}")
    print("(type 'reset' to clear memory, 'exit' to quit)\n")
    if voice:
        voice.speak(hello)

    while True:
        # ---- get user input ----
        if args.voice:
            print("Listening...")
            user_text = voice.listen()
            if not user_text:
                continue
            print(f"You: {user_text}")

            if args.wake:
                if not WAKE_PATTERN.search(user_text):
                    print("(Ignored. Start with 'Lisa', for example: 'Lisa, what time is it?')")
                    continue
                user_text = WAKE_PATTERN.sub("", user_text, count=1).strip(" ,.")
                if not user_text:  # you only said her name
                    print("LISA: Yes?")
                    voice.speak("Yes?")
                    print("Listening for your command...")
                    user_text = voice.listen()
                    if not user_text:
                        continue
                    print(f"You: {user_text}")
        else:
            try:
                user_text = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nLISA: Goodbye!")
                break
            if not user_text:
                continue

        # ---- built-in commands ----
        lowered = user_text.lower().strip(" .!")
        if lowered in {"exit", "quit", "bye", "goodbye", "stop", "shutdown"}:
            bye = f"Goodbye, {USER_NAME}. Shutting down."
            print(f"LISA: {bye}")
            if voice:
                voice.speak(bye)
            break
        if lowered in {"reset", "clear", "forget everything"}:
            chat = create_chat(client)
            print("LISA: Memory cleared.")
            if voice:
                voice.speak("Memory cleared.")
            continue

        # ---- ask Gemini ----
        reply = ask(chat, user_text)
        print(f"LISA: {reply}\n")
        if voice:
            voice.speak(reply)


if __name__ == "__main__":
    main()
