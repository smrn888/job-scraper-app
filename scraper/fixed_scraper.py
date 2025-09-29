"""
Iranian Job Market Scraper - Jobinja & Jabama
Extracts AI/ML/DL jobs and saves to Google Sheets

REQUIREMENTS:
pip install selenium beautifulsoup4 gspread oauth2client pandas
"""

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
    def __init__(self, headless=False):
        """Initialize the scraper with browser settings"""
        self.setup_browser(headless)
        self.jobs = []
        
    def setup_browser(self, headless):
        """Configure Chrome with anti-detection measures"""
        chrome_options = Options()

        # ❌ فعلاً headless رو نذار
        # if headless:
        #    chrome_options.add_argument('--headless')

        # Anti-detection settings
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(executable_path='chromedriver.exe')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # 🔑 اینجا یک توقف بذار تا خودت لاگین کنی
        print("🔑 لطفاً وارد حساب Jobinja بشو، بعد Enter بزن توی ترمینال...")
        input()
        
    def human_delay(self, min_seconds=2, max_seconds=5):
        """Add random delay to mimic human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
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
            # Find the title link - it's inside h2.o-listView__itemTitle
            title_elem = card.find('h2', class_='o-listView__itemTitle')
            if not title_elem:
                return None
            
            # Get the link and title text
            title_link = title_elem.find('a')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            job_link = title_link.get('href', '')
            
            # Remove date suffix from title (e.g., "(14 روز پیش)" or "(امروز)")
            import re
            title = re.sub(r'\([^)]*روز[^)]*\)|\(امروز\)|\(دیروز\)', '', title).strip()
            
            # Find company name - it's in div.c-jobListView__company
            company_elem = card.find('div', class_='c-jobListView__company')
            company = company_elem.get_text(strip=True) if company_elem else 'N/A'
            
            # Find location - it's in li.c-jobListView__metaItem
            location = 'N/A'
            contract_type = 'N/A'
            
            meta_items = card.find_all('li', class_='c-jobListView__metaItem')
            for item in meta_items:
                text = item.get_text(strip=True)
                # Check for contract type
                if 'تمام‌وقت' in text or 'تمام وقت' in text:
                    contract_type = 'تمام‌وقت'
                elif 'پاره‌وقت' in text or 'پاره وقت' in text:
                    contract_type = 'پاره‌وقت'
                elif 'دورکاری' in text:
                    contract_type = 'دورکاری'
                elif 'پروژه‌ای' in text:
                    contract_type = 'پروژه‌ای'
                # Check for location
                elif 'تهران' in text or '،' in text:
                    location = text
            
            # Get detailed info by visiting the job page
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
            # ✅ برو به لینک در همان تب (نه تب جدید)
            self.driver.get(job_url)
            self.human_delay(2, 3)
            
            # Wait for page to load
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "c-jobView"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract salary
            salary_section = soup.find('div', class_='c-infoBox')
            if salary_section:
                salary_text = salary_section.find('span', class_='c-infoBox__value')
                if salary_text:
                    details['salary'] = salary_text.get_text(strip=True)
            
           # Extract job description / requirements
            desc_section = soup.find('div', class_='o-box__text s-jobDesc c-pr40p')
            if not desc_section:
                desc_section = soup.find('div', class_='c-jobView__description')
            if not desc_section:
                desc_section = soup.find('div', class_='o-box__text')
            if not desc_section:
                desc_section = soup.find('div', class_='o-box__content')

            if desc_section:
                desc_text = desc_section.get_text(" ", strip=True)
                details['requirements'] = desc_text[:3000]  # تا ۳۰۰۰ کاراکتر ذخیره کن
            
            # Extract working hours
            info_boxes = soup.find_all('div', class_='c-infoBox')
            for box in info_boxes:
                label = box.find('span', class_='c-infoBox__label')
                if label and 'ساعت کاری' in label.get_text():
                    value = box.find('span', class_='c-infoBox__value')
                    if value:
                        details['working_hours'] = value.get_text(strip=True)
        
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
            # Setup credentials
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            client = gspread.authorize(creds)
            
            # Open or create spreadsheet
            try:
                sheet = client.open(spreadsheet_name).sheet1
            except:
                spreadsheet = client.create(spreadsheet_name)
                sheet = spreadsheet.sheet1
                # Set headers
                headers = ['Date Added', 'Job Title', 'Company', 'Location', 'Requirements', 
                          'Salary', 'Contract Type', 'Working Hours', 'Job Link', 'Source']
                sheet.append_row(headers)
            
            # Get existing links to avoid duplicates
            try:
                existing_links = set(sheet.col_values(9)[1:])  # Column 9 is Job Link
            except:
                existing_links = set()
            
            new_jobs = [job for job in self.jobs if job['link'] not in existing_links]
            
            # Append new jobs
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
            print("❌ credentials.json not found!")
            print("   Follow setup instructions to create Google Sheets API credentials")
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
        self.driver.quit()

def main():
    """Main execution function"""
    print("🚀 Starting Iranian Job Market Scraper\n")
    
    scraper = JobScraper(headless=False)  # Set True to hide browser
    
    try:
        # Scrape jobs with your preferred keywords
        scraper.scrape_jobinja(keywords=[
            'machine learning'

        ])
        
        # Save results
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
