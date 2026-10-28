# 🎯 Role Radar

> Hunts remote internships daily, scores every role against your resume & skills, and drops a ranked shortlist straight to your Telegram — with a full Excel report attached.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-automated-2088FF?logo=github-actions&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-bot-26A5E4?logo=telegram&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ What It Does

Role Radar runs on a daily cron schedule (via GitHub Actions) and:

1. **Scrapes** multiple job boards and RSS feeds for remote / WFH internships
2. **Scores** each listing against your `resume_keywords.txt` and `skills_keywords.txt`
3. **Deduplicates** results across runs using a local `seen_jobs.json` cache
4. **Sends** a ranked top-N shortlist to your Telegram chat
5. **Attaches** a full Excel report (`jobs-YYYYMMDD-HHMMSS.xlsx`) with scores, stipends, links, and tags

---

## 🛠 Tech Stack

| Layer | Tools |
|---|---|
| Scraping | `requests`, `BeautifulSoup4`, `feedparser` |
| Scoring | Keyword matching against resume + skills files |
| Reporting | `openpyxl` (Excel) |
| Delivery | Telegram Bot API |
| Automation | GitHub Actions (daily cron) |

---

## 🚀 Quick Start

### Local

```bash
# 1. Clone and enter the repo
git clone https://github.com/ayush3739/role-radar.git
cd role-radar

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1       # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your credentials
cp .env.example .env             # then fill in the values
```

`.env` template:
```env
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

```bash
# 5. Run
python main.py
```

---

### GitHub Actions (zero-maintenance)

1. Push this repo to GitHub
2. Go to **Settings → Secrets and variables → Actions** and add:
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. The workflow (`.github/workflows/cron.yml`) fires every day at **09:30 UTC** — or trigger it manually from the **Actions** tab

---

## ⚙️ Configuration

| File | Purpose |
|---|---|
| `resume_keywords.txt` | Role-level keywords (e.g. `backend`, `sde`) |
| `skills_keywords.txt` | Skill keywords that boost a listing's score |
| `runtime_config.json` | Runtime overrides — `top_n`, `extra_keywords` |

**`runtime_config.json` example:**
```json
{
  "top_n": 10,
  "extra_keywords": ["gen ai", "backend", "fastapi"]
}
```

---

## 📤 Output

| Output | Description |
|---|---|
| Telegram message | Top-N ranked internships with score, title, company & link |
| Telegram document | `jobs-YYYYMMDD-HHMMSS.xlsx` — full table with all matches |

**Excel columns:** Relevancy Score · Title · Company · Location · Stipend · Source · Link · Tags · Description

---

## 🔍 How Scoring Works

Each listing is matched against two keyword lists:

- **Skills keywords** (`skills_keywords.txt`) — mandatory signals; each hit adds weight
- **Resume keywords** (`resume_keywords.txt`) — role descriptors; used for filtering and scoring
- **Focus keywords** — hardcoded high-value terms (e.g. `python`, `llm`, `fastapi`) that add bonus weight

Listings that contain at least one `ROLE_KEYWORDS` term (`intern`, `wfh`, etc.) and clear a minimum score threshold make the shortlist. The rest are silently dropped.

---

## 🗂 Project Structure

```
role-radar/
├── .github/
│   └── workflows/
│       └── cron.yml          # Daily GitHub Actions workflow
├── main.py                   # Core scraper, scorer & sender
├── resume_keywords.txt        # Your role keywords
├── skills_keywords.txt        # Your skills keywords
├── seen_jobs.json             # Dedup cache (gitignored)
├── requirements.txt
└── .env                      # Secrets (gitignored)
```

---

## 🐛 Troubleshooting

| Symptom | Fix |
|---|---|
| `No new matches today` | All matches already seen — delete or empty `seen_jobs.json` to resend |
| No Telegram message | Check that `.env` / GitHub Secrets are set correctly |
| Empty Excel | Lower your keyword thresholds or add more terms to `skills_keywords.txt` |

---

## 📄 License

MIT — do whatever you want, just don't blame me if you get too many internship offers.
