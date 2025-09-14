import speech_recognition as sr
import threading
from mtranslate import translate
from colorama import Fore, init

init(autoreset=True)

# Translate Hindi to English
def trans_hindi_to_english(txt):
    english_txt = translate(txt, to_language="en")
    return english_txt

# Listening and recognition logic
def listen():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 2.2
    recognizer.non_speaking_duration = 2.2

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print(Fore.LIGHTGREEN_EX + "🎙 Ready! Speak in Hindi...")

        while True:
            try:
                print(Fore.LIGHTGREEN_EX + "I am listening...", end="\r", flush=True)
                audio = recognizer.listen(source, timeout=None)
                print(Fore.LIGHTYELLOW_EX + "Got it, now recognizing...")

                recognized_txt = recognizer.recognize_google(audio, language="hi-IN")

                if recognized_txt:
                    translated_txt = trans_hindi_to_english(recognized_txt)
                    print(Fore.BLUE + "Mr Zeno (English): " + translated_txt)
                else:
                    print("Could not recognize any speech.")

            except sr.UnknownValueError:
                print(Fore.RED + "❌ Sorry, I could not understand the audio.")
            except Exception as e:
                print(Fore.RED + f"⚠️ Error: {e}")

def main():
    # Run listener (single thread is enough)
    listen()

if __name__ == "__main__":
    main()
