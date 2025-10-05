# scraper_funcs.py
"""
Iranian Job Market Scraper - functions version (no class)
Save this file as scraper_funcs.py
"""
import time
import random
import re
from datetime import datetime
import os
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ---------------- Browser / helper ----------------
def create_browser(headless=False, chromedriver_path='chromedriver.exe'):
    """Create and return a Selenium Chrome driver with anti-detection options."""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('prefs', {'profile.default_content_setting_values.notifications': 2})
    if headless:
        chrome_options.add_argument('--headless=new')

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        pass
    return driver


def close_browser(driver):
    try:
        if driver:
            driver.quit()
    except Exception:
        pass


def human_delay(a=1.0, b=2.0):
    """Human-like random delay."""
    time.sleep(random.uniform(a, b))


# ---------------- JobVision scraping ----------------
def scrape_jobvision(driver, keywords=None, jobvision_user=None, jobvision_pass=None, max_per_keyword=10):
    """
    Scrape JobVision for a list of keywords.
    Returns list of job dicts.
    """
    if keywords is None:
        keywords = ['هوش مصنوعی', 'machine learning']

    jobs = []
    print("\n" + "="*60)
    print("SCRAPING JOBVISION")
    print("="*60)

    if jobvision_user and jobvision_pass:
        try:
            login_to_jobvision(driver, jobvision_user, jobvision_pass)
        except Exception as e:
            print("Login to JobVision failed or not implemented:", e)
    else:
        print("\nNo JobVision credentials provided")

    for keyword in keywords:
        try:
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://jobvision.ir/jobs/keyword/{encoded_keyword}"

            print(f"\nSearching: {keyword}")
            driver.get(search_url)
            human_delay(5, 7)

            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_links = soup.find_all('a', href=lambda x: x and '/jobs/' in str(x) and len(str(x)) > 20)

            if not job_links:
                print("   No job links found for this keyword.")
                continue

            unique_jobs = {}
            for link in job_links:
                href = link.get('href', '')
                if '/type/' in href or href in unique_jobs:
                    continue

                parent_container = link.parent
                for _ in range(5):
                    if parent_container and parent_container.parent:
                        parent_container = parent_container.parent
                    else:
                        break

                if parent_container:
                    job_info = extract_jobvision_card_info(parent_container, href)
                    if job_info:
                        unique_jobs[href] = job_info

            print(f"   Found {len(unique_jobs)} unique jobs")

            for idx, (href, job_info) in enumerate(list(unique_jobs.items())[:max_per_keyword], 1):
                print(f"\n   Job {idx}/{min(max_per_keyword, len(unique_jobs))}: {job_info['title']}")
                details = get_jobvision_details(driver, job_info['link'])

                job_data = {
                    'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'title': job_info['title'],
                    'company': job_info['company'],
                    'location': job_info['location'],
                    'requirements': details.get('requirements', 'N/A'),
                    'salary': details.get('salary', 'توافقی'),
                    'contract_type': job_info.get('contract_type', 'N/A'),
                    'working_hours': details.get('working_hours', 'استاندارد'),
                    'link': job_info['link'],
                    'source': 'JobVision'
                }

                if not any(job['link'] == job_data['link'] for job in jobs):
                    jobs.append(job_data)

                human_delay(1, 2)

        except Exception as e:
            print(f"   Error scraping keyword '{keyword}': {e}")
            continue

    return jobs


def extract_jobvision_card_info(container, href):
    """Extract job card info from a JobVision container (BeautifulSoup element)."""
    try:
        title = None
        title_elem = container.find('div', class_=lambda x: x and 'title' in str(x).lower())
        if not title_elem:
            title_elem = container.find(['h2', 'h3', 'h4'])
        if title_elem:
            title = title_elem.get_text(strip=True)

        if not title or len(title) < 10:
            link_elem = container.find('a', href=href)
            if link_elem:
                title = link_elem.get_text(strip=True)

        if title:
            title = re.sub(r'^(فوری|کارفرمای پاسخگو|در حال بررسی)', '', title).strip()

        company = 'N/A'
        company_elem = container.find('div', class_=lambda x: x and 'company' in str(x).lower())
        if not company_elem:
            company_elem = container.find('a', href=lambda x: x and '/companies/' in str(x))
        if company_elem:
            company = company_elem.get_text(strip=True)

        location = 'N/A'
        location_elem = container.find('div', class_=lambda x: x and 'location' in str(x).lower())
        if location_elem:
            location = location_elem.get_text(strip=True)

        contract_type = 'N/A'
        full_url = href if str(href).startswith('http') else f"https://jobvision.ir{href}"

        if title and len(title) > 5:
            return {
                'title': title,
                'company': company,
                'location': location,
                'contract_type': contract_type,
                'link': full_url
            }

        return None
    except Exception:
        return None


def get_jobvision_details(driver, job_url):
    """Open job page and extract details (requirements, salary, hours)."""
    details = {'requirements': 'N/A', 'salary': 'توافقی', 'working_hours': 'استاندارد'}
    try:
        driver.get(job_url)
        human_delay(3, 4)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        combined_text = []

        headings = soup.find_all(['h2', 'h3', 'h4', 'div', 'p'])

        for heading in headings:
            heading_text = heading.get_text(strip=True)
            if 'شاخص' in heading_text and 'کلیدی' in heading_text:
                section = heading.find_next(['div', 'ul', 'section'])
                if section:
                    combined_text.append(section.get_text(" ", strip=True))
                break

        for heading in headings:
            heading_text = heading.get_text(strip=True)
            if 'شرح شغل' in heading_text:
                section = heading.find_next(['div', 'ul', 'section'])
                if section:
                    combined_text.append(section.get_text(" ", strip=True))
                break

        if combined_text:
            details['requirements'] = "\n".join(combined_text)[:5000]

    except Exception:
        pass

    return details


# ---------------- Saveers ----------------
def save_to_google_sheets(jobs, spreadsheet_name='AI_ML_Jobs', credentials_file='credentials.json', your_email=None):
    """Save list of jobs to Google Sheets via service account."""
    print("\nSaving to Google Sheets...")

    if not jobs:
        print("No jobs to save.")
        return

    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)

        try:
            spreadsheet = client.open(spreadsheet_name)
            sheet = spreadsheet.sheet1
            print(f"   Opened spreadsheet")
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create(spreadsheet_name)
            sheet = spreadsheet.sheet1
            if your_email:
                spreadsheet.share(your_email, perm_type='user', role='writer')
            headers = ['Date Added', 'Job Title', 'Company', 'Location', 'Requirements',
                       'Salary', 'Contract Type', 'Working Hours', 'Job Link', 'Source']
            sheet.append_row(headers)

        all_values = sheet.get_all_values()
        existing_links = set(row[8] for row in all_values[1:] if len(row) > 8) if len(all_values) > 1 else set()

        new_jobs = [job for job in jobs if job['link'] not in existing_links]

        if not new_jobs:
            print(f"   No new jobs to add to Google Sheets")
            return

        for job in new_jobs:
            row = [
                job['date_added'], job['title'], job['company'],
                job.get('location', 'N/A'), job['requirements'],
                job['salary'], job['contract_type'], job['working_hours'],
                job['link'], job['source']
            ]
            sheet.append_row(row)

        print(f"   Added {len(new_jobs)} jobs!")

    except Exception as e:
        print(f"   Error: {e}")
        save_to_csv_append(jobs)


def save_to_csv_append(jobs, filename='jobs.csv'):
    """Append jobs to CSV, avoiding duplicates by 'link'."""
    if not jobs:
        return

    df_new = pd.DataFrame(jobs)

    if os.path.exists(filename):
        try:
            df_existing = pd.read_csv(filename, encoding='utf-8-sig')
            existing_links = set(df_existing['link'].values) if 'link' in df_existing.columns else set()
            df_new_filtered = df_new[~df_new['link'].isin(existing_links)]

            if len(df_new_filtered) == 0:
                print("No new rows to append to CSV.")
                return

            df_combined = pd.concat([df_existing, df_new_filtered], ignore_index=True)
            df_combined.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"Appended {len(df_new_filtered)} new rows to {filename}")
        except Exception as e:
            print("Error appending to CSV:", e)
            # fallback: overwrite with all (safe)
            df_all = pd.concat([df_existing, df_new], ignore_index=True)
            df_all.to_csv(filename, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Wrote {len(df_new)} rows to new file {filename}")
