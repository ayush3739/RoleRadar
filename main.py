import os
import json
import hashlib
import re
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import feedparser  # pip install feedparser
from urllib.parse import urljoin
import html
from datetime import datetime
from openpyxl import Workbook

load_dotenv('.env')

# ─── Config ────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SEEN_FILE = "seen_jobs.json"
CONFIG_FILE = "runtime_config.json"

def load_keywords_file(file_path):
    with open(file_path) as f:
        return [k.strip().lower() for k in f if k.strip()]

def save_keywords_file(file_path, keywords):
    with open(file_path, "w") as f:
        for keyword in keywords:
            f.write(f"{keyword}\n")

# Load your keywords
KEYWORDS = load_keywords_file("resume_keywords.txt")
SKILLS_KEYWORDS = load_keywords_file("skills_keywords.txt")

IGNORED_RESUME_KEYWORDS = {
    "computer science",
    "engineering intern",
    "sde intern",
}

ROLE_KEYWORDS = [
    "intern",
    "internship",
    "work from home",
    "wfh",
]

FOCUS_KEYWORDS = [
    "python",
    "gen ai",
    "generative ai",
    "llm",
    "langchain",
    "langgraph",
    "rag",
    "openai",
    "hugging face",
    "fastapi",
    "flask",
    "django",
    "rest api",
    "backend",
    "api",
    "ml",
    "machine learning",
    "data science",
    "nlp",
]

REJECT_KEYWORDS = [
    "hackathon",
    "quiz",
    "quizz",
    "webinar",
    "competition",
    "contest",
    "challenge",
    "event",
    "demo",
]

LOCATION_KEYWORDS = [
    "india",
    "uttar pradesh",
    "noida",
    "lucknow",
    "ghaziabad",
    "meerut",
    "kanpur",
    "prayagraj",
    "agra",
    "remote",
    "work from home",
    "wfh",
]

INDIA_LOCATION_KEYWORDS = [
    "india",
    "uttar pradesh",
    "noida",
    "lucknow",
    "ghaziabad",
    "meerut",
    "kanpur",
    "prayagraj",
    "agra",
]


def normalize_text(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()

def clean_text(value):
    if not value:
        return ""
    text = BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
                return {
                    "top_n": int(data.get("top_n", 10)),
                    "extra_keywords": data.get("extra_keywords", []),
                }
        except (json.JSONDecodeError, ValueError, TypeError):
            return {"top_n": 10, "extra_keywords": []}
    return {"top_n": 10, "extra_keywords": []}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def get_active_keywords(extra_keywords):
    combined = KEYWORDS + [k for k in extra_keywords if isinstance(k, str)]
    return [k.strip().lower() for k in combined if k and k.strip()]

# ─── Load / Save seen jobs ──────────────────────────────
def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE) as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            return set()
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def job_id(url):
    return hashlib.md5(url.encode()).hexdigest()

# ─── Scrapers ───────────────────────────────────────────
def scrape_internshala():
    jobs = []
    base_url = "https://internshala.com/internships/python-internship/"
    headers = {"User-Agent": "Mozilla/5.0"}

    for page_number in range(1, 8):
        if page_number == 1:
            url = base_url
        else:
            url = f"https://internshala.com/internships/python-internship/page-{page_number}/"

        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select("div.individual_internship")
            if not cards:
                print(f"Internshala page {page_number}: 0 cards")
                continue

            for card in cards:
                title_el = card.select_one("h2.job-internship-name")
                link_el = card.select_one("a.job-title-href") or card.select_one("a[href*='/internship/detail/']")
                company_el = card.select_one(".company-name") or card.select_one(".company_name")
                location_el = card.select_one(".locations")
                stipend_el = card.select_one(".stipend")
                description_el = card.select_one(".about_job")
                skill_els = card.select(".job_skill")

                if title_el and link_el:
                    title = title_el.get_text(" ", strip=True)
                    link = urljoin("https://internshala.com", link_el.get("href", ""))
                    jobs.append({
                        "title": title,
                        "link": link,
                        "source": "Internshala",
                        "company": company_el.get_text(" ", strip=True).replace("Actively hiring", "").strip() if company_el else "",
                        "location": location_el.get_text(" ", strip=True) if location_el else "",
                        "stipend": stipend_el.get_text(" ", strip=True) if stipend_el else "",
                        "description": description_el.get_text(" ", strip=True) if description_el else card.get_text(" ", strip=True),
                        "tags": ", ".join(skill.get_text(" ", strip=True) for skill in skill_els),
                    })
        except Exception as e:
            print(f"Internshala page {page_number} error: {e}")
    return jobs

def scrape_unstop():
    jobs = []
    url = "https://unstop.com/api/public/opportunity/search-result?type=jobs&page=1&per_page=20"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        for item in data.get("data", {}).get("data", [])[:15]:
            title = item.get("title", "")
            slug = item.get("public_url", "")
            if slug:
                jobs.append({
                    "title": title,
                    "link": slug,
                    "source": "Unstop",
                    "description": item.get("details", ""),
                    "tags": ", ".join(item.get("tags", [])) if isinstance(item.get("tags"), list) else "",
                })
    except Exception as e:
        print(f"Unstop error: {e}")
    return jobs

def scrape_indeed_rss():
    jobs = []
    queries = [
        "python internship",
        "machine learning internship",
        "web developer internship",
        "work from home python",
        "remote developer",
    ]
    locations = ["India", "Uttar+Pradesh"]
    for q in queries:
        for location in locations:
            url = f"https://www.indeed.com/rss?q={q.replace(' ', '+')}&l={location}&sort=date"
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                jobs.append({
                    "title": entry.title,
                    "link": entry.link,
                    "description": entry.get("summary", ""),
                    "source": f"Indeed ({location.replace('+', ' ')})"
                })
    return jobs

def scrape_remoteok():
    jobs = []
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        for item in data[1:25]:
            title = item.get("position") or item.get("title") or ""
            link = item.get("url") or item.get("apply_url") or ""
            if title and link:
                jobs.append({
                    "title": title,
                    "link": link,
                    "description": item.get("description", ""),
                    "source": "RemoteOK",
                    "tags": ", ".join(item.get("tags", [])) if isinstance(item.get("tags"), list) else "",
                })
    except Exception as e:
        print(f"RemoteOK error: {e}")
    return jobs

def scrape_remotive():
    jobs = []
    url = "https://remotive.com/api/remote-jobs"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        for item in data.get("jobs", [])[:50]:
            title = item.get("title", "")
            link = item.get("url", "")
            if title and link:
                jobs.append({
                    "title": title,
                    "link": link,
                    "description": item.get("description", ""),
                    "source": "Remotive",
                    "company": item.get("company_name", ""),
                    "location": item.get("candidate_required_location", ""),
                    "tags": ", ".join(item.get("tags", [])) if isinstance(item.get("tags"), list) else "",
                })
    except Exception as e:
        print(f"Remotive error: {e}")
    return jobs

def scrape_arbeitnow():
    jobs = []
    url = "https://www.arbeitnow.com/api/job-board-api"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        for item in data.get("data", [])[:50]:
            title = item.get("title", "")
            link = item.get("url", "")
            if title and link:
                jobs.append({
                    "title": title,
                    "link": link,
                    "description": item.get("description", ""),
                    "source": "Arbeitnow",
                    "company": item.get("company_name", ""),
                    "location": item.get("location", ""),
                    "tags": ", ".join(item.get("tags", [])) if isinstance(item.get("tags"), list) else "",
                })
    except Exception as e:
        print(f"Arbeitnow error: {e}")
    return jobs

def collect_jobs():
    scrapers = [
        scrape_internshala,
        scrape_unstop,
        scrape_indeed_rss,
        scrape_remoteok,
        scrape_remotive,
        scrape_arbeitnow,
    ]
    jobs = []
    for scraper in scrapers:
        try:
            scraped = scraper()
            print(f"{scraper.__name__}: {len(scraped)} jobs")
            jobs.extend(scraped)
        except Exception as e:
            print(f"{scraper.__name__} failed: {e}")
    unique = {}
    for job in jobs:
        link = job.get("link", "")
        if link and link not in unique:
            unique[link] = job
    return list(unique.values())

# ─── Keyword matching ───────────────────────────────────
def matches_resume(job):
    fields = [job.get("title", ""), job.get("description", ""), job.get("tags", "")]
    text = normalize_text(" ".join(fields))
    config = load_config()
    active_keywords = get_active_keywords(config.get("extra_keywords", []))
    normalized_keywords = [
        normalize_text(keyword)
        for keyword in active_keywords
        if normalize_text(keyword) not in IGNORED_RESUME_KEYWORDS
    ]
    return any(keyword and keyword in text for keyword in normalized_keywords)

def matches_skills(job):
    fields = [job.get("title", ""), job.get("description", ""), job.get("tags", "")]
    text = normalize_text(" ".join(fields))
    normalized_skills = [normalize_text(skill) for skill in SKILLS_KEYWORDS]
    return any(skill and skill in text for skill in normalized_skills)

def matches_target_role(job):
    text = normalize_text(" ".join([
        job.get("title", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]))
    return any(keyword in text for keyword in ROLE_KEYWORDS)

def matches_target_location(job):
    text = normalize_text(" ".join([
        job.get("title", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]))
    return any(keyword in text for keyword in LOCATION_KEYWORDS)

def is_reject_job(job):
    text = normalize_text(" ".join([
        job.get("title", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]))
    return any(keyword in text for keyword in REJECT_KEYWORDS)

def matches_job_like_terms(job):
    text = normalize_text(" ".join([
        job.get("title", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]))
    job_like_keywords = [
        "developer",
        "engineer",
        "designer",
        "analyst",
        "assistant",
        "fresher",
        "graduate",
        "entry level",
        "support",
        "product",
        "marketing",
        "sales",
        "content",
        "data",
        "tester",
        "qa",
        "writer",
        "journalist",
        "operations",
    ]
    return any(keyword in text for keyword in job_like_keywords)

def is_relevant_job(job):
    if is_reject_job(job):
        return False

    text = normalize_text(" ".join([
        job.get("title", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]))
    role_hit = any(keyword in text for keyword in ROLE_KEYWORDS)
    resume_hit = matches_resume(job)
    skills_hit = matches_skills(job)
    location_text = normalize_text(job.get("location", ""))
    india_location_hit = any(keyword in location_text for keyword in INDIA_LOCATION_KEYWORDS)
    wfh_hit = (
        "work from home" in location_text
        or "wfh" in location_text
        or "remote" in location_text
        or "work from home" in text
        or "wfh" in text
        or "remote" in text
    )

    source = normalize_text(job.get("source", ""))
    if source in {"remotive", "arbeitnow", "remoteok", "unstop"}:
        return wfh_hit and india_location_hit and skills_hit
    return wfh_hit and skills_hit and (role_hit or resume_hit)

def job_paid_status(stipend_text):
    cleaned = normalize_text(stipend_text)
    if not cleaned:
        return "Unknown"
    if "unpaid" in cleaned:
        return "Unpaid"
    if re.search(r"\d", cleaned):
        return "Paid"
    return "Unknown"

def job_match_score(job):
    fields = [job.get("title", ""), job.get("description", ""), job.get("tags", "")]
    text = normalize_text(" ".join(fields))
    config = load_config()
    active_keywords = get_active_keywords(config.get("extra_keywords", []))
    score = 0
    for keyword in FOCUS_KEYWORDS:
        if normalize_text(keyword) in text:
            score += 3
    for skill in SKILLS_KEYWORDS:
        normalized = normalize_text(skill)
        if normalized and normalized in text:
            score += 2
    for keyword in active_keywords:
        normalized = normalize_text(keyword)
        if normalized and normalized not in IGNORED_RESUME_KEYWORDS and normalized in text:
            score += 1
    if "work from home" in normalize_text(job.get("location", "")):
        score += 2
    return score

# ─── Telegram sender ────────────────────────────────────
def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram config missing; skipping notification")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": False
    })
    if not res.ok:
        print(f"Telegram error {res.status_code}: {res.text}")

def send_telegram_document(file_path, caption):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram config missing; skipping document upload")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        res = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={"document": f},
        )
    if not res.ok:
        print(f"Telegram document error {res.status_code}: {res.text}")

def send_telegram_chunks(lines, header):
    if not lines:
        return
    max_len = 3800
    current = header
    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            send_telegram(current)
            current = header + line
        else:
            current += line
    if current.strip() != header.strip():
        send_telegram(current)

def export_jobs_excel(jobs, file_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Jobs"
    sheet.append([
        "Rank",
        "Relevancy Score",
        "Title",
        "Company",
        "Location",
        "Stipend",
        "Paid",
        "Source",
        "Link",
        "Tags",
        "Description",
    ])
    for index, job in enumerate(jobs, start=1):
        stipend = job.get("stipend", "")
        sheet.append([
            index,
            job_match_score(job),
            clean_text(job.get("title", "")),
            clean_text(job.get("company", "")),
            clean_text(job.get("location", "")),
            clean_text(stipend) or "Not listed",
            job_paid_status(stipend),
            clean_text(job.get("source", "")),
            job.get("link", ""),
            clean_text(job.get("tags", "")),
            clean_text(job.get("description", "")),
        ])
    workbook.save(file_path)

def export_all_jobs_excel(jobs, file_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "All Jobs"
    sheet.append([
        "Title",
        "Company",
        "Location",
        "Stipend",
        "Paid",
        "Source",
        "Link",
        "Tags",
        "Description",
    ])
    for job in jobs:
        stipend = job.get("stipend", "")
        sheet.append([
            clean_text(job.get("title", "")),
            clean_text(job.get("company", "")),
            clean_text(job.get("location", "")),
            clean_text(stipend) or "Not listed",
            job_paid_status(stipend),
            clean_text(job.get("source", "")),
            job.get("link", ""),
            clean_text(job.get("tags", "")),
            clean_text(job.get("description", "")),
        ])
    workbook.save(file_path)

# ─── Main ───────────────────────────────────────────────
def main():
    seen = load_seen()
    all_jobs = collect_jobs()
    print(f"Collected {len(all_jobs)} jobs total")

    relevant_jobs = [job for job in all_jobs if is_relevant_job(job)]
    relevant_jobs.sort(key=job_match_score, reverse=True)
    
    new_matches = []
    for job in all_jobs:
        jid = job_id(job["link"])
        if jid not in seen and is_relevant_job(job):
            new_matches.append(job)
            seen.add(jid)

    new_matches.sort(key=job_match_score, reverse=True)
    
    if new_matches:
        config = load_config()
        top_n = config.get("top_n", 15)
        new_matches = new_matches[:top_n]
        header = f"Top {len(new_matches)} jobs matched your resume:\n\n"
        messages = [header]
        for job in new_matches:
            stipend = job.get("stipend", "")
            paid_status = job_paid_status(stipend)
            location = job.get("location", "")
            stipend_line = stipend if stipend else "Not listed"
            description = clean_text(job.get("description", ""))
            description_line = description[:180].strip()
            if description and len(description) > 180:
                description_line += "..."
            messages.append(
                f"📌 {clean_text(job['title'])}\n"
                f"🏢 {clean_text(job.get('company', ''))}\n"
                f"📍 {clean_text(location)}\n"
                f"💰 {clean_text(stipend_line)} ({paid_status})\n"
                f"🌐 {clean_text(job['source'])}\n"
                f"📝 {description_line}\n"
                f"🔗 {job['link']}\n\n"
            )
        send_telegram_chunks(messages[1:], header)
        print(f"Sent {len(new_matches)} new jobs")
    else:
        print("No new matches today")

    if relevant_jobs:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        export_path = f"jobs-{timestamp}.xlsx"
        export_jobs_excel(relevant_jobs, export_path)
        send_telegram_document(export_path, "Full relevant jobs list (Excel)")
        print(f"Exported {len(relevant_jobs)} relevant jobs to {export_path}")

    if all_jobs:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        export_all_path = f"jobs-all-{timestamp}.xlsx"
        export_all_jobs_excel(all_jobs, export_all_path)
        send_telegram_document(export_all_path, "All scraped jobs (Excel)")
        print(f"Exported {len(all_jobs)} total jobs to {export_all_path}")
    
    save_seen(seen)

if __name__ == "__main__":
    main()