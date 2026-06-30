import os
import sys

# Try to import whisper for audio transcription. If not available, we can fallback to mock/simulated results for demo purposes.
HAS_WHISPER = False
try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    pass

class LocalTranscriber:
    def __init__(self, model_name="tiny"):
        """
        Initialize Whisper transcriber.
        model_name: 'tiny', 'base', 'small', 'medium'
        """
        self.model_name = model_name
        self.model = None

    def load_model(self):
        if not HAS_WHISPER:
            raise ImportError(
                "Whisper library is not installed. To transcribe audio, run:\n"
                "pip install openai-whisper torch\n"
                "Also, ensure 'ffmpeg' is installed and in your system PATH."
            )
        if self.model is None:
            # Loads the model (downloads it locally to ~/.cache/whisper if not already cached)
            self.model = whisper.load_model(self.model_name)

    def transcribe(self, audio_path):
        """
        Transcribes the given audio file path.
        Returns the transcript text or raises error.
        """
        if not HAS_WHISPER:
            # Fallback to simulated demo transcript
            return self.get_simulated_transcript(audio_path)

        try:
            self.load_model()
            result = self.model.transcribe(audio_path)
            return result.get("text", "")
        except Exception as e:
            # If actual whisper fails (e.g. ffmpeg missing), fallback with notice or raise
            print(f"Whisper transcription failed: {e}", file=sys.stderr)
            raise e

    def get_simulated_transcript(self, file_path):
        """
        Provides a realistic simulated transcript if whisper is not installed,
        allowing testing of the assistant immediately.
        """
        base_name = os.path.basename(file_path).lower()
        
        # If it seems like a design meeting
        if "design" in base_name or "ui" in base_name or "frontend" in base_name:
            return (
                "Sarah: Hi team, let's review the new app design.\n"
                "John: I will update the landing page mockups by Wednesday.\n"
                "Sarah: Perfect. Emily, could you verify the responsive design layout tomorrow?\n"
                "Emily: Yes, I will test it on mobile viewports tomorrow.\n"
                "Mike: I will schedule a user feedback session next week.\n"
                "Sarah: Sounds great, let's coordinate on Slack."
            )
        
        # Default high-quality simulated meeting transcript
        return (
            "Alice: Good morning. Let's go around and list our action items.\n"
            "Bob: I will update the database server by Friday.\n"
            "Alice: That sounds good. Charlie, please review the frontend mockups tomorrow.\n"
            "Charlie: Sure, I can do that. I need to coordinate with Dave as well.\n"
            "Dave: Yes, I will write the API documentation next week.\n"
            "Alice: Great, let's sync up again on Monday."
        )
