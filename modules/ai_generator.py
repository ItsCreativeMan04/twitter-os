from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
import random

class TweetDraft(BaseModel):
    category: str = Field(description="The category of the tweet (e.g., Trading Psychology, Market Observations)")
    hook_score: int = Field(description="Score from 1-10 on how strong the opening line is")
    tweet_draft: str = Field(description="The actual tweet text in raw Hinglish tone")
    why_it_works: str = Field(description="Brief explanation of why this tweet will perform well")
    authentic_image_idea: str = Field(description="A highly specific suggestion for a real trading chart or P&L screenshot to attach")
    stock_photo_keyword: str = Field(description="A single 1-word keyword (like 'wealth', 'chart', 'mindset') to fetch a stock photo")

class GeneratedTweets(BaseModel):
    tweets: list[TweetDraft] = Field(description="List of exactly 15 generated tweets")

CATEGORIES = [
    "Trading Psychology",
    "Finance Facts",
    "Money Mindset",
    "Investing",
    "Behavioral Finance",
    "Retail Trader Mistakes",
    "Risk Management",
    "Market Observations",
    "Questions/Polls",
    "Contrarian Opinions",
    "Productivity for Traders"
]

class AIGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def generate_tweets(self, golden_dataset: list[str]) -> list[dict]:
        """Generates 15 draft tweets using Gemini."""
        
        # Select 5 random categories to focus on for variety
        selected_categories = random.sample(CATEGORIES, 5)
        
        golden_examples = "\n---\n".join(golden_dataset[:20]) # Limit to 20 to save context if needed
        
        system_instruction = f"""You are an expert Ghostwriter for a successful Option Seller and trader on Twitter.
Your goal is to write 15 highly engaging, raw, and insightful tweets about trading, finance, and mindset.

Tone Rules:
- Write in SIMPLE, clear, and easy-to-understand English so a global audience can connect with it.
- Do NOT use complex jargon or overly academic words.
- Keep the tone conversational, highly motivational, and raw (like a 1-on-1 mentorship session).
- Avoid cringe vocabulary, emojis, and hashtags.
- Keep paragraphs very short (1-2 lines maximum per paragraph).
- Make it scannable and easy to read on mobile.
- Use strong, curiosity-inducing hooks (first lines).

Here are examples of my past best-performing tweets (The Golden Dataset) to understand the core message:
{golden_examples}

Generate exactly 15 fresh tweets. Mimic the core message and style of the examples, but rewrite them in clean, simple English.
Cover these specific categories for this batch: {', '.join(selected_categories)}.
"""

        try:
            response = self.client.models.generate_content(
                model='gemini-flash-latest',
                contents="Generate 15 highly engaging tweets in simple English based on the instructions. For each tweet, suggest a specific screenshot/chart idea, and a 1-word search keyword.",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=GeneratedTweets,
                    temperature=0.8,
                )
            )
            
            # The response.text will be a JSON string matching the GeneratedTweets schema
            data = json.loads(response.text)
            
            # Convert to the dict format expected by our Sheets and DB clients
            formatted_tweets = []
            for t in data.get("tweets", []):
                keyword = t.get("stock_photo_keyword", "trading")
                formatted_tweets.append({
                    "Category": t.get("category"),
                    "Hook Score": t.get("hook_score"),
                    "Tweet Draft": t.get("tweet_draft"),
                    "Why it works": t.get("why_it_works"),
                    "Authentic Image Idea": t.get("authentic_image_idea"),
                    "Stock Photo Link": f"https://unsplash.com/s/photos/{keyword}"
                })
            
            print(f"Successfully generated {len(formatted_tweets)} tweets from Gemini.")
            return formatted_tweets
            
        except Exception as e:
            print(f"Error generating tweets: {e}")
            return []
