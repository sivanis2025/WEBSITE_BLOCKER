# test_nlp.py
import sys
from models.site_model import analyze_website

print("\n--- TEST 1: Gambling Site ---")
result = analyze_website("www.casino.com")
sys.stdout.flush()
print("Should Block? :", result["should_block"])
print("Category      :", result["category"])
print("Reason        :", result["reason"])

print("\n--- TEST 2: Safe Site ---")
result = analyze_website("www.wikipedia.org")
sys.stdout.flush()
print("Should Block? :", result["should_block"])
print("Category      :", result["category"])
print("Reason        :", result["reason"])

print("\n✅ NLP Test Complete!")

print("\n--- TEST 3: Smart Block Test ---")
from core.blocker import smart_block

result = smart_block("www.casino.com")
print("Blocked?  :", result["blocked"])
print("Category  :", result["category"])
print("Reason    :", result["reason"])