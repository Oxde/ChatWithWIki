"""
ChatWithWiki Flask Application
Main application file with API endpoints for Wikipedia conversational chatbot.
"""

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Import our custom modules
from modules.wikipedia_fetcher import WikipediaFetcher
from modules.text_processor import TextProcessor
from modules.chain_factory import ChainFactory
from modules.session_manager import SessionManager

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
text_processor = TextProcessor()
session_manager = SessionManager()
wikipedia_fetcher = WikipediaFetcher()

# Initialize chain factory (requires OpenAI API key)
chain_factory = None
try:
    chain_factory = ChainFactory()
    logger.info("ChainFactory initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ChainFactory: {str(e)}")
    logger.warning("Application will run in limited mode without AI features")


@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')


@app.route('/api/load', methods=['POST'])
def load_article():
    """
    Load a Wikipedia article and create a conversational chain.
    
    Expected JSON: {"url": "https://en.wikipedia.org/wiki/Article_Name"}
    Returns: {"status": "success", "session_id": "...", "article_title": "..."}
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        # Validate Wikipedia URL
        if not wikipedia_fetcher.validate_url(url):
            return jsonify({"error": "Invalid Wikipedia URL"}), 400
        
        # Check if chain factory is available
        if not chain_factory:
            return jsonify({"error": "OpenAI API key not configured"}), 500
        
        logger.info(f"Loading article from URL: {url}")
        
        # Fetch article content
        article_data = wikipedia_fetcher.fetch_article_content(url)
        logger.info(f"Fetched article: {article_data['title']}")
        
        # Process text into chunks
        documents = text_processor.create_chunks(article_data)
        logger.info(f"Created {len(documents)} text chunks")
        
        # Create conversational chain
        try:
            chain, retriever, chat_history = chain_factory.create_wiki_chain(documents)
        except Exception as openai_error:
            logger.error(f"OpenAI connection error: {str(openai_error)}")
            if "timeout" in str(openai_error).lower() or "connection" in str(openai_error).lower():
                return jsonify({
                    "error": "OpenAI API connection timeout. Please try again in a moment.",
                    "details": "The AI service is temporarily unavailable due to network issues."
                }), 503
            else:
                return jsonify({
                    "error": "AI service initialization failed. Please try again.",
                    "details": str(openai_error)
                }), 500
        
        # Create session
        session_id = session_manager.create_session(
            chain=chain,
            retriever=retriever,
            chat_history=chat_history,
            article_title=article_data['title']
        )
        
        logger.info(f"Created session {session_id} for article: {article_data['title']}")
        
        # Get text statistics
        stats = text_processor.get_text_stats(article_data['full_text'])
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "article_title": article_data['title'],
            "article_url": url,
            "stats": stats,
            "message": f"Article '{article_data['title']}' loaded successfully. You can now ask questions about it!"
        })
        
    except Exception as e:
        logger.error(f"Error loading article: {str(e)}")
        return jsonify({"error": f"Failed to load article: {str(e)}"}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handle chat messages for a session.
    
    Expected JSON: {"session_id": "...", "question": "..."}
    Returns: {"answer": "...", "sources": [...], "history": [...]}
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        session_id = data.get('session_id', '').strip()
        question = data.get('question', '').strip()
        
        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        # Get session
        chain_and_history = session_manager.get_chain_and_history(session_id)
        if not chain_and_history:
            return jsonify({"error": "Session not found or expired"}), 404
        
        chain, chat_history = chain_and_history
        
        logger.info(f"Processing question for session {session_id}: {question[:100]}...")
        
        # Check for recent topics to provide context for more varied responses
        recent_topics = session_manager.get_recent_topics(session_id, last_n=3)
        
        # Enhance the question with context if similar topics were recently discussed
        enhanced_question = question
        if recent_topics and len(recent_topics) > 1:
            # If we've discussed similar topics, add context to encourage variety
            topic_context = f"Previous topics discussed: {', '.join(set(recent_topics))}. "
            if recent_topics.count(recent_topics[-1]) > 1:  # Same topic repeated
                topic_context += "Please provide a different perspective or additional details. "
            enhanced_question = topic_context + question
        
        # Get response from chain using new API
        response = chain.invoke({
            "input": enhanced_question,
            "chat_history": chat_history
        })
        
        # Add messages to chat history
        session_manager.add_message_to_history(session_id, question, response['answer'])
        
        # Increment message count
        session_manager.increment_message_count(session_id)
        
        # Extract source information
        sources = []
        if response.get('context'):
            for doc in response['context']:
                sources.append({
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    'metadata': doc.metadata
                })
        
        # Get conversation history for display
        history = []
        for msg in chat_history[-10:]:  # Last 10 messages
            history.append({
                'type': 'human' if msg.__class__.__name__ == 'HumanMessage' else 'ai',
                'content': msg.content
            })
        
        logger.info(f"Generated response for session {session_id}")
        
        return jsonify({
            "answer": response['answer'],
            "sources": sources,
            "history": history,
            "session_info": session_manager.get_session_info(session_id),
            "recent_topics": recent_topics,
            "enhanced_query": enhanced_question != question
        })
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({"error": f"Failed to process question: {str(e)}"}), 500


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session_info(session_id):
    """Get information about a session."""
    try:
        session_info = session_manager.get_session_info(session_id)
        if not session_info:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify(session_info)
        
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session."""
    try:
        if session_manager.delete_session(session_id):
            return jsonify({"message": "Session deleted successfully"})
        else:
            return jsonify({"error": "Session not found"}), 404
            
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions."""
    try:
        sessions = session_manager.list_active_sessions()
        stats = session_manager.get_stats()
        
        return jsonify({
            "sessions": sessions,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_configured": chain_factory is not None,
        "active_sessions": len(session_manager.list_active_sessions())
    })


@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check configuration without exposing sensitive data."""
    try:
        raw_api_key = os.getenv('OPENAI_API_KEY')
        cleaned_api_key = raw_api_key.strip().replace('\n', '').replace('\r', '').replace('=', '') if raw_api_key else None
        
        return jsonify({
            "openai_key_configured": bool(raw_api_key),
            "raw_key_length": len(raw_api_key) if raw_api_key else 0,
            "cleaned_key_length": len(cleaned_api_key) if cleaned_api_key else 0,
            "raw_key_prefix": repr(raw_api_key[:10]) if raw_api_key and len(raw_api_key) > 10 else "Invalid",
            "cleaned_key_prefix": cleaned_api_key[:7] + "..." if cleaned_api_key and len(cleaned_api_key) > 10 else "Invalid",
            "key_starts_with_sk": cleaned_api_key.startswith('sk-') if cleaned_api_key else False,
            "chain_factory_initialized": chain_factory is not None,
            "environment": os.getenv('FLASK_ENV', 'production'),
            "python_version": os.sys.version,
            "openai_env_var_count": len([k for k in os.environ.keys() if k == 'OPENAI_API_KEY'])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/test-openai', methods=['GET'])
def test_openai():
    """Test OpenAI API connectivity."""
    try:
        if not chain_factory:
            return jsonify({"error": "ChainFactory not initialized"}), 500
        
        # Simple test - try to create embeddings for a short text
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Test with a very simple request
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input="test",
            timeout=30
        )
        
        return jsonify({
            "status": "success",
            "message": "OpenAI API connection successful",
            "embedding_dimensions": len(response.data[0].embedding),
            "model_used": response.model
        })
        
    except Exception as e:
        logger.error(f"OpenAI API test failed: {str(e)}")
        return jsonify({
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Check if OpenAI API key is configured
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("OPENAI_API_KEY not found in environment variables")
        logger.warning("Please set your OpenAI API key in a .env file")
    
    # Run the app
    port = int(os.getenv('PORT', 8069))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting ChatWithWiki on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug) 