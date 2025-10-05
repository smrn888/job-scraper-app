"""
Iranian Job Market Scraper - Fixed CAPTCHA Bypass
Based on working test_jobvision.py approach
"""

import time
import random
import subprocess
import sys
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
import urllib.parse


class FixedJobScraper:
    def __init__(self, headless=False, jobinja_user=None, jobinja_pass=None, 
                 jobvision_user=None, jobvision_pass=None):
        self.setup_browser(headless)
        self.jobs = []
        self.jobinja_user = jobinja_user
        self.jobinja_pass = jobinja_pass
        self.jobvision_user = jobvision_user
        self.jobvision_pass = jobvision_pass
        
    def setup_browser(self, headless):
        """Setup browser with anti-detection"""
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option('prefs', {'profile.default_content_setting_values.notifications': 2})
        
        if headless:
            chrome_options.add_argument('--headless=new')
        
        service = Service(executable_path='chromedriver.exe')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    

    def scrape_jobvision(self, keywords=['هوش مصنوعی', 'machine learning']):
        """Scrape JobVision"""
        print("\n" + "="*60)
        print("SCRAPING JOBVISION")
        print("="*60)
        
        if self.jobvision_user and self.jobvision_pass:
            self.login_to_jobvision()
        else:
            print("\nNo credentials provided")
        
        for keyword in keywords:
            try:
                encoded_keyword = urllib.parse.quote(keyword)
                search_url = f"https://jobvision.ir/jobs/keyword/{encoded_keyword}"
                
                print(f"\nSearching: {keyword}")
                self.driver.get(search_url)
                self.human_delay(5, 7)
                
                for i in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                job_links = soup.find_all('a', href=lambda x: x and '/jobs/' in str(x) and len(str(x)) > 20)
                
                if not job_links:
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
                        job_info = self.extract_jobvision_card_info(parent_container, href)
                        if job_info:
                            unique_jobs[href] = job_info
                
                print(f"   Found {len(unique_jobs)} unique jobs")
                
                for idx, (href, job_info) in enumerate(list(unique_jobs.items())[:10], 1):
                    print(f"\n   Job {idx}/10: {job_info['title']}")
                    
                    details = self.get_jobvision_details(job_info['link'])
                    
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
                    
                    if not any(job['link'] == job_data['link'] for job in self.jobs):
                        self.jobs.append(job_data)
                    
                    self.human_delay(1, 2)

            except Exception as e:
                print(f"   Error: {e}")
                continue

    def extract_jobvision_card_info(self, container, href):
        """Extract JobVision card info"""
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
            
            full_url = href if href.startswith('http') else f"https://jobvision.ir{href}"
            
            if title and len(title) > 5:
                return {
                    'title': title,
                    'company': company,
                    'location': location,
                    'contract_type': contract_type,
                    'link': full_url
                }
            
            return None
            
        except:
            return None
    
        """Get JobVision details"""
        details = {'requirements': 'N/A', 'salary': 'توافقی', 'working_hours': 'استاندارد'}
        
        try:
            self.driver.get(job_url)
            self.human_delay(3, 4)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
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
            
        except:
            pass
        
        return details
    
    def save_to_google_sheets(self, spreadsheet_name='AI_ML_Jobs', credentials_file='credentials.json', your_email=None):
        """Save to Google Sheets"""
        print("\nSaving to Google Sheets...")
        
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            client = gspread.authorize(creds)
            
            try:
                spreadsheet = client.open(spreadsheet_name)
                sheet = spreadsheet.sheet1
                print(f"   Opened: {spreadsheet.url}")
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
            
            new_jobs = [job for job in self.jobs if job['link'] not in existing_links]
            
            if not new_jobs:
                print(f"   No new jobs")
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
            self.save_to_csv_append()
    
    def save_to_csv_append(self, filename='jobs.csv'):
        """Save to CSV"""
        if not self.jobs:
            return
        
        df_new = pd.DataFrame(self.jobs)
        
        if os.path.exists(filename):
            df_existing = pd.read_csv(filename, encoding='utf-8-sig')
            existing_links = set(df_existing['link'].values) if 'link' in df_existing.columns else set()
            df_new = df_new[~df_new['link'].isin(existing_links)]
            
            if len(df_new) == 0:
                return
            
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(filename, index=False, encoding='utf-8-sig')
        else:
            df_new.to_csv(filename, index=False, encoding='utf-8-sig')


def main():
    try:
        keywords = ['هوش مصنوعی', 'machine learning']
        
        scraper.scrape_jobvision(keywords=keywords)
        scraper.scrape_jobinja(keywords=keywords)
        
        if scraper.jobs:
            print(f"\nTotal jobs: {len(scraper.jobs)}")
            scraper.save_to_google_sheets(spreadsheet_name='AI Job Iran')
        
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()