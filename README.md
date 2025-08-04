# Telegram Audio Transcription Bot

A Telegram bot that automatically transcribes voice messages and audio files using Google's Gemini 1.5 Pro model. The bot can transcribe audio in various languages and provides English translations for non-English audio.

## Features

- Transcribes voice messages and audio files sent via Telegram
- Supports multiple audio formats (automatically converts to WAV)
- Provides transcription in the original language
- Automatically translates non-English audio to English
- Simple and intuitive interface with helpful command messages

## Prerequisites

- Python 3.12+
- Telegram Bot Token
- Google API Key (for Gemini 1.5 Pro)

## Required Environment Variables

Create a `.env` file in the root directory with the following variables:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_google_api_key
```

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the bot:
```bash
python main.py
```

2. In Telegram:
   - Start a chat with the bot
   - Use `/start` to get a welcome message
   - Use `/help` to see available commands
   - Send any voice message or audio file to get a transcription

## Project Structure

- `main.py`: Main application file containing the bot logic
- `requirements.txt`: List of Python dependencies
- `.env`: Environment variables configuration
- `.gitignore`: Git ignore file

## Main Components

### AudioTranscriber Class
Handles all audio processing tasks:
- Downloads audio files from Telegram
- Converts audio to WAV format
- Transcribes audio using Google's Gemini 1.5 Pro
- Provides translations for non-English audio

### TelegramBot Class
Manages the Telegram bot functionality:
- Handles commands (`/start`, `/help`)
- Processes incoming audio messages
- Manages user interactions and messages

## Dependencies

- python-telegram-bot: Telegram Bot API wrapper
- python-dotenv: Environment variables management
- google-generativeai: Google's Generative AI API
- pydub: Audio file processing
- Other supporting libraries (see requirements.txt)

## Error Handling

The bot includes comprehensive error handling for:
- Audio processing failures
- Transcription errors
- File download issues
- API communication problems

## Logging

Includes built-in logging functionality that tracks:
- Application startup
- Command usage
- Processing events
- Errors and exceptions

## Contributing

Feel free to submit issues and enhancement requests!