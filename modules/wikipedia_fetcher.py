"""
Wikipedia article fetcher module.
Handles URL parsing and content extraction from Wikipedia Action API.
"""

import requests
import re
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup


class WikipediaFetcher:
    """Fetches and processes Wikipedia articles using the MediaWiki Action API."""
    
    def __init__(self):
        """Initialize the fetcher with proper headers."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ChatWithWiki/1.0 (https://github.com/user/chatwithwiki) Python/requests'
        })
    
    @staticmethod
    def extract_title_from_url(url: str) -> tuple[str, str]:
        """
        Extract article title and language from Wikipedia URL.
        
        Args:
            url: Wikipedia article URL
            
        Returns:
            tuple: (language, title)
            
        Raises:
            ValueError: If URL is not a valid Wikipedia URL
        """
        parsed = urlparse(url)
        
        if 'wikipedia.org' not in parsed.netloc:
            raise ValueError("Not a Wikipedia URL")
        
        # Extract language (e.g., 'en' from 'en.wikipedia.org')
        lang = parsed.netloc.split('.')[0]
        
        # Extract title from path (e.g., '/wiki/Python_(programming_language)')
        path_parts = parsed.path.split('/')
        if len(path_parts) < 3 or path_parts[1] != 'wiki':
            raise ValueError("Invalid Wikipedia article URL")
        
        title = unquote(path_parts[2])
        return lang, title
    
    def fetch_article_content(self, url: str) -> dict:
        """
        Fetch full article content from Wikipedia using Action API.
        
        Args:
            url: Wikipedia article URL
            
        Returns:
            dict: Article data with title, extract, and full_text
            
        Raises:
            Exception: If article cannot be fetched
        """
        try:
            lang, title = self.extract_title_from_url(url)
            
            # Build API URL for the specific language
            api_url = f"https://{lang}.wikipedia.org/w/api.php"
            
            # First, get the extract (summary) using the extracts module
            extract_params = {
                "action": "query",
                "prop": "extracts",
                "titles": title,
                "exintro": True,
                "explaintext": True,
                "format": "json"
            }
            
            extract_response = self.session.get(api_url, params=extract_params, timeout=10)
            extract_response.raise_for_status()
            extract_data = extract_response.json()
            
            # Get the page ID and extract
            pages = extract_data.get("query", {}).get("pages", {})
            if not pages:
                raise Exception("Article not found")
            
            page_id = list(pages.keys())[0]
            if page_id == "-1":
                raise Exception("Article not found")
            
            page_data = pages[page_id]
            article_title = page_data.get("title", title)
            extract = page_data.get("extract", "")
            
            # Now get the full content using the parse action
            parse_params = {
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json"
            }
            
            parse_response = self.session.get(api_url, params=parse_params, timeout=15)
            parse_response.raise_for_status()
            parse_data = parse_response.json()
            
            if "error" in parse_data:
                raise Exception(f"API Error: {parse_data['error'].get('info', 'Unknown error')}")
            
            # Extract HTML content
            html_content = parse_data.get("parse", {}).get("text", {}).get("*", "")
            
            # Convert HTML to clean text
            full_text = self._html_to_text(html_content)
            
            # Combine extract and full text
            if extract and extract not in full_text:
                full_text = extract + "\n\n" + full_text
            
            return {
                'title': article_title,
                'extract': extract,
                'full_text': full_text.strip(),
                'url': url
            }
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch article: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing article: {str(e)}")
    
    def _html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to clean text.
        
        Args:
            html_content: HTML string from Wikipedia
            
        Returns:
            str: Clean text content
        """
        if not html_content:
            return ""
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'sup', 'table', 'div.navbox', 
                               'div.infobox', 'div.metadata', 'div.hatnote']):
                element.decompose()
            
            # Remove reference links like [1], [2], etc.
            for element in soup.find_all('a', href=True):
                if element.get('href', '').startswith('#cite_note'):
                    element.decompose()
            
            # Get text and clean it up
            text = soup.get_text()
            
            # Clean up the text
            text = re.sub(r'\[edit\]', '', text)  # Remove [edit] markers
            text = re.sub(r'\[\d+\]', '', text)   # Remove citation numbers
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize line breaks
            text = re.sub(r' +', ' ', text)       # Normalize spaces
            
            return text.strip()
            
        except Exception as e:
            # Fallback: simple regex cleaning
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\[edit\]', '', text)
            text = re.sub(r'\[\d+\]', '', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            return text.strip()
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate if URL is a proper Wikipedia article URL.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if valid Wikipedia URL
        """
        try:
            WikipediaFetcher.extract_title_from_url(url)
            return True
        except ValueError:
            return False 