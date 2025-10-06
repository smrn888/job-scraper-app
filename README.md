<<<<<<< HEAD
# job-scraper-app
A Python scraper for collecting AI, Machine Learning, and Data Science job postings from Jobinja & Jobvision-  Scraper to extract AI/ML job details from Job websites and save them to CSV or Google Sheets for further data processing analysis.

=======
# Iranian Job Market Scraper (Jobinja)

A Python scraper to collect job postings (AI/ML/Data Science related) from [Jobinja.ir](https://jobinja.ir).
A Python scraper to collect job postings (AI/ML/Data Science related) from [Jobvision.ir](https://jobvision.ir).

Note: Account required  - Automatically sign in


## Features
- Automatically entering email and password
- ArCaptcha Puzzle Slider Solving (Selenium + OpenCV + Template Matching)
- Scrapes job postings by keyword (e.g., "هوش مصنوعی", "data science").
- Extracts job title, company, location, salary, requirements, and more.
- Saves results to CSV (Jobinja: 'jobs.csv', Jobvision:'jobvision_jobs_fixed').
- (Optional) Save results to Google Sheets with your own credentials.

## Installation
```bash
git clone https://github.com/YOUR_USERNAME/job-scraper.git
cd job-scraper
pip install -r requirements.txt


