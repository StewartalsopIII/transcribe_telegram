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

class TelegramBot:
    def __init__(self):
        self.transcriber = AudioTranscriber()
        
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

            # Send transcription
            await update.message.reply_text(
                f"📝 Transcription and Translation:\n\n{transcription}"
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