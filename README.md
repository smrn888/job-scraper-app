# Iranian Job Market Scraper (Jobinja)

A Python scraper to collect job postings (AI/ML/Data Science related) from [Jobinja.ir](https://jobinja.ir).

## Features
- Scrapes job postings by keyword (e.g. "هوش مصنوعی", "data science").
- Extracts job title, company, location, salary, requirements, and more.
- Saves results to CSV (default: `jobs.csv`).
- (Optional) Save results to Google Sheets with your own credentials.

## Installation
```bash
git clone https://github.com/YOUR_USERNAME/job-scraper.git
cd job-scraper
pip install -r requirements.txt
