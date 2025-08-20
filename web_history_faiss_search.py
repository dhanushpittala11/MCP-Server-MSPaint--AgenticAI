import os
import sqlite3
import datetime
import requests
import numpy as np
import faiss
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import tempfile
import shutil
import time 
from google import genai
import re
from google.ai.generativelanguage import Content, Part
from google.ai.generativelanguage_v1.types import GenerateContentRequest
import nltk
from scipy.spatial.distance import cosine
from nltk.tokenize import sent_tokenize
import html
nltk.download('punkt_tab')

# --- CONFIG ---
CHROME_HISTORY_PATH = os.path.expandvars(
    r'%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Profile 8\\History'
)
DAYS_BACK = 2
SKIP_DOMAINS = ['mail.google.com', 'web.whatsapp.com', 'accounts.google.com']
EMBEDDING_URL = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL = "nomic-embed-text"
FAISS_INDEX_FILE = "web_faiss.index"
FAISS_META_FILE = "web_faiss_meta.npy"

# --- EMBEDDING FUNCTION ---
def get_embedding(text: str) -> np.ndarray:
    response = requests.post(
        EMBEDDING_URL,
        json={"model": EMBEDDING_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

# --- 1. Extract Chrome History ---
def get_recent_urls(days=DAYS_BACK):
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        shutil.copy2(CHROME_HISTORY_PATH, tf.name)
        conn = sqlite3.connect(tf.name)
        cursor = conn.cursor()
        chrome_epoch = datetime.datetime(1601, 1, 1)
        cutoff_chrome = int((datetime.datetime.now() - datetime.timedelta(days=days) - chrome_epoch).total_seconds() * 1_000_000)
        cursor.execute("""
            SELECT url, title, last_visit_time
            FROM urls
            WHERE last_visit_time > ?
        """, (cutoff_chrome,))
        urls = cursor.fetchall()
        conn.close()
    filtered = [u for u in urls if not any(d in u[0] for d in SKIP_DOMAINS)]
    return filtered

# --- 2. Fetch Web Page Content ---
def fetch_content(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'lxml')
        texts = soup.stripped_strings
        content = ' '.join(texts)
        return content
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

# --- 3. Build Embeddings and FAISS Index ---
def build_faiss_index():
    urls = get_recent_urls()
    embeddings = []
    meta = []
    for url, title, _ in urls:
        print(f"Processing: {url}")
        content = fetch_content(url)
        if not content or len(content) < 100:
            continue
        snippet = content[:300]
        try:
            emb = get_embedding(snippet)
            embeddings.append(emb)
            meta.append({'url': url, 'title': title, 'snippet': snippet, 'content': content})
        except Exception as e:
            print(f"Embedding failed for {url}: {e}")
    if not embeddings:
        print("No embeddings created.")
        return
    emb_matrix = np.vstack(embeddings).astype('float32')
    index = faiss.IndexFlatL2(emb_matrix.shape[1])
    index.add(emb_matrix)
    faiss.write_index(index, FAISS_INDEX_FILE)
    np.save(FAISS_META_FILE, np.array(meta, dtype=object))
    print(f"FAISS index and metadata saved. {len(meta)} pages indexed.")

# --- 4. NEW APPROACH: Extract and analyze text directly from live webpage ---
def extract_live_content(driver):
    """Extract text content directly from the live webpage with better cleaning"""
    try:
        # Wait for page to fully load
        time.sleep(3)
        
        # Get all text content from the page using a simpler approach
        text_content = driver.execute_script("""
            var textElements = [];
            
            // Get all elements with text content
            var allElements = document.body.getElementsByTagName('*');
            
            for (var i = 0; i < allElements.length; i++) {
                var element = allElements[i];
                
                // Skip problematic elements
                if (element.tagName === 'SCRIPT' || 
                    element.tagName === 'STYLE' ||
                    element.tagName === 'NOSCRIPT') {
                    continue;
                }
                
                // Get direct text content (not including child elements)
                var directText = '';
                for (var j = 0; j < element.childNodes.length; j++) {
                    var child = element.childNodes[j];
                    if (child.nodeType === Node.TEXT_NODE) {
                        directText += child.textContent;
                    }
                }
                
                // Clean and normalize the text
                directText = directText.trim().replace(/\\s+/g, ' ');
                
                if (directText.length > 8) {  // Only meaningful text
                    textElements.push(directText);
                }
            }
            
            // Also get some longer text segments by combining adjacent elements
            var paragraphs = document.querySelectorAll('p, div, li, td, th, h1, h2, h3, h4, h5, h6');
            for (var k = 0; k < paragraphs.length; k++) {
                var para = paragraphs[k];
                var paraText = para.textContent.trim().replace(/\\s+/g, ' ');
                if (paraText.length > 15 && paraText.length < 500) {
                    textElements.push(paraText);
                }
            }
            
            return textElements;
        """)
        
        # Remove duplicates and clean up
        unique_texts = []
        seen = set()
        
        for text in text_content:
            text_clean = text.strip()
            if text_clean and len(text_clean) > 8:
                # Simple deduplication
                text_key = text_clean[:50].lower()
                if text_key not in seen:
                    seen.add(text_key)
                    unique_texts.append(text_clean)
        
        return unique_texts
    except Exception as e:
        print(f"Error extracting live content: {e}")
        return []

def find_relevant_live_content(driver, query, similarity_threshold=0.35):
    """Find relevant content directly from the live webpage"""
    try:
        print("🔍 Extracting content from live webpage...")
        text_elements = extract_live_content(driver)
        
        if not text_elements:
            print("❌ No text content found on the page")
            return []
        
        print(f"📄 Found {len(text_elements)} text elements on the page")
        
        # Get query embedding
        query_emb = get_embedding(query)
        relevant_matches = []
        
        # Analyze each text element
        processed_texts = set()
        
        for i, text in enumerate(text_elements):
            text = text.strip()
            
            # Skip very short text or duplicates
            if len(text) < 10:
                continue
                
            # Simple deduplication
            text_key = text[:50].lower()
            if text_key in processed_texts:
                continue
            processed_texts.add(text_key)
            
            try:
                # Get embedding for this text
                text_emb = get_embedding(text)
                similarity = 1 - cosine(query_emb, text_emb)
                
                if similarity > similarity_threshold:
                    # Determine color based on similarity
                    if similarity > 0.60:
                        color = "yellow"
                    elif similarity > 0.50:
                        color = "lightgreen"
                    elif similarity > 0.45:
                        color = "lightblue"
                    else:
                        color = "lightcyan"
                    
                    relevant_matches.append((text, similarity, color))
                    
            except Exception as e:
                print(f"Error processing text element {i}: {e}")
                continue
        
        # Sort by similarity
        relevant_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Limit results
        top_matches = relevant_matches[:10]
        
        print(f"✅ Found {len(relevant_matches)} relevant matches, will highlight top {len(top_matches)}")
        for i, (text, sim, color) in enumerate(top_matches):
            print(f"  {i+1}. [{sim:.3f}] {text[:70]}{'...' if len(text) > 70 else ''}")
        
        return top_matches
        
    except Exception as e:
        print(f"Error in live content analysis: {e}")
        return []

def highlight_text_on_page(driver, text, color, similarity):
    """Highlight specific text on the webpage using a simpler, more reliable approach"""
    try:
        # Clean and prepare the text
        clean_text = text.strip()
        if len(clean_text) < 3:
            return False
        
        # Create a simple, robust highlighting approach
        # We'll try multiple variations of the text
        search_variations = [
            clean_text,
            clean_text.replace('\n', ' ').replace('\r', ' '),
            ' '.join(clean_text.split()),  # Normalize whitespace
        ]
        
        # Add word-based partial matches for longer text
        if len(clean_text) > 20:
            words = clean_text.split()
            if len(words) > 2:
                # Try key phrases
                search_variations.append(' '.join(words[:3]))  # First 3 words
                search_variations.append(' '.join(words[-3:]))  # Last 3 words
                if len(words) > 4:
                    search_variations.append(' '.join(words[1:4]))  # Middle words
        
        highlighted = False
        
        for search_text in search_variations:
            if len(search_text.strip()) < 3:
                continue
                
            try:
                # Use a simpler highlighting approach with better escaping
                escaped_search = (search_text.replace('\\', '\\\\')
                                           .replace('"', '\\"')
                                           .replace("'", "\\'")
                                           .replace('\n', ' ')
                                           .replace('\r', ' ')
                                           .strip())
                
                js_code = f'''
                (function() {{
                    var searchText = "{escaped_search}";
                    var color = "{color}";
                    var similarity = {similarity:.3f};
                    
                    // Get all text nodes
                    var walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    var textNodes = [];
                    var node;
                    while (node = walker.nextNode()) {{
                        if (node.nodeValue.trim().length > 0) {{
                            textNodes.push(node);
                        }}
                    }}
                    
                    var found = false;
                    for (var i = 0; i < textNodes.length; i++) {{
                        var textNode = textNodes[i];
                        var text = textNode.nodeValue;
                        var parent = textNode.parentNode;
                        
                        // Skip if already highlighted or in problematic elements
                        if (parent.tagName === 'MARK' || 
                            parent.closest('mark') ||
                            parent.tagName === 'SCRIPT' ||
                            parent.tagName === 'STYLE') {{
                            continue;
                        }}
                        
                        // Case-insensitive search
                        var lowerText = text.toLowerCase();
                        var lowerSearch = searchText.toLowerCase();
                        var index = lowerText.indexOf(lowerSearch);
                        
                        if (index !== -1) {{
                            try {{
                                var beforeText = text.substring(0, index);
                                var matchText = text.substring(index, index + searchText.length);
                                var afterText = text.substring(index + searchText.length);
                                
                                var span = document.createElement('span');
                                span.innerHTML = beforeText + 
                                    '<mark style="background-color: ' + color + 
                                    '; padding: 2px 4px; border-radius: 3px; margin: 0 1px; ' +
                                    'font-weight: bold; border: 1px solid rgba(0,0,0,0.1);" ' +
                                    'title="Similarity: ' + similarity.toFixed(3) + '" ' +
                                    'data-highlight="true">' + 
                                    matchText + '</mark>' + afterText;
                                
                                parent.replaceChild(span, textNode);
                                found = true;
                                break; // Only highlight first occurrence
                            }} catch (e) {{
                                console.log("Error highlighting:", e);
                            }}
                        }}
                    }}
                    
                    return found;
                }})();
                '''
                
                result = driver.execute_script(js_code)
                if result:
                    highlighted = True
                    break
                    
            except Exception as e:
                print(f"    ⚠️ Error with variation '{search_text[:30]}...': {e}")
                continue
        
        return highlighted
        
    except Exception as e:
        print(f"❌ Error in highlight_text_on_page: {e}")
        return False

def apply_highlights(driver, matches):
    """Apply highlights to all matching text segments with better debugging"""
    if not matches:
        return 0
    
    successful_highlights = 0
    
    print(f"🎨 Applying highlights to {len(matches)} text segments...")
    
    # Try highlighting each segment
    for i, (text, similarity, color) in enumerate(matches):
        print(f"  📍 Highlighting segment {i+1}/{len(matches)}: {text[:50]}... (similarity: {similarity:.3f}, color: {color})")
        
        success = highlight_text_on_page(driver, text, color, similarity)
        
        if success:
            successful_highlights += 1
            print(f"    ✅ Successfully highlighted")
        else:
            print(f"    ⚠️  Could not highlight this segment")
            
            # Debug: Show what text we're trying to match
            print(f"    🔍 Debug: Looking for text '{text[:30]}...'")
            
            # Try to find if similar text exists on page
            try:
                words = text.split()[:3]  # First 3 words
                if len(words) >= 2:
                    partial_search = ' '.join(words)
                    found_similar = driver.execute_script(f"""
                        return document.body.textContent.toLowerCase().includes('{partial_search.lower()}');
                    """)
                    if found_similar:
                        print(f"    💡 Similar text found on page, but exact matching failed")
                    else:
                        print(f"    ❌ No similar text found on page")
            except:
                pass
        
        # Small delay between highlights
        time.sleep(0.1)
    
    # Check final count and add styling
    try:
        final_count = driver.execute_script("return document.querySelectorAll('mark[data-highlight=\"true\"]').length;")
        print(f"📊 Final highlight count on page: {final_count}")
        
        if final_count > 0:
            # Add global styles and scroll to first highlight
            driver.execute_script("""
                // Add global styles for highlights
                if (!document.getElementById('highlight-global-styles')) {
                    var style = document.createElement('style');
                    style.id = 'highlight-global-styles';
                    style.textContent = `
                        mark[data-highlight="true"] {
                            transition: all 0.3s ease;
                        }
                        mark[data-highlight="true"]:hover {
                            transform: scale(1.02);
                            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                        }
                        @keyframes highlight-pulse {
                            0%, 100% { opacity: 1; }
                            50% { opacity: 0.8; }
                        }
                    `;
                    document.head.appendChild(style);
                }
                
                // Scroll to first highlight
                setTimeout(function() {
                    var firstHighlight = document.querySelector('mark[data-highlight="true"]');
                    if (firstHighlight) {
                        firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        firstHighlight.style.animation = 'highlight-pulse 3s ease-in-out 2';
                    }
                }, 1000);
            """)
    except Exception as e:
        print(f"Error in final styling: {e}")
    
    return successful_highlights

def search_and_open(query, top_k=1):
    if not os.path.exists(FAISS_INDEX_FILE) or not os.path.exists(FAISS_META_FILE):
        print("Index or metadata not found. Run build_faiss_index() first.")
        return
    
    # Load index and metadata
    index = faiss.read_index(FAISS_INDEX_FILE)
    meta = np.load(FAISS_META_FILE, allow_pickle=True)
    
    # Search for similar content
    q_emb = get_embedding(query).reshape(1, -1)
    D, I = index.search(q_emb, top_k)
    
    for idx in I[0]:
        m = meta[idx]
        print(f"\n🎯 Best match: {m['title']}")
        print(f"📄 URL: {m['url']}")
        print(f"📝 Snippet: {m['snippet'][:200]}...")
        
        # Launch Chrome with Selenium
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=chrome_options
        )
        
        try:
            print("🌐 Opening webpage...")
            driver.get(m['url'])
            time.sleep(3)  # Wait for initial load
            
            print("⏳ Waiting for page to fully load...")
            
            # Wait for the page to be completely loaded
            driver.execute_script("return document.readyState") == "complete"
            time.sleep(2)  # Additional wait for dynamic content
            
            print("🔍 Starting live content analysis...")
            
            # Find relevant content directly from the live page
            relevant_matches = find_relevant_live_content(driver, query)
            
            if relevant_matches:
                print("🎨 Applying intelligent highlighting...")
                
                successful_count = apply_highlights(driver, relevant_matches)
                
                if successful_count > 0:
                    print(f"\n✅ Successfully highlighted {successful_count}/{len(relevant_matches)} segments!")
                    print("💡 Color Legend:")
                    print("  🟡 Yellow: Highest relevance (>0.60 similarity)")
                    print("  🟢 Light Green: High relevance (>0.50 similarity)")
                    print("  🔵 Light Blue: Medium relevance (>0.45 similarity)")
                    print("  🟦 Light Cyan: Lower relevance (>0.35 similarity)")
                    
                    # Show final count
                    try:
                        time.sleep(1)
                        final_count = driver.execute_script(
                            "return document.querySelectorAll('mark[data-highlight=\"true\"]').length;"
                        )
                        print(f"📊 Total highlights visible on page: {final_count}")
                    except:
                        pass
                        
                else:
                    print("⚠️  No highlights were successfully applied")
                    print("💭 The text content might be dynamically loaded or formatted differently")
            else:
                print("⚠️  No relevant content found on the live webpage")
                print("💭 Try a different search query or check if the page loaded correctly")
            
            print("\n🎉 Analysis complete! The webpage is ready for viewing.")
            print("💡 Hover over highlights to see similarity scores")
            print("📍 The page will auto-scroll to the first highlight")
            print("\nPress Enter to close the browser...")
            input()
            
        except Exception as e:
            print(f"❌ Error during search and highlight: {e}")
            import traceback
            traceback.print_exc()
        finally:
            driver.quit()

# --- MAIN USAGE ---
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python web_history_faiss_search.py build      # Build FAISS index from history")
        print("  python web_history_faiss_search.py search QUERY  # Search and open best match")
    elif sys.argv[1] == "build":
        build_faiss_index()
    elif sys.argv[1] == "search":
        query = " ".join(sys.argv[2:])
        search_and_open(query)
    else:
        print("Unknown command.")