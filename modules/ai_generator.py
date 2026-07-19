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
        
        system_instruction = f"""You are an elite Twitter Growth Expert and a highly successful Indian stock market trader.
Your goal is to write highly engaging, raw, and authentic tweets in "Hinglish" (Hindi + English written in Latin script).

Tone Rules:
- NO generic AI motivational BS.
- NO robotic or formal language.
- Use raw, conversational Hinglish (e.g., "Market mein survive karna hai toh...", "Bhai, stop loss hit hone par rona band karo").
- Keep paragraphs very short (1-2 lines maximum per paragraph).
- Make it scannable and easy to read on mobile.
- Use strong, curiosity-inducing hooks (first lines).

Here are examples of my past best-performing tweets (The Golden Dataset) to copy the tone exactly:
{golden_examples}

Generate exactly 15 fresh tweets. Do NOT copy the examples, just use them to understand the tone and formatting style.
Cover these specific categories for this batch: {', '.join(selected_categories)}.
"""

        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash-latest',
                contents="Generate 15 highly engaging Hinglish tweets based on the instructions.",
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
                formatted_tweets.append({
                    "Category": t.get("category"),
                    "Hook Score": t.get("hook_score"),
                    "Tweet Draft": t.get("tweet_draft"),
                    "Why it works": t.get("why_it_works")
                })
            
            print(f"Successfully generated {len(formatted_tweets)} tweets from Gemini.")
            return formatted_tweets
            
        except Exception as e:
            print(f"Error generating tweets: {e}")
            print("--- DEBUG: LISTING AVAILABLE MODELS FOR THIS API KEY ---")
            try:
                for m in self.client.models.list():
                    print(f"Model: {m.name}")
            except Exception as e2:
                print(f"Could not list models: {e2}")
            print("------------------------------------------------------")
            return []
