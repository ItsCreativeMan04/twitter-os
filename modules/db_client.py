from supabase import create_client, Client
from google import genai
import config

class DBClient:
    def __init__(self, supabase_url: str, supabase_key: str, gemini_api_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.ai_client = genai.Client(api_key=gemini_api_key)

    def get_embedding(self, text: str) -> list[float]:
        """Generates a text embedding using Gemini."""
        try:
            # Use the available embedding model from the user's debug list
            response = self.ai_client.models.embed_content(
                model='gemini-embedding-2',
                contents=text
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

    def is_duplicate(self, tweet_text: str, threshold: float = 0.8) -> bool:
        """
        Checks if a tweet is semantically similar to any past tweets.
        Returns True if a similar tweet is found (>80% similarity).
        """
        embedding = self.get_embedding(tweet_text)
        if not embedding:
            return False # Fail open if embedding fails
            
        try:
            # Call the Postgres function we created in schema.sql
            response = self.supabase.rpc(
                'match_tweets',
                {'query_embedding': embedding, 'match_threshold': threshold, 'match_count': 1}
            ).execute()
            
            if response.data and len(response.data) > 0:
                print(f"Duplicate found! Similarity: {response.data[0]['similarity']:.2f}")
                return True
            return False
        except Exception as e:
            print(f"Error checking for duplicates: {e}")
            return False

    def save_posted_tweet(self, tweet_text: str, category: str):
        """Saves a published tweet to the database with its embedding."""
        embedding = self.get_embedding(tweet_text)
        if not embedding:
            return False
            
        try:
            data, count = self.supabase.table('tweets').insert({
                'tweet_text': tweet_text,
                'category': category,
                'embedding': embedding
            }).execute()
            return True
        except Exception as e:
            print(f"Error saving tweet to database: {e}")
            return False
