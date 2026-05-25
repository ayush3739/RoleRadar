# Cron Job Scraper

A scheduled job scraper that finds relevant work-from-home internships, ranks them by your skills, and sends:
- A short Telegram message with the top N jobs
- An Excel file with all relevant jobs and scores

## Setup (Local)

1. Create and activate a virtual environment:

   Windows (PowerShell):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Create a .env file with your Telegram bot info:

   ```text
   TELEGRAM_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

4. Run the script:

   ```powershell
   py main.py
   ```

## Setup (GitHub Actions)

1. Push this repository to GitHub.
2. Add repository secrets:
   - TELEGRAM_TOKEN
   - TELEGRAM_CHAT_ID
3. The workflow runs on a schedule (see .github/workflows/cron.yml). You can also run it manually from the Actions tab.

Notes:
- Excel files are sent to Telegram, not stored as artifacts.
- If you want a different schedule, edit the cron expression in the workflow.

## Configuration

- resume_keywords.txt: role keywords
- skills_keywords.txt: skills you want to match (mandatory)
- runtime_config.json: runtime settings (top_n, extra_keywords)

Example runtime_config.json:
```json
{
  "top_n": 10,
  "extra_keywords": ["gen ai", "backend", "fastapi"]
}
```

## Output

- Telegram message: top N jobs
- Telegram document: jobs-YYYYMMDD-HHMMSS.xlsx

The Excel file includes relevancy score, title, company, location, stipend, source, link, tags, and description.

## Troubleshooting

- If you see "No new matches today", it means all matches were already sent and stored in seen_jobs.json.
- To resend everything, delete seen_jobs.json (or empty it) and run again.
- If your .env is missing, the script will skip Telegram sending.
