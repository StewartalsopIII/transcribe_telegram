import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
from pydub import AudioSegment
import io
import base64
import json

# Google AI types for enabling tools like Google Search (may not be strictly required depending on library version)
try:
    from google.generativeai import types as genai_types
except ImportError:
    genai_types = None

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Google AI
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class AudioTranscriber:
    async def download_audio_file(self, file):
        """Download audio file from Telegram."""
        binary = await file.download_as_bytearray()
        return io.BytesIO(binary)

    async def convert_to_wav(self, audio_data):
        """Convert audio to WAV format."""
        audio = AudioSegment.from_file(audio_data)
        wav_io = io.BytesIO()
        audio.export(wav_io, format='wav')
        wav_io.seek(0)
        return wav_io

    async def transcribe_audio(self, audio_file):
        """Transcribe audio and translate to English if not in English."""
        try:
            # Convert the audio file to base64
            audio_bytes = audio_file.read()
            audio_b64 = base64.b64encode(audio_bytes).decode()
            
            # Use the newer Gemini 1.5 Pro model
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Create content parts in the correct format
            parts = [
                {
                    "inline_data": {
                        "mime_type": "audio/wav",
                        "data": audio_b64
                    }
                },
                {
                    "text": """Please transcribe this audio.
                    
                    If the audio is in English:
                    - Provide ONLY the transcription, nothing else
                    
                    If the audio is NOT in English:
                    Original: [transcription in original language]
                    Translation: [English translation]"""
                }
            ]
            
            # Generate content with proper format
            response = model.generate_content(parts)
            
            return response.text
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return f"Error transcribing audio: {str(e)}"

    async def process_audio(self, audio_file):
        """Process audio file and return transcription."""
        wav_file = await self.convert_to_wav(audio_file)
        transcription = await self.transcribe_audio(wav_file)
        return transcription


class TextProcessor:
    """Process transcribed text: clarity rewrite, grounding, and proposition extraction."""

    def __init__(self):
        # Fast / cheap text-only models
        self.clarity_model = genai.GenerativeModel('gemini-2.5-flash')
        self.proposition_model = genai.GenerativeModel('gemini-1.5-flash')

    def _enable_google_search_tool(self):
        """Return a tools argument enabling Google Search grounding if SDK supports it."""
        # Only enable if the SDK version exposes GoogleSearch and Tool helpers.
        if genai_types is None:
            return None
        if not hasattr(genai_types, "GoogleSearch") or not hasattr(genai_types, "Tool"):
            return None

        return [genai_types.Tool(google_search=genai_types.GoogleSearch())]

    def rewrite_for_clarity(self, raw_text):
        """Rewrite the text for clarity and flag ambiguity.

        Returns (clarified_text, ambiguous_terms: list[str])
        """
        prompt = (
            "Rewrite the following text for clarity while preserving meaning.\n"
            "Surround any word or phrase you suspect was mistranscribed with ‹??›.\n"
            "Format the text with proper paragraphs and structure for readability - break up long sentences and add line breaks between different topics or ideas.\n"
            "After the rewrite, return a JSON object with exactly two keys: \n"
            "  clarified_text – the rewritten text,\n"
            "  ambiguous_terms – an array of the flagged words/phrases (may be empty).\n\n"
            "Text:\n" + raw_text
        )

        response = self.clarity_model.generate_content(prompt)

        def _extract_json(text: str):
            """Best-effort extraction of JSON object even if wrapped in code fences."""
            text = text.strip()
            # Remove ```json ... ``` fences if present
            if text.startswith("```"):
                # Strip leading ```lang and trailing ```
                lines = text.splitlines()
                # drop the first line (```json or ```)
                if lines:
                    lines = lines[1:]
                # remove trailing ``` if present
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()

            # Attempt to locate first '{' ... last '}'
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                candidate = text[start:end+1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass
            # Final attempt – direct load
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None

        data = _extract_json(response.text)
        if data:
            clarified_text = str(data.get('clarified_text', '')).strip()
            ambiguous_terms = data.get('ambiguous_terms', []) or []
            return clarified_text, ambiguous_terms

        # Fallback: treat whole output as clarified text (possible the model didn't output JSON)
        return response.text.strip(), []

    def ground_ambiguous_terms(self, clarified_text):
        """
        Use Google Search grounding to correct ambiguous terms and qualify proper names.

        Returns (corrected_text: str, search_terms: list[str])
        """

        prompt = (
            "Here is a passage of text. Using web search as needed, correct any words or phrases "
            "that appear between ‹??› markers. Identify and qualify all proper-name candidates "
            "with web search.\n\n"
            "Return a JSON object with exactly two keys:\n"
            "  corrected_text – the final corrected text,\n"
            "  search_terms   – an array of the search queries you performed (may be empty).\n\n"
            "Text:\n" + clarified_text
        )

        tools_arg = self._enable_google_search_tool()
        response = (
            self.clarity_model.generate_content(prompt, tools=tools_arg)
            if tools_arg is not None
            else self.clarity_model.generate_content(prompt)
        )

        # Lightweight helper to pull JSON from model response
        def _extract_json(text: str):
            text = text.strip()
            if text.startswith("```"):
                lines = text.splitlines()[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end != -1 and end > start:
                fragment = text[start : end + 1]
                try:
                    return json.loads(fragment)
                except json.JSONDecodeError:
                    pass
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None

        data = _extract_json(response.text)
        if data:
            corrected_text = str(data.get("corrected_text", "")).strip()
            search_terms = data.get("search_terms", []) or []
            return corrected_text, search_terms

        # Fallback – model did not return JSON
        return response.text.strip(), []

    def extract_propositions(self, final_text):
        """Split text into atomic propositions and return list[str]."""

        prompt = (
            "Split the following text into a JSON array named propositions, where each element\n"
            "is an atomic fact or claim expressed in the text. Return only the JSON.\n\n"
            "Text:\n" + final_text
        )

        response = self.proposition_model.generate_content(prompt)
        try:
            data = json.loads(response.text)
            return data.get('propositions', [])
        except json.JSONDecodeError:
            # Fallback: split by lines
            return [line.strip() for line in response.text.splitlines() if line.strip()]

class TelegramBot:
    def __init__(self):
        self.transcriber = AudioTranscriber()
        self.text_processor = TextProcessor()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "👋 Welcome to the Audio Transcriber Bot!\n\n"
            "Send me any voice message or audio file, and I'll transcribe it for you.\n"
            "If the audio is in Russian or another language, I'll provide an English translation too!"
        )
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = (
            "🎯 Here's how to use the bot:\n\n"
            "1. Send any voice message or audio file\n"
            "2. Wait for processing (this may take a moment)\n"
            "3. Receive your transcription and translation\n\n"
            "Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message"
        )
        await update.message.reply_text(help_message)

    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio messages."""
        try:
            # Send processing message
            processing_message = await update.message.reply_text(
                "🎵 Processing your audio... Please wait."
            )

            # Get the audio file
            if update.message.voice:
                file = await update.message.voice.get_file()
            else:
                file = await update.message.audio.get_file()

            # Download and process audio
            audio_data = await self.transcriber.download_audio_file(file)
            transcription = await self.transcriber.process_audio(audio_data)

            # ---- New post-processing pipeline ----
            clarified_text, ambiguous_terms = self.text_processor.rewrite_for_clarity(transcription)

            # Ground ambiguous terms if needed
            if ambiguous_terms:
                final_text, search_terms = self.text_processor.ground_ambiguous_terms(clarified_text)
            else:
                final_text = clarified_text
                search_terms = []

            propositions = self.text_processor.extract_propositions(final_text)

            # -------- Send separate messages --------

            # 1) Original transcription (raw, easy to copy)
            await update.message.reply_text(transcription)

            # 2) Clarified / grounded text (raw)
            await update.message.reply_text(final_text)

            # 3) JSON details (ambiguous terms + search terms + propositions)
            json_payload = json.dumps({
                "ambiguous_terms": ambiguous_terms,
                "search_terms": search_terms,
                "propositions": propositions,
            }, ensure_ascii=False, indent=2)

            await update.message.reply_text(
                f"```json\n{json_payload}\n```",
                parse_mode="Markdown"
            )

            # Delete processing message
            await processing_message.delete()

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            await update.message.reply_text(
                f"❌ Sorry, there was an error processing your audio: {str(e)}"
            )

    def run(self):
        """Run the bot."""
        # Create application
        application = Application.builder().token(
            os.getenv('TELEGRAM_BOT_TOKEN')
        ).build()

        # Add handlers
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(MessageHandler(
            filters.VOICE | filters.AUDIO, 
            self.handle_audio
        ))

        # Start the bot
        application.run_polling()

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()