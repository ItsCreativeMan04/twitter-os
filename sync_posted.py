import config
from modules.db_client import DBClient
from modules.sheets_client import SheetsClient

def main():
    print("Starting Nightly Sync...")
    
    # 1. Initialize Clients
    sheets = SheetsClient(config.GOOGLE_SHEETS_CREDENTIALS_FILE, config.GOOGLE_SHEET_ID)
    db = DBClient(config.SUPABASE_URL, config.SUPABASE_KEY, config.GEMINI_API_KEY)
    
    # 2. Find posted tweets in Google Sheets
    print("Fetching posted tweets from 'Today's Queue'...")
    posted_tweets = sheets.get_posted_tweets()
    
    success_count = 0
    if posted_tweets:
        print(f"Found {len(posted_tweets)} posted tweets. Saving to database...")
        for tweet in posted_tweets:
            tweet_text = tweet.get("Tweet Draft")
            category = tweet.get("Category", "Unknown")
            
            if tweet_text:
                if db.save_posted_tweet(tweet_text, category):
                    success_count += 1
                    
        print(f"Successfully saved {success_count}/{len(posted_tweets)} tweets to Supabase.")
    else:
        print("No tweets marked as 'Posted' today.")
    
    # 3. Clean up Google Sheet (This removes both 'Posted' and 'Skipped')
    print("Cleaning up Google Sheet (Removing Posted and Skipped rows)...")
    sheets.remove_posted_tweets()
    print("Cleanup complete.")

if __name__ == "__main__":
    main()
