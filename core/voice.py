import speech_recognition as sr

def transcribe_audio(file_path: str) -> str:
    """Transcribe audio file to text using SpeechRecognition."""
    r = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Speech recognition service failed"
