# Mandarin to English Speech Translator

This application captures Mandarin speech through your microphone and translates it to English text using OpenAI's Whisper API.

## Features
- High-quality Mandarin speech recognition using OpenAI Whisper
- Automatic translation to English
- Modern, responsive user interface
- Text input option for direct translation

## Requirements
- Python 3.7+
- OpenAI API key with available credits
- A working microphone
- Internet connection (for speech recognition and translation)

## Local Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/mandarin-english-translator.git
cd mandarin-english-translator
```

2. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Run the translator:
```bash
python translator.py
```

5. Open your browser and navigate to:
```
http://localhost:8080
```

## Deployment Options

### Option 1: Deploy to Heroku

1. Create a Heroku account at https://heroku.com
2. Install the Heroku CLI
3. Login to Heroku:
```bash
heroku login
```

4. Create a new Heroku app:
```bash
heroku create your-app-name
```

5. Set your OpenAI API key as an environment variable:
```bash
heroku config:set OPENAI_API_KEY=your_api_key_here
```

6. Deploy your application:
```bash
git push heroku main
```

7. Open your application:
```bash
heroku open
```

### Option 2: Deploy to Render

1. Create a Render account at https://render.com
2. Create a new Web Service
3. Connect your GitHub repository
4. Set the build command to: `pip install -r requirements.txt`
5. Set the start command to: `gunicorn translator:app`
6. Add the environment variable: `OPENAI_API_KEY=your_api_key_here`
7. Deploy the service

### Option 3: Deploy to PythonAnywhere

1. Create a PythonAnywhere account at https://www.pythonanywhere.com
2. Upload your files or clone your repository
3. Set up a new web app with Flask
4. Configure the WSGI file to point to your `translator.py` file
5. Set your OpenAI API key in the environment variables
6. Reload the web app

## Sharing with Others

When sharing with others, make sure:
1. Your OpenAI API key has sufficient credits
2. You've deployed to a publicly accessible server
3. You've shared the URL with your users
4. You've explained any usage limitations

## Note
The application requires an OpenAI API key with available credits. If you see "API Error: OpenAI quota exceeded", you'll need to update your API key or add more credits to your OpenAI account.

## License
MIT
