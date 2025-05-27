# ChatWithWiki 🤖📚

A conversational AI chatbot that allows users to have intelligent conversations with Wikipedia articles using advanced natural language processing.

## What it does

Load any Wikipedia article and ask questions about it in natural language. The AI will provide detailed, contextual answers based on the article content, maintaining conversation memory for follow-up questions.

## Tech Stack

- **Backend**: Flask (Python web framework)
- **AI/ML**: 
  - OpenAI GPT-3.5-turbo (conversational AI)
  - LangChain (AI application framework)
  - ChromaDB (vector database for semantic search)
  - OpenAI Embeddings (text-embedding-ada-002)
- **Data Processing**:
  - Wikipedia MediaWiki API (content fetching)
  - BeautifulSoup4 (HTML parsing)
  - Text chunking and preprocessing
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Deployment**: Railway (cloud platform)
- **Production Server**: Gunicorn

## Key Features

- 🔍 **Semantic Search**: Finds relevant information using vector embeddings
- 💬 **Conversational Memory**: Remembers context throughout the conversation
- 🎯 **Smart Retrieval**: Uses MMR (Maximal Marginal Relevance) for diverse, relevant responses
- 📊 **Session Management**: Handles multiple concurrent users
- 🔄 **Topic Tracking**: Provides varied responses to similar questions
- ⚡ **Real-time Processing**: Fast response times with optimized chunking

## How it Works

1. **Article Loading**: Fetches Wikipedia content via MediaWiki API
2. **Text Processing**: Splits content into semantic chunks (1000 chars, 200 overlap)
3. **Vector Storage**: Creates embeddings and stores in ChromaDB
4. **Conversational AI**: Uses LangChain's retrieval-augmented generation (RAG)
5. **Smart Responses**: Combines retrieved context with conversation history

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd chatwithwiki
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Run locally
python app.py
```

Visit `http://localhost:8069` and start chatting with Wikipedia!

## API Endpoints

- `POST /api/load` - Load Wikipedia article
- `POST /api/chat` - Send message to AI
- `GET /api/health` - Health check
- `GET /api/sessions` - List active sessions

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `PORT` - Server port (default: 8069)
- `FLASK_ENV` - Environment mode (development/production)

## Deployment

Ready for Railway deployment with included `Procfile`, `railway.toml`, and production configurations.

---

Built with ❤️ using modern AI technologies for intelligent document interaction. 