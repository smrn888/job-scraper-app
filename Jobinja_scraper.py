#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Iranian Job Market Scraper - Auto-login + Jobinja scraping + Google Sheets
REQUIREMENTS:
pip install selenium beautifulsoup4 gspread oauth2client pandas
"""

import os
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

class JobScraper:
    def __init__(self, headless=False, chromedriver_path='chromedriver.exe'):
        """Initialize the scraper with browser settings"""
        self.chromedriver_path = chromedriver_path
        self.headless = headless
        self.setup_browser(headless)
        self.jobs = []

    def setup_browser(self, headless):
        """Configure Chrome with anti-detection measures"""
        chrome_options = Options()

        # اگر خواستید headless فعال کنید می‌توانید این خط را uncomment کنید
        if headless:
            chrome_options.add_argument('--headless=new')

        # Anti-detection settings
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(executable_path=self.chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Remove webdriver property to help avoid simple bot-detection
        try:
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
                    window.navigator.chrome = { runtime: {} }
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})
                    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]})
                """
            })
        except Exception:
            # fallback for older selenium versions
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception:
                pass

    def human_delay(self, min_seconds=1.0, max_seconds=2.5):
        """Add random delay to mimic human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def auto_login(self, email: str, password: str, site='jobinja'):
        try:
            login_url = "https://jobinja.ir/login/user"
            self.driver.get(login_url)

            # صبر برای لود فیلدها
            email_elem = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "identifier"))
            )
            password_elem = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )

            email_elem.clear()
            email_elem.send_keys(email)
            password_elem.clear()
            password_elem.send_keys(password)

            # دکمه ورود
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='وارد شوید']"))
            )
            login_btn.click()

            # صبر تا تغییر URL بعد از لاگین
            WebDriverWait(self.driver, 15).until(
                EC.url_changes(login_url)
            )

            print("✅ Login successful.")
            self.human_delay(1, 2)
            return True

        except Exception as e:
            print(f"❌ Auto-login failed: {e}")
            return False

    # ----- (بقیه توابع اسکرپینگ شما) -----
    def scrape_jobinja(self, keywords=['machine learning', 'هوش مصنوعی']):
        print("🔍 Scraping Jobinja...")
        for keyword in keywords:
            try:
                search_url = f"https://jobinja.ir/jobs?filters[keywords][]={keyword.replace(' ', '+')}"
                print(f"\n   Searching for: {keyword}")
                self.driver.get(search_url)
                self.human_delay(3, 5)

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                job_cards = soup.find_all('li', class_='c-jobListView__item')

                print(f"   Found {len(job_cards)} job listings")

                for card in job_cards:
                    try:
                        job_data = self.parse_jobinja_card(card)
                        if job_data and not any(job['link'] == job_data['link'] for job in self.jobs):
                            self.jobs.append(job_data)
                            print(f"   ✅ {job_data['title']} - {job_data['company']}")
                    except Exception as e:
                        print(f"   ⚠️ Error parsing job card: {e}")
                        continue

                self.human_delay(2, 4)

            except Exception as e:
                print(f"   ❌ Error scraping Jobinja for '{keyword}': {e}")
                continue

    def parse_jobinja_card(self, card):
        """Parse individual job card from Jobinja - FIXED VERSION"""
        try:
            title_elem = card.find('h2', class_='o-listView__itemTitle')
            if not title_elem:
                return None

            title_link = title_elem.find('a')
            if not title_link:
                return None

            title = title_link.get_text(strip=True)
            job_link = title_link.get('href', '')
            if job_link and job_link.startswith('/'):
                job_link = "https://jobinja.ir" + job_link

            import re
            title = re.sub(r'\([^)]*روز[^)]*\)|\(امروز\)|\(دیروز\)', '', title).strip()

            company_elem = card.find('div', class_='c-jobListView__company')
            company = company_elem.get_text(strip=True) if company_elem else 'N/A'

            location = 'N/A'
            contract_type = 'N/A'
            meta_items = card.find_all('li', class_='c-jobListView__metaItem')
            for item in meta_items:
                text = item.get_text(strip=True)
                if 'تمام‌وقت' in text or 'تمام وقت' in text:
                    contract_type = 'تمام‌وقت'
                elif 'پاره‌وقت' in text or 'پاره وقت' in text:
                    contract_type = 'پاره‌وقت'
                elif 'دورکاری' in text:
                    contract_type = 'دورکاری'
                elif 'پروژه‌ای' in text:
                    contract_type = 'پروژه‌ای'
                elif 'تهران' in text or '،' in text:
                    location = text

            details = self.get_job_details(job_link)

            return {
                'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'title': title,
                'company': company,
                'location': location,
                'requirements': details.get('requirements', 'N/A'),
                'salary': details.get('salary', 'توافقی'),
                'contract_type': contract_type,
                'working_hours': details.get('working_hours', 'استاندارد'),
                'link': job_link,
                'source': 'Jobinja'
            }

        except Exception as e:
            print(f"   Error parsing card: {e}")
            return None

    def get_job_details(self, job_url):
        """Visit individual job page to get detailed information (SAME TAB)"""
        details = {
            'requirements': 'N/A',
            'salary': 'توافقی',
            'working_hours': 'استاندارد'
        }

        try:
            if not job_url:
                return details

            self.driver.get(job_url)
            self.human_delay(2, 3)

            WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extract salary (سعی می‌کنیم چند گزینه معمول را بررسی کنیم)
            salary_section = None
            # common info boxes
            info_boxes = soup.find_all('div', class_='c-infoBox')
            if info_boxes:
                for box in info_boxes:
                    label = box.find('span', class_='c-infoBox__label')
                    value = box.find('span', class_='c-infoBox__value')
                    if label and value:
                        lbl = label.get_text(strip=True)
                        if 'حقوق' in lbl or 'دستمزد' in lbl or 'حقوق' in value.get_text():
                            details['salary'] = value.get_text(strip=True)
                        if 'ساعت کاری' in lbl:
                            details['working_hours'] = value.get_text(strip=True)
            # fallback salary location
            if details['salary'] == 'توافقی':
                try:
                    alt = soup.find('div', class_='c-jobView__meta').get_text(" ", strip=True)
                    if 'تومان' in alt or 'حقوق' in alt:
                        details['salary'] = alt[:200]
                except Exception:
                    pass

            # Extract description / requirements
            desc_section = None
            for candidate_class in ['o-box__text s-jobDesc c-pr40p', 'c-jobView__description', 'o-box__text', 'o-box__content']:
                desc_section = soup.find('div', class_=candidate_class)
                if desc_section:
                    break
            if not desc_section:
                # try a more permissive approach
                possible = soup.find('div', {'id': lambda x: x and 'description' in x})
                if possible:
                    desc_section = possible

            if desc_section:
                desc_text = desc_section.get_text(" ", strip=True)
                details['requirements'] = desc_text[:3000]

        except Exception as e:
            print(f"   Could not fetch details from {job_url}: {e}")

        return details

    def scroll_page(self):
        """Scroll page to load more content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):  # Scroll 3 times
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.human_delay(1, 2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def save_to_google_sheets(self, spreadsheet_name='AI_ML_Jobs', credentials_file='credentials.json'):
        """Save scraped jobs to Google Sheets"""
        print("\n📊 Saving to Google Sheets...")
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            client = gspread.authorize(creds)

            try:
                sheet = client.open(spreadsheet_name).sheet1
            except:
                spreadsheet = client.create(spreadsheet_name)
                sheet = spreadsheet.sheet1
                headers = ['Date Added', 'Job Title', 'Company', 'Location', 'Requirements',
                           'Salary', 'Contract Type', 'Working Hours', 'Job Link', 'Source']
                sheet.append_row(headers)

            try:
                existing_links = set(sheet.col_values(9)[1:])  # Column 9 is Job Link
            except:
                existing_links = set()

            new_jobs = [job for job in self.jobs if job['link'] not in existing_links]

            for job in new_jobs:
                row = [
                    job['date_added'],
                    job['title'],
                    job['company'],
                    job.get('location', 'N/A'),
                    job['requirements'],
                    job['salary'],
                    job['contract_type'],
                    job['working_hours'],
                    job['link'],
                    job['source']
                ]
                sheet.append_row(row)

            print(f"✅ Added {len(new_jobs)} new jobs to Google Sheets")
            print(f"   (Skipped {len(self.jobs) - len(new_jobs)} duplicates)")

        except FileNotFoundError:
            print("❌ credentials.json not found! Falling back to CSV.")
            self.save_to_csv()
        except Exception as e:
            print(f"❌ Error saving to Google Sheets: {e}")
            print("   Falling back to CSV...")
            self.save_to_csv()

    def save_to_csv(self, filename='jobs.csv'):
        """Fallback: Save to CSV file"""
        print(f"\n💾 Saving to {filename}...")
        if self.jobs:
            df = pd.DataFrame(self.jobs)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✅ Saved {len(self.jobs)} jobs to {filename}")
        else:
            print("⚠️ No jobs to save")

    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
        except Exception:
            pass

def main():
    print("🚀 Starting Iranian Job Market Scraper (Auto-login)\n")

    # دریافت ایمیل/پسورد از environment یا ورودی کاربر
    EMAIL = os.environ.get("JOBVISION_EMAIL") or input("Email for JobVision: ").strip()
    PASSWORD = os.environ.get("JOBVISION_PASSWORD") or input("Password for JobVision: ").strip()
    # اگر خواستید از getpass برای عدم نمایش پسورد استفاده کنید:
    # import getpass
    # PASSWORD = os.environ.get("JOBVISION_PASSWORD") or getpass.getpass("Password for JobVision: ").strip()

    scraper = JobScraper(headless=False, chromedriver_path='chromedriver.exe')

    try:
        # ابتدا تلاش برای لاگین خودکار (به Jobinja یا jobvision)
        # اینجا پیش‌فرض را روی jobinja گذاشتم. اگر حساب شما در jobvision است، site='jobvision' بگذارید.
        success = scraper.auto_login(EMAIL, PASSWORD, site='jobinja')
        if not success:
            print("⚠️ Auto-login failed. Continuing anyway (maybe public pages قابل دسترسی هستند).")

        # اجرای اسکرپ Jobinja
        scraper.scrape_jobinja(keywords=[
            'machine learning',
            'هوش مصنوعی',
            'deep learning'
        ])

        # ذخیره نتایج
        if scraper.jobs:
            print(f"\n✅ Total unique jobs found: {len(scraper.jobs)}")
            scraper.save_to_google_sheets()
        else:
            print("\n⚠️ No jobs found")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close()
        print("\n🏁 Scraping complete!")

if __name__ == "__main__":
    main()
