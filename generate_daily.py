import config
from modules.ai_generator import AIGenerator
from modules.db_client import DBClient
from modules.sheets_client import SheetsClient
from difflib import SequenceMatcher

def text_similarity(a: str, b: str) -> float:
    """Calculates text similarity ratio between two strings."""
    a_clean = ''.join(c.lower() for c in a if c.isalnum() or c.isspace())
    b_clean = ''.join(c.lower() for c in b if c.isalnum() or c.isspace())
    if not a_clean or not b_clean:
        return 0.0
    return SequenceMatcher(None, a_clean, b_clean).ratio()

def main():
    print("Starting Morning Tweet Generation...")
    
    # 1. Initialize Clients
    sheets = SheetsClient(config.GOOGLE_SHEETS_CREDENTIALS_FILE, config.GOOGLE_SHEET_ID)
    ai = AIGenerator(config.GEMINI_API_KEY)
    db = DBClient(config.SUPABASE_URL, config.SUPABASE_KEY, config.GEMINI_API_KEY)
    
    # 2. Fetch Golden Dataset and Current Queue
    print("Fetching Golden Dataset and Current Queue...")
    golden_dataset = sheets.get_golden_dataset()
    existing_queued = sheets.get_existing_queued_tweets()
    print(f"Found {len(existing_queued)} tweets already in Today's Queue.")
    if not golden_dataset:
        print("Warning: Golden Dataset is empty. AI will generate without past context.")
        
    # Reference list of all known tweets (queued + golden dataset) to prevent duplicates
    reference_tweets = list(existing_queued) + list(golden_dataset)
        
    # 3. Generate Drafts
    print("Generating Tweets...")
    drafts = ai.generate_tweets(golden_dataset, existing_queued)
    
    # 4. Filter Duplicates (Multi-layer Check)
    print("Checking for duplicate tweets...")
    unique_tweets = []
    for draft in drafts:
        tweet_text = draft.get("Tweet Draft", "")
        if not tweet_text:
            continue
            
        # Check A: Text similarity against existing queue, golden dataset, & current batch
        is_dup = False
        for ref_text in reference_tweets:
            sim = text_similarity(tweet_text, ref_text)
            if sim >= 0.65: # 65% text similarity threshold
                print(f"Skipped duplicate (fuzzy match {sim:.2f}): {tweet_text[:50]}...")
                is_dup = True
                break
                
        if is_dup:
            continue

        # Check B: Vector embedding check in Supabase
        if db.is_duplicate(tweet_text, threshold=0.75):
            print(f"Skipped duplicate (vector match): {tweet_text[:50]}...")
            continue

        # Passed all checks!
        unique_tweets.append(draft)
        reference_tweets.append(tweet_text)
            
    # 5. Append to Google Sheets
    if unique_tweets:
        print(f"Pushing {len(unique_tweets)} unique tweets to Google Sheets...")
        sheets.append_generated_tweets(unique_tweets)
        print("Done! Have a great morning.")
    else:
        print("No unique tweets generated today (all generated tweets were duplicates).")

if __name__ == "__main__":
    main()
