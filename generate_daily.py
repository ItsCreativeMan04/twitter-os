import config
from modules.ai_generator import AIGenerator
from modules.db_client import DBClient
from modules.sheets_client import SheetsClient

def main():
    print("Starting Morning Tweet Generation...")
    
    # 1. Initialize Clients
    sheets = SheetsClient(config.GOOGLE_SHEETS_CREDENTIALS_FILE, config.GOOGLE_SHEET_ID)
    ai = AIGenerator(config.GEMINI_API_KEY)
    db = DBClient(config.SUPABASE_URL, config.SUPABASE_KEY, config.GEMINI_API_KEY)
    
    # 2. Fetch Golden Dataset
    print("Fetching Golden Dataset...")
    golden_dataset = sheets.get_golden_dataset()
    if not golden_dataset:
        print("Warning: Golden Dataset is empty. AI will generate without past context.")
        
    # 3. Generate Drafts
    print("Generating Tweets...")
    drafts = ai.generate_tweets(golden_dataset)
    
    # 4. Filter Duplicates (Semantic Check)
    print("Checking for semantic duplicates...")
    unique_tweets = []
    for draft in drafts:
        tweet_text = draft["Tweet Draft"]
        if not db.is_duplicate(tweet_text, threshold=0.8):
            unique_tweets.append(draft)
        else:
            print(f"Skipped duplicate: {tweet_text[:50]}...")
            
    # 5. Append to Google Sheets
    if unique_tweets:
        print(f"Pushing {len(unique_tweets)} unique tweets to Google Sheets...")
        sheets.append_generated_tweets(unique_tweets)
        print("Done! Have a great morning.")
    else:
        print("No unique tweets generated today.")

if __name__ == "__main__":
    main()
