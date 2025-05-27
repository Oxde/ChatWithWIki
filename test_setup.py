#!/usr/bin/env python3
"""
Test script to verify ChatWithWiki setup.
Checks all dependencies, file structure, and basic functionality.
"""

import os
import sys
from pathlib import Path

def test_file_structure():
    """Test if all required files exist."""
    print("Testing file structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'modules/__init__.py',
        'modules/wikipedia_fetcher.py',
        'modules/text_processor.py',
        'modules/chain_factory.py',
        'modules/session_manager.py',
        'templates/index.html',
        'static/style.css',
        'static/script.js',
        'README.md'
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_python_imports():
    """Test if all required Python packages can be imported."""
    print("Testing imports...")
    
    imports = [
        ('Flask', 'flask'),
        ('Requests', 'requests'),
        ('OpenAI', 'openai'),
        ('LangChain', 'langchain'),
        ('ChromaDB', 'chromadb')
    ]
    
    all_imported = True
    for name, module in imports:
        try:
            __import__(module)
            print(f"✓ {name} imported successfully")
        except ImportError as e:
            print(f"✗ {name} import failed: {e}")
            all_imported = False
    
    return all_imported

def test_custom_modules():
    """Test if custom modules can be imported."""
    print("Testing custom modules...")
    
    # Add current directory to path
    sys.path.insert(0, os.getcwd())
    
    modules = [
        ('WikipediaFetcher', 'modules.wikipedia_fetcher', 'WikipediaFetcher'),
        ('TextProcessor', 'modules.text_processor', 'TextProcessor'),
        ('ChainFactory', 'modules.chain_factory', 'ChainFactory'),
        ('SessionManager', 'modules.session_manager', 'SessionManager')
    ]
    
    all_imported = True
    for name, module_path, class_name in modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {name} imported successfully")
        except (ImportError, AttributeError) as e:
            print(f"✗ {name} import failed: {e}")
            all_imported = False
    
    return all_imported

def test_wikipedia_fetcher():
    """Test Wikipedia fetcher functionality."""
    print("Testing Wikipedia fetcher...")
    
    try:
        from modules.wikipedia_fetcher import WikipediaFetcher
        
        # Test URL validation
        valid_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        invalid_url = "https://google.com"
        
        if WikipediaFetcher.validate_url(valid_url):
            print("✓ URL validation works for valid URLs")
        else:
            print("✗ URL validation failed for valid URLs")
            return False
        
        if not WikipediaFetcher.validate_url(invalid_url):
            print("✓ URL validation works for invalid URLs")
        else:
            print("✗ URL validation failed for invalid URLs")
            return False
        
        # Test URL parsing
        lang, title = WikipediaFetcher.extract_title_from_url(valid_url)
        if lang == "en" and title == "Python_(programming_language)":
            print("✓ URL parsing works correctly")
        else:
            print(f"✗ URL parsing failed: got '{lang}', '{title}'")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Wikipedia fetcher test failed: {e}")
        return False

def test_text_processor():
    """Test text processor functionality."""
    print("Testing text processor...")
    
    try:
        from modules.text_processor import TextProcessor
        
        processor = TextProcessor()
        
        # Test text preprocessing
        test_text = "This is a test text with some [edit] markers and extra spaces."
        processed = processor.preprocess_text(test_text)
        
        if "[edit]" not in processed and len(processed) > 0:
            print("✓ Text preprocessing works correctly")
        else:
            print("✗ Text preprocessing failed")
            return False
        
        # Test token counting
        token_count = processor.count_tokens(test_text)
        if isinstance(token_count, int) and token_count > 0:
            print("✓ Token counting works")
        else:
            print("✗ Token counting failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Text processor test failed: {e}")
        return False

def test_environment():
    """Test environment configuration."""
    print("Testing environment...")
    
    # Check for .env file or environment variable
    env_file_exists = Path('.env').exists()
    api_key_in_env = os.getenv('OPENAI_API_KEY') is not None
    
    if env_file_exists or api_key_in_env:
        print("✓ Environment configuration found")
        return True
    else:
        print("⚠ OPENAI_API_KEY not found in environment")
        print("  Please set your OpenAI API key in a .env file")
        return True  # Not a failure, just a warning

def main():
    """Run all tests."""
    print("ChatWithWiki Setup Test")
    print("=" * 50)
    print()
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Imports", test_python_imports),
        ("Custom Modules", test_custom_modules),
        ("Wikipedia Fetcher", test_wikipedia_fetcher),
        ("Text Processor", test_text_processor),
        ("Environment", test_environment)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"{test_name}:")
        print("-" * 30)
        print()
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results[test_name] = False
        
        print()
    
    # Summary
    print("=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your ChatWithWiki setup is ready.")
        return 0
    else:
        failed = total - passed
        print(f"\n⚠ {failed} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 