import speech_recognition as sr
import tempfile
import os

def transcribe_audio(audio_bytes):
    """
    Transcribes audio bytes (e.g., from Streamlit st.audio_input) to text
    using Google's Speech Recognition API.
    """
    recognizer = sr.Recognizer()
    
    # Save bytes to a temporary wav file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file.flush()
        tmp_file_path = tmp_file.name

    try:
        with sr.AudioFile(tmp_file_path) as source:
            # Read the audio file
            audio_data = recognizer.record(source)
            # Transcribe using Google's free API
            text = recognizer.recognize_google(audio_data)
            return text
    except sr.UnknownValueError:
        return "Speech Recognition could not understand the audio."
    except sr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"
    except Exception as e:
        return f"Error processing audio: {str(e)}"
    finally:
        # Clean up temp file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path) 
