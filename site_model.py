# =====================================================
#  site_model.py  —  Database + NLP Analysis
# =====================================================

# --- Original imports ---
from config.db import get_db

# --- New NLP imports ---
import re
import requests
from bs4 import BeautifulSoup

# --- DB Setup (your original code) ---
db = get_db()
collection = db["blocked_sites"]


# =====================================================
#  PART 1 — YOUR ORIGINAL DB FUNCTIONS (unchanged)
# =====================================================

def add_site(site_name):
    existing = collection.find_one({"site": site_name})
    if existing:
        print(f"⚠️  {site_name} is already in the list!")
    else:
        collection.insert_one({"site": site_name, "status": "blocked"})
        print(f"✅ {site_name} added successfully!")

def remove_site(site_name):
    result = collection.delete_one({"site": site_name})
    if result.deleted_count > 0:
        print(f"✅ {site_name} removed successfully!")
    else:
        print(f"⚠️  {site_name} not found in the list!")

def get_all_sites():
    sites = [doc["site"] for doc in collection.find()]
    return sites

def display_all_sites():
    sites = get_all_sites()
    if sites:
        print("\n🚫 Blocked Sites List:")
        for i, site in enumerate(sites, 1):
            print(f"  {i}. {site}")
    else:
        print("⚠️  No sites in the blocked list!")


# =====================================================
#  PART 2 — NEW NLP FUNCTIONS
# =====================================================

# Keyword dictionary for each harmful category
CATEGORIES = {
    "adult":        ["xxx", "porn", "nude", "adult", "sex", "erotic"],
    "gambling":     ["casino", "bet", "poker", "lottery", "gamble", "slots"],
    "social_media": ["facebook", "instagram", "twitter", "tiktok", "snapchat"],
    "violence":     ["kill", "gore", "weapon", "murder", "fight", "shooting"],
    "drugs":        ["drug", "cocaine", "weed", "marijuana", "narcotic"],
    "safe":         ["news", "education", "science", "wikipedia", "health"]
}


# --- Function 1: Analyze URL ---
def analyze_url(url):
    """
    Check if the URL itself contains any harmful keywords.
    This is the FASTEST check — no internet needed.
    
    Example:
        Input : www.casino-games.com
        Output: "gambling"
    """
    # Remove symbols, keep only letters and numbers
    url_clean = re.sub(r'[^a-z0-9]', ' ', url.lower())
    print(f"  🔍 Checking URL: {url_clean}")

    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in url_clean:
                print(f"  ✅ URL keyword match: '{keyword}' → {category}")
                return category

    print("  ℹ️  No keyword match in URL")
    return "unknown"


# --- Function 2: Scrape Webpage Content ---
def scrape_content(url):
    """
    Open the website and read its text content.
    Like a browser reading a webpage.
    
    Example:
        Input : www.casino.com
        Output: "Welcome to casino, play poker, bet now..."
    """
    try:
        # Open the website
        headers  = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)

        # Read HTML page
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script/style tags (not needed)
        for tag in soup(["script", "style"]):
            tag.decompose()

        # Extract only visible text
        text = soup.get_text(separator=" ")
        text = re.sub(r'\s+', ' ', text).strip()

        print(f"  📄 Scraped {len(text)} characters")
        return text[:2000]   # Return first 2000 characters only

    except Exception as e:
        print(f"  ❌ Could not scrape website: {e}")
        return ""


# --- Function 3: Classify Text ---
def classify_text(text):
    """
    Count how many times each category's keywords
    appear in the webpage text.
    
    Example:
        Text has: "casino"x5, "bet"x3, "poker"x2
        gambling score = 10  ← highest
        Result: "gambling", 85% confidence
    """
    text_lower = text.lower()
    scores     = {}

    for category, keywords in CATEGORIES.items():
        count          = sum(text_lower.count(kw) for kw in keywords)
        scores[category] = count
        print(f"  📊 {category}: {count} hits")

    # Find best matching category
    best_category = max(scores, key=scores.get)
    total         = sum(scores.values())
    confidence    = round(scores[best_category] / total, 2) if total > 0 else 0.0

    print(f"  🏆 Result: {best_category} ({int(confidence*100)}% confidence)")
    return best_category, confidence


# --- Function 4: Main NLP Analyzer ---
def analyze_website(url):
    """
    MAIN FUNCTION — Full NLP analysis of a website.
    
    Flow:
        1. Check URL keywords  (fast)
        2. Scrape page content (if URL is clean)
        3. Classify the text
        4. Return result dict
    
    Example result:
        {
            "url"         : "www.casino.com",
            "category"    : "gambling",
            "confidence"  : 0.95,
            "should_block": True,
            "reason"      : "URL contains gambling keywords"
        }
    """
    print(f"\n{'='*45}")
    print(f"🔎 Analyzing: {url}")
    print(f"{'='*45}")

    result = {
        "url"         : url,
        "category"    : "unknown",
        "confidence"  : 0.0,
        "should_block": False,
        "reason"      : ""
    }

    # ---- Step 1: Check URL (fast, no internet needed) ----
    url_category = analyze_url(url)

    if url_category != "unknown":
        result["category"]      = url_category
        result["confidence"]    = 0.95
        result["should_block"]  = url_category != "safe"
        result["reason"]        = f"URL contains '{url_category}' keywords"
        return result

    # ---- Step 2: Scrape and analyze page content ----
    print("  🌐 URL looks clean, checking page content...")
    content = scrape_content(url)

    if content:
        category, confidence = classify_text(content)
        result["category"]     = category
        result["confidence"]   = confidence
        result["should_block"] = category != "safe" and confidence > 0.3
        result["reason"]       = f"Page content classified as '{category}'"
    else:
        result["reason"] = "Could not scrape content"

    return result