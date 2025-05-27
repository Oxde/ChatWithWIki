# ChatWithWiki - Wikipedia Conversational Chatbot

A Flask-based web application that allows users to have conversations with Wikipedia articles using AI-powered question answering.

## 🚀 Features

- Load any Wikipedia article by URL
- Ask questions about the article content
- Conversational memory (remembers previous questions in the session)
- Real-time chat interface
- Vector-based semantic search for accurate answers

## 🛠 Tech Stack

### Backend
- **Flask** - Web framework
- **LangChain** - LLM orchestration and chains
- **OpenAI GPT** - Language model for answering questions
- **FAISS** - Vector database for semantic search
- **Tiktoken** - Token counting and text processing

### Frontend
- **HTML/CSS/JavaScript** - Simple, responsive chat interface
- **Fetch API** - Asynchronous communication with backend

### Data Processing
- **Wikipedia REST API** - Article content retrieval
- **Text Chunking** - Overlapping chunks for better context
- **OpenAI Embeddings** - Vector representations of text

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key

## 🔧 Installation

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd chatwithwiki
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment setup**
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open browser**
   Navigate to `http://localhost:5000`

## 🎯 Usage

1. **Load Article**: Paste a Wikipedia URL and click "Load Article"
2. **Ask Questions**: Type questions about the article content
3. **Conversational**: Follow up with related questions - the bot remembers context

## 🏗 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API      │    │   LangChain     │
│   (HTML/JS)     │◄──►│   (Routes)       │◄──►│   (QA Chain)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Session        │    │   FAISS Vector  │
                       │   Management     │    │   Store         │
                       └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
chatwithwiki/
├── app.py                 # Main Flask application
├── modules/
│   ├── __init__.py
│   ├── wikipedia_fetcher.py    # Wikipedia API integration
│   ├── text_processor.py       # Text chunking and preprocessing
│   ├── chain_factory.py        # LangChain setup
│   └── session_manager.py      # Session state management
├── static/
│   ├── style.css              # Frontend styling
│   └── script.js              # Frontend JavaScript
├── templates/
│   └── index.html             # Main chat interface
├── requirements.txt           # Python dependencies
├── env.example               # Environment variables template
└── README.md                 # This file
```

## 🔒 Security Notes

- Never commit your `.env` file with real API keys
- API keys are handled server-side only
- Sessions are stored in memory (consider Redis for production)

## 🚀 Deployment

For production deployment:

1. **Heroku**
   ```bash
   # Add Procfile
   echo "web: gunicorn app:app" > Procfile
   ```

2. **Environment Variables**
   Set `OPENAI_API_KEY` in your hosting platform

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details 