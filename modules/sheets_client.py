import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime

from datetime import timezone, timedelta

# Scope for Google Sheets and Drive
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

class SheetsClient:
    def __init__(self, credentials_file: str, sheet_id: str):
        self.credentials_file = credentials_file
        self.sheet_id = sheet_id
        self.client = self._authenticate()
        self.sheet = self._open_sheet()

    def _authenticate(self):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, SCOPE)
            client = gspread.authorize(creds)
            return client
        except Exception as e:
            print(f"Error authenticating to Google Sheets: {e}")
            raise e

    def _open_sheet(self):
        try:
            return self.client.open_by_key(self.sheet_id)
        except Exception as e:
            print(f"Error opening spreadsheet {self.sheet_id}: {e}")
            raise e

    def get_golden_dataset(self) -> list[str]:
        """Reads the 'Golden Dataset' tab to fetch past best tweets for AI context."""
        try:
            worksheet = self.sheet.worksheet("Golden Dataset")
            records = worksheet.get_all_records()
            return [str(record.get("Tweet", "")) for record in records if record.get("Tweet")]
        except gspread.exceptions.WorksheetNotFound:
            print("Worksheet 'Golden Dataset' not found. Returning empty list.")
            return []

    def append_generated_tweets(self, tweets: list[dict]):
        """
        Appends newly generated tweets to 'Today's Queue'.
        Expected dict format: {"Category": str, "Hook Score": int, "Tweet Draft": str, "Why it works": str}
        """
        try:
            worksheet = self.sheet.worksheet("Today's Queue")
        except gspread.exceptions.WorksheetNotFound:
            # Create if it doesn't exist
            worksheet = self.sheet.add_worksheet(title="Today's Queue", rows="100", cols="8")
            headers = ["Date", "Category", "AI Hook Score", "Tweet Draft", "Status", "Why it works", "AI Image Prompt", "Stock Photo Link"]
            worksheet.append_row(headers)

        rows = []
        # Fix UTC timezone issue (add 5.5 hours for IST)
        ist_offset = timedelta(hours=5, minutes=30)
        ist_time = datetime.datetime.now(timezone.utc) + ist_offset
        today = ist_time.strftime("%Y-%m-%d")
        for tweet in tweets:
            rows.append([
                today,
                tweet.get("Category", ""),
                tweet.get("Hook Score", ""),
                tweet.get("Tweet Draft", ""),
                "Queued",
                tweet.get("Why it works", ""),
                tweet.get("AI Image Prompt", ""),
                tweet.get("Stock Photo Link", "")
            ])
        
        if rows:
            worksheet.append_rows(rows)
            print(f"Appended {len(rows)} tweets to Today's Queue.")
            
        # Apply Dropdown Data Validation to Column E (Status)
        try:
            body = {
                "requests": [
                    {
                        "setDataValidation": {
                            "range": {
                                "sheetId": worksheet.id,
                                "startRowIndex": 1,
                                "startColumnIndex": 4, # Column E (0-indexed)
                                "endColumnIndex": 5
                            },
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_LIST",
                                    "values": [
                                        {"userEnteredValue": "Queued"},
                                        {"userEnteredValue": "Posted"},
                                        {"userEnteredValue": "Skipped"}
                                    ]
                                },
                                "showCustomUi": True,
                                "strict": True
                            }
                        }
                    }
                ]
            }
            self.sheet.batch_update(body)
        except Exception as e:
            print(f"Could not apply data validation: {e}")

    def get_posted_tweets(self) -> list[dict]:
        """
        Reads 'Today's Queue' and returns rows where Status is 'Posted'.
        This is used by the sync script to move them to the vector DB.
        """
        try:
            worksheet = self.sheet.worksheet("Today's Queue")
            records = worksheet.get_all_records()
            posted = [row for row in records if str(row.get("Status", "")).lower() == "posted"]
            return posted
        except gspread.exceptions.WorksheetNotFound:
            return []
            
    def remove_posted_tweets(self):
        """
        Removes rows from 'Today's Queue' where Status is 'Posted' or 'Skipped'.
        Call this AFTER saving posted ones to Supabase.
        """
        try:
            worksheet = self.sheet.worksheet("Today's Queue")
            records = worksheet.get_all_records()
            # Iterate backwards to safely delete rows
            # gspread is 1-indexed, plus 1 for header row
            for i in range(len(records), 0, -1):
                status = str(records[i-1].get("Status", "")).lower()
                if status in ["posted", "skipped"]:
                    worksheet.delete_rows(i + 1)
        except Exception as e:
            print(f"Error removing posted tweets: {e}")
