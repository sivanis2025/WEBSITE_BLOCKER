import platform
from models.site_model import get_all_sites, add_site, analyze_website

REDIRECT = "127.0.0.1"

def get_hosts_path():
    if platform.system() == "Windows":
        return r"C:\Windows\System32\drivers\etc\hosts"
    return "/etc/hosts"


# =====================================================
#  YOUR ORIGINAL FUNCTIONS (unchanged)
# =====================================================

def block_sites():
    """Block all sites from MongoDB in hosts file"""
    sites      = get_all_sites()
    hosts_path = get_hosts_path()

    with open(hosts_path, "r") as f:
        existing_content = f.read()

    with open(hosts_path, "a") as f:
        for site in sites:
            if site not in existing_content:
                f.write(f"{REDIRECT} {site}\n")
                print(f"🚫 Blocked: {site}")
            else:
                print(f"⚠️  {site} already blocked!")

def unblock_sites():
    """Remove all sites from hosts file"""
    sites      = get_all_sites()
    hosts_path = get_hosts_path()

    with open(hosts_path, "r") as f:
        lines = f.readlines()

    with open(hosts_path, "w") as f:
        for line in lines:
            if not any(site in line for site in sites):
                f.write(line)
            else:
                print(f"✅ Unblocked: {line.strip()}")


# =====================================================
#  NEW — NLP SMART BLOCKING FUNCTIONS
# =====================================================

def smart_block(url):
    """
    Use NLP to analyze a URL and block it automatically
    if it is harmful.

    Flow:
        1. Run NLP analysis on the URL
        2. If harmful → add to MongoDB + block in hosts file
        3. If safe    → do nothing

    Example:
        smart_block("www.casino.com")
        → NLP detects gambling
        → Auto blocks it!
    """
    print(f"\n🔎 Running NLP analysis on: {url}")

    # Step 1: Run NLP analysis
    result = analyze_website(url)

    category   = result["category"]
    confidence = int(result["confidence"] * 100)
    reason     = result["reason"]

    print(f"  Category   : {category}")
    print(f"  Confidence : {confidence}%")
    print(f"  Reason     : {reason}")

    # Step 2: Block if harmful
    if result["should_block"]:
        print(f"\n🚫 Harmful site detected! Blocking {url}...")

        # Add to MongoDB
        add_site(url)

        # Add to hosts file
        hosts_path = get_hosts_path()
        with open(hosts_path, "r") as f:
            existing = f.read()

        if url not in existing:
            with open(hosts_path, "a") as f:
                f.write(f"{REDIRECT} {url}\n")
            print(f"✅ {url} blocked in hosts file!")
        else:
            print(f"⚠️  {url} already in hosts file!")

        return {
            "blocked"   : True,
            "category"  : category,
            "confidence": confidence,
            "reason"    : reason
        }

    # Step 3: Safe site — do nothing
    else:
        print(f"\n✅ Site is SAFE — not blocked: {url}")
        return {
            "blocked"   : False,
            "category"  : category,
            "confidence": confidence,
            "reason"    : reason
        }


def smart_unblock(url):
    """
    Remove a specific site from hosts file and MongoDB.
    """
    from models.site_model import remove_site

    # Remove from MongoDB
    remove_site(url)

    # Remove from hosts file
    hosts_path = get_hosts_path()
    with open(hosts_path, "r") as f:
        lines = f.readlines()

    with open(hosts_path, "w") as f:
        for line in lines:
            if url not in line:
                f