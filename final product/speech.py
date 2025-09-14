import os, asyncio, pygame, edge_tts, threading, re, queue, tempfile
from dotenv import dotenv_values

# Load voice setting
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-JennyNeural")

# Global playback queue & flags
speech_queue = queue.Queue()
speech_stop_flag = threading.Event()  # controls TTS
player_lock = threading.Lock()

def split_text(text, max_len=250):
    """Split text into smaller chunks for playback."""
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) < max_len:
            current += " " + s
        else:
            chunks.append(current.strip())
            current = s
    if current:
        chunks.append(current.strip())
    return chunks

async def gen_tts(part, file_path):
    """Generate MP3 for a text chunk."""
    communicate = edge_tts.Communicate(text=part, voice=AssistantVoice)
    await communicate.save(file_path)

def _player_loop():
    """Background loop that plays speech chunks sequentially."""
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    while True:
        part = speech_queue.get()
        if part is None:
            break

        with player_lock:
            if speech_stop_flag.is_set():
                continue

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                file_path = tmp.name

            try:
                asyncio.run(gen_tts(part, file_path))

                if speech_stop_flag.is_set():
                    os.remove(file_path)
                    continue

                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                print("[TTS] Speaking:", part[:60])

                while pygame.mixer.music.get_busy():
                    if speech_stop_flag.is_set():
                        pygame.mixer.music.stop()
                        break
                    pygame.time.Clock().tick(20)

            except Exception as e:
                print("TTS Error:", e)
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

# Start background player thread
threading.Thread(target=_player_loop, daemon=True).start()

def text_to_speech(text):
    """Queue text for speech. Stops old playback immediately."""
    # Stop old TTS only, don't affect voice input
    stop_speech()
    for chunk in split_text(text):
        speech_queue.put(chunk)

def stop_speech():
    """Stop current playback & clear TTS queue instantly."""
    speech_stop_flag.set()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except:
        pass

    # fully drain queue
    while not speech_queue.empty():
        try:
            speech_queue.get_nowait()
        except queue.Empty:
            break

    speech_stop_flag.clear()
