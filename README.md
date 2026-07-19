# 🚀 Twitter OS: Operations Playbook

This document is your permanent cheat sheet for how your Twitter OS works, which third-party apps are connected, and how to operate it daily.

## 🏗️ System Architecture

Your Twitter OS runs entirely in the cloud for $0/month. It is composed of 4 main components:

1. **Google Sheets (The User Interface)**
   - **Purpose:** Where you review AI-generated tweets, pick images, and mark tweets as "Posted."
   - **URL:** [Your Google Sheet](https://docs.google.com/spreadsheets/d/1hesoCeiiWJvrAGYQQBzPFgdM3iexZOko0ya_Tw8KFWs/edit)
2. **Google AI Studio / Gemini (The Brain)**
   - **Purpose:** Generates 15 high-quality tweets in simple English daily. It uses the `gemini-flash-latest` model.
   - **URL:** [Google AI Studio](https://aistudio.google.com/) (Where your API key lives)
3. **Supabase (The Memory)**
   - **Purpose:** A Vector Database that stores all your previously posted tweets. It prevents the AI from ever generating repetitive or similar content using semantic search (`gemini-embedding-2`).
   - **URL:** [Supabase Dashboard](https://supabase.com/dashboard/projects)
4. **GitHub Actions (The Engine)**
   - **Purpose:** The server that runs the Python scripts automatically on a schedule. 
   - **URL:** [Your GitHub Repository](https://github.com/ItsCreativeMan04/twitter-os)

---

## 📅 Daily Operations (How to use it)

### 1. The Morning Generation (Automatic)
Every morning at **3:00 AM**, GitHub Actions automatically runs `generate_daily.py`.
- It reads your tone from the **Golden Dataset** tab.
- It generates 15 fresh tweets.
- It checks Supabase to ensure none of them are duplicates.
- It pastes the unique tweets into the **Today's Queue** tab.

### 2. Your Daily Routine (Manual)
When you wake up, open your Google Sheet on your phone or laptop:
1. Go to the **Today's Queue** tab.
2. Read the tweets. If you want to post one, copy the text.
3. Check **Column G** for a suggested authentic chart idea, or click the link in **Column H** to grab a free professional stock photo from Unsplash.
4. Post the tweet on Twitter/X.
5. In your Google Sheet, change the status in **Column E** from `Pending` to `Posted`.

### 3. The Nightly Sync (Automatic)
Every night at **11:00 PM**, GitHub Actions automatically runs `sync_posted.py`.
- It finds every row you marked as `Posted`.
- It uploads those tweets to Supabase so the AI remembers you posted them.
- It deletes those rows from the Google Sheet to keep your queue clean for the next morning.

---

## ⚙️ Manual Overrides

If you don't want to wait for the automatic schedule, you can force the system to run at any time.

**To Generate Tweets Instantly:**
1. Go to your [GitHub Actions Tab](https://github.com/ItsCreativeMan04/twitter-os/actions).
2. Click on **Twitter OS Automation** on the left.
3. Click the **Run workflow** dropdown on the right.
4. Leave the input box empty (it defaults to `generate`) and click the green **Run workflow** button.
5. Wait ~15 seconds, and new tweets will appear in your sheet.

**To Sync Posted Tweets Instantly:**
1. Do the same as above, but type `sync` in the input box before clicking **Run workflow**.

---

## 🗝️ Secrets & Keys Used

If you ever need to reset a password or update a key, these are stored in your GitHub Repository under **Settings > Secrets and variables > Actions**:

- `GEMINI_API_KEY`: Your Google AI Studio token.
- `SUPABASE_URL` & `SUPABASE_KEY`: Your database connection strings.
- `GOOGLE_SHEET_ID`: The ID from your Google Sheet URL.
- `GOOGLE_SHEETS_CREDENTIALS_JSON`: The raw JSON from your Google Cloud Service Account.
