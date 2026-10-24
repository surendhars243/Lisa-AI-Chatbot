"""
LISA-Lite: a simple LISA-style AI assistant powered by Google Gemini.

Features
  * Chat with Gemini (remembers the conversation)
  * Gemini can use "tools": time, weather, Wikipedia, open websites/apps,
    YouTube/Google search, notes, system status
  * Optional voice mode (speech-to-text + text-to-speech)

Run:
  python lisa.py              # text chat
  python lisa.py --speak      # text input, spoken replies
  python lisa.py --voice      # full voice mode (mic + speaker)
  python lisa.py --voice --wake   # only reacts when you say "Lisa ..."
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
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

# Configuration ------------------------------------------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
USER_NAME = os.getenv("USER_NAME", "Boss")
VOICE_LANG = os.getenv("VOICE_LANG", "en-IN")
WAKE_WORD = "lisa"
NOTES_FILE = Path(__file__).with_name("notes.json")
HTTP_HEADERS = {"User-Agent": "LisaLite/1.0 (student project)"}

SYSTEM_PROMPT = f"""
You are LISA, a smart, polite and slightly witty personal AI assistant.
The user's name is {USER_NAME}; address them naturally (use their name or "sir/madam" sparingly).

Rules:
- Keep answers short and conversational (1-4 sentences) unless the user asks for detail.
- Do not use markdown, bullet symbols or emojis; your replies may be spoken aloud.
- Use the available tools for the current time/date, weather, Wikipedia facts,
  opening websites or apps, searching, notes and system status.
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
    """Search Google for something in the web browser.

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
    search_google, play_on_youtube, open_application, add_note,
    read_notes, get_system_status,
]


# =========================================================================
# VOICE (optional)
# =========================================================================
class Voice:
    """Text-to-speech (pyttsx3) and speech-to-text (SpeechRecognition)."""

    def __init__(self, want_listen: bool):
        self.engine = None
        self.recognizer = None
        self.mic = None

        if pyttsx3:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", int(os.getenv("VOICE_RATE", "175")))
                voices = self.engine.getProperty("voices")
                index = int(os.getenv("VOICE_INDEX", "0"))
                if 0 <= index < len(voices):
                    self.engine.setProperty("voice", voices[index].id)
            except Exception as e:  # missing espeak/driver, etc.
                print(f"[!] Text-to-speech unavailable: {e}")
        else:
            print("[!] pyttsx3 not installed -> replies will not be spoken.")

        if want_listen:
            if sr is None:
                sys.exit("Voice input needs: pip install SpeechRecognition PyAudio")
            self.recognizer = sr.Recognizer()
            self.mic = sr.Microphone()
            with self.mic as source:
                print("Calibrating microphone... stay quiet for a second.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def speak(self, text: str) -> None:
        if not self.engine:
            return
        clean = re.sub(r"[*_`#>]", "", text)
        self.engine.say(clean)
        self.engine.runAndWait()

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
def create_chat(client: genai.Client):
    """Create a Gemini chat session (history is kept automatically)."""
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=TOOLS,  # the SDK runs the matching Python function automatically
        temperature=0.7,
    )
    return client.chats.create(model=MODEL, config=config)


def ask(chat, text: str) -> str:
    try:
        response = chat.send_message(text)
        return (response.text or "").strip() or "I'm sorry, I couldn't come up with a reply."
    except Exception as e:
        return f"Sorry, I had trouble reaching Gemini: {e}"


def greeting() -> str:
    hour = datetime.datetime.now().hour
    part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    return f"Good {part}, {USER_NAME}. Lisa is here...How can i help you dear."


def main() -> None:
    parser = argparse.ArgumentParser(description="LISA-Lite assistant")
    parser.add_argument("--voice", action="store_true", help="use microphone + speaker")
    parser.add_argument("--speak", action="store_true", help="speak replies (keyboard input)")
    parser.add_argument("--wake", action="store_true", help="in voice mode, require the wake word")
    args = parser.parse_args()

    if not API_KEY:
        sys.exit("GEMINI_API_KEY missing. Copy .env.example to .env and add your key.")

    client = genai.Client(api_key=API_KEY)
    chat = create_chat(client)
    voice = Voice(want_listen=args.voice) if (args.voice or args.speak) else None

    hello = greeting()
    print(f"\nLISA: {hello}")
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
                if WAKE_WORD not in user_text.lower():
                    continue
                user_text = re.sub(WAKE_WORD, "", user_text, flags=re.IGNORECASE).strip(" ,.") or "Yes?"
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
