"""
Iranian Job Market Scraper - Enhanced Anti-Detection Version
Combines stealth techniques to bypass CAPTCHA detection
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
import urllib.parse

class StealthJobScraper:
    def __init__(self, headless=False, jobinja_user=None, jobinja_pass=None, jobvision_user=None, jobvision_pass=None):
        """Initialize with enhanced stealth settings"""
        self.setup_stealth_browser(headless)
        self.jobs = []
        self.jobinja_user = jobinja_user
        self.jobinja_pass = jobinja_pass
        self.jobvision_user = jobvision_user
        self.jobvision_pass = jobvision_pass
        
    def setup_stealth_browser(self, headless):
        """Configure Chrome with maximum anti-detection"""
        chrome_options = Options()
        
        # Enhanced anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        
        # Realistic user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set preferences
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        if headless:
            chrome_options.add_argument('--headless=new')
        
        service = Service(executable_path='chromedriver.exe')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Advanced stealth scripts
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'fa']});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({state: 'granted'})
                    })
                });
            '''
        })
    
    def human_delay(self, min_seconds=2, max_seconds=5):
        """Enhanced human-like delay with micro-variations"""
        base_delay = random.uniform(min_seconds, max_seconds)
        # Add micro-variations
        micro_delay = random.uniform(0, 0.3)
        time.sleep(base_delay + micro_delay)
    
    def human_type(self, element, text, min_delay=0.08, max_delay=0.2):
        """Type text character by character with human-like timing"""
        for char in text:
            element.send_keys(char)
            # Variable typing speed
            delay = random.uniform(min_delay, max_delay)
            # Occasionally pause (like humans thinking)
            if random.random() < 0.1:
                delay += random.uniform(0.3, 0.8)
            time.sleep(delay)
    
    def human_mouse_move(self, element):
        """Move mouse to element in human-like way"""
        actions = ActionChains(self.driver)
        # Move with offset
        actions.move_to_element_with_offset(
            element, 
            random.randint(-5, 5), 
            random.randint(-5, 5)
        )
        actions.perform()
        time.sleep(random.uniform(0.1, 0.3))
    
    def trigger_events(self, element):
        """Trigger realistic input events"""
        self.driver.execute_script("""
            let el = arguments[0];
            el.dispatchEvent(new Event('focus', {bubbles: true}));
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true}));
            el.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true}));
            el.dispatchEvent(new Event('blur', {bubbles: true}));
        """, element)
    
    def login_to_jobinja(self):
        """Enhanced Jobinja login"""
        print(f"\n🔐 Logging in to Jobinja...")
        
        try:
            self.driver.get("https://jobinja.ir/login/user")
            self.human_delay(4, 6)
            
            # Email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            
            self.human_mouse_move(email_field)
            email_field.click()
            self.human_delay(0.5, 1)
            email_field.clear()
            self.human_type(email_field, self.jobinja_user)
            self.trigger_events(email_field)
            print("   ✓ Email entered")
            self.human_delay(1, 2)
            
            # Password
            password_field = self.driver.find_element(By.NAME, "password")
            self.human_mouse_move(password_field)
            password_field.click()
            self.human_delay(0.5, 1)
            password_field.clear()
            self.human_type(password_field, self.jobinja_pass)
            self.trigger_events(password_field)
            print("   ✓ Password entered")
            self.human_delay(1, 2)
            
            # Submit
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
            )
            self.human_mouse_move(login_button)
            self.driver.execute_script("arguments[0].click();", login_button)
            print("   ✅ Login button clicked")
            
            self.human_delay(5, 7)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "c-header__avatar"))
                )
                print("   ✅ Successfully logged in to Jobinja!")
            except:
                print("   ⚠️ Login verification unclear")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            input("   Please login manually and press ENTER...")
    
    def smart_wait_for_captcha(self, timeout=45):
        """Smart waiting with page interaction to appear human"""
        print("      ⏳ Waiting for page to load (appearing human)...")
        
        start_time = time.time()
        check_interval = 2
        
        while time.time() - start_time < timeout:
            # Random micro-interactions
            if random.random() < 0.3:
                try:
                    # Random scroll
                    scroll_amount = random.randint(-100, 100)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                except:
                    pass
            
            # Check for captcha token
            token = self.driver.execute_script("""
                let tokenInput = document.querySelector('input[name="arcaptcha-token"]');
                return tokenInput ? tokenInput.value : null;
            """)
            
            if token and len(token) > 10:
                print(f"      ✅ Page loaded successfully")
                return True
            
            time.sleep(check_interval)
        
        return False
    
    def login_to_jobvision(self):
        """Enhanced JobVision login with maximum stealth"""
        print(f"\n🔐 Logging in to JobVision (Stealth Mode)...")
        
        try:
            print("   📄 Step 1: Opening login page...")
            self.driver.get("https://jobvision.ir/login")
            self.human_delay(6, 8)
            
            # Simulate human browsing behavior
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            self.human_delay(1, 2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            self.human_delay(1, 2)
            
            print("   📄 Step 2: Entering email (human-like)...")
            try:
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "Username"))
                )
                
                # Human-like interaction
                self.human_mouse_move(email_field)
                time.sleep(random.uniform(0.3, 0.6))
                email_field.click()
                self.human_delay(0.4, 0.7)
                
                # Clear with backspace (more human)
                email_field.clear()
                time.sleep(0.2)
                
                # Type slowly
                self.human_type(email_field, self.jobvision_user, 0.1, 0.25)
                
                # Trigger events
                self.trigger_events(email_field)
                
                print("   ✅ Email entered")
                
            except Exception as e:
                print(f"   ❌ Failed to enter email: {e}")
                return
            
            self.human_delay(2, 3)
            
            print("   📄 Step 3: Continuing to password...")
            # Use mouse click instead of Enter for more human behavior
            try:
                continue_btn = self.driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
                self.human_mouse_move(continue_btn)
                time.sleep(random.uniform(0.2, 0.5))
                continue_btn.click()
            except:
                email_field.send_keys(Keys.ENTER)
            
            print("   ✅ Clicked continue")
            self.human_delay(4, 5)
            
            # Small random mouse movements (appear active)
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                actions = ActionChains(self.driver)
                for _ in range(2):
                    actions.move_by_offset(random.randint(-20, 20), random.randint(-20, 20))
                    actions.perform()
                    time.sleep(random.uniform(0.3, 0.7))
            except:
                pass
            
            print("   📄 Step 4: Entering password (human-like)...")
            try:
                password_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "Password"))
                )
                
                self.human_mouse_move(password_field)
                time.sleep(random.uniform(0.3, 0.6))
                password_field.click()
                self.human_delay(0.4, 0.7)
                
                password_field.clear()
                time.sleep(0.2)
                
                # Type password with variations
                self.human_type(password_field, self.jobvision_pass, 0.1, 0.25)
                
                self.trigger_events(password_field)
                
                print("   ✅ Password entered")
                
            except Exception as e:
                print(f"   ❌ Failed to enter password: {e}")
                return
            
            self.human_delay(2, 3)
            
            # More human-like waiting before submit
            if random.random() < 0.5:
                time.sleep(random.uniform(1, 2))
            
            url_before = self.driver.current_url
            
            print("   📄 Step 5: Submitting (stealth)...")
            
            # Try clicking button with human behavior
            try:
                login_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary"))
                )
                
                # Scroll into view naturally
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", login_btn)
                self.human_delay(0.5, 1)
                
                # Move mouse and click
                self.human_mouse_move(login_btn)
                time.sleep(random.uniform(0.2, 0.5))
                
                # Natural click
                actions = ActionChains(self.driver)
                actions.click(login_btn).perform()
                
                print("   ✅ Login button clicked")
                
            except Exception as e:
                print(f"   ℹ️ Using keyboard: {e}")
                password_field.send_keys(Keys.ENTER)
            
            # Wait and check
            print("   ⏳ Waiting for login to complete...")
            self.human_delay(5, 7)
            
            # Additional wait with interaction
            self.smart_wait_for_captcha(timeout=15)
            
            current_url = self.driver.current_url
            if "account.jobvision.ir" not in current_url:
                print("   ✅ Successfully logged in to JobVision!")
                return
            
            # If still on login page, check for issues
            print("   ℹ️ Checking page status...")
            self.human_delay(3, 5)
            
            if "account.jobvision.ir" not in self.driver.current_url:
                print("   ✅ Login successful!")
            else:
                print("   ⚠️ May need manual intervention...")
                print("   Please check the browser and solve any CAPTCHA if needed")
                input("   Press ENTER after resolving...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print("   Please login manually...")
            input("   Press ENTER after logging in...")

    def scrape_jobinja(self, keywords=['machine learning', 'هوش مصنوعی']):
        """Scrape Jobinja"""
        print("\n" + "="*60)
        print("🔍 SCRAPING JOBINJA")
        print("="*60)
        
        if self.jobinja_user and self.jobinja_pass:
            self.login_to_jobinja()
        else:
            print("\n⚠️ No credentials provided.")
            self.driver.get("https://jobinja.ir")
            input("Press ENTER after logging in...")
        
        for keyword in keywords:
            try:
                search_url = f"https://jobinja.ir/jobs?filters[keywords][]={keyword.replace(' ', '+')}"
                print(f"\n🔎 Searching: {keyword}")
                self.driver.get(search_url)
                self.human_delay(3, 5)

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                job_cards = soup.find_all('li', class_='c-jobListView__item')
                print(f"📋 Found {len(job_cards)} listings")

                for card in job_cards:
                    try:
                        job_data = self.parse_jobinja_card(card)
                        if job_data and not any(job['link'] == job_data['link'] for job in self.jobs):
                            self.jobs.append(job_data)
                            print(f"   ✅ {job_data['title']} - {job_data['company']}")
                    except Exception as e:
                        continue

                self.human_delay(2, 4)

            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

    def parse_jobinja_card(self, card):
        """Parse Jobinja card"""
        try:
            title_elem = card.find('h2', class_='o-listView__itemTitle')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            job_link = title_link.get('href', '')
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
            
            details = self.get_jobinja_details(job_link)
            
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
            return None
    
    def get_jobinja_details(self, job_url):
        """Get Jobinja details"""
        details = {'requirements': 'N/A', 'salary': 'توافقی', 'working_hours': 'استاندارد'}
        
        try:
            self.driver.get(job_url)
            self.human_delay(2, 3)
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "c-jobView"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            salary_section = soup.find('div', class_='c-infoBox')
            if salary_section:
                salary_text = salary_section.find('span', class_='c-infoBox__value')
                if salary_text:
                    details['salary'] = salary_text.get_text(strip=True)
            
            desc_section = soup.find('div', class_='o-box__text s-jobDesc c-pr40p')
            if not desc_section:
                desc_section = soup.find('div', class_='c-jobView__description')
            if not desc_section:
                desc_section = soup.find('div', class_='o-box__text')

            if desc_section:
                desc_text = desc_section.get_text(" ", strip=True)
                details['requirements'] = desc_text[:3000]
            
            info_boxes = soup.find_all('div', class_='c-infoBox')
            for box in info_boxes:
                label = box.find('span', class_='c-infoBox__label')
                if label and 'ساعت کاری' in label.get_text():
                    value = box.find('span', class_='c-infoBox__value')
                    if value:
                        details['working_hours'] = value.get_text(strip=True)
        
        except:
            pass
        
        return details

    def scrape_jobvision(self, keywords=['هوش مصنوعی', 'machine learning']):
        """Scrape JobVision"""
        print("\n" + "="*60)
        print("🔍 SCRAPING JOBVISION")
        print("="*60)
        
        if self.jobvision_user and self.jobvision_pass:
            self.login_to_jobvision()
        else:
            print("\n⚠️ No credentials. Continuing...")
        
        for keyword in keywords:
            try:
                encoded_keyword = urllib.parse.quote(keyword)
                search_url = f"https://jobvision.ir/jobs/keyword/{encoded_keyword}"
                
                print(f"\n🔎 Searching: {keyword}")
                self.driver.get(search_url)
                self.human_delay(5, 7)
                
                # Human-like scrolling
                print("   📜 Loading content...")
                for i in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                job_links = soup.find_all('a', href=lambda x: x and '/jobs/' in str(x) and len(str(x)) > 20)
                print(f"   Found {len(job_links)} job links")
                
                if not job_links:
                    continue
                
                unique_jobs = {}
                for link in job_links:
                    href = link.get('href', '')
                    
                    if '/type/' in href:
                        continue
                    
                    if href and href not in unique_jobs:
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
                
                print(f"   📋 Found {len(unique_jobs)} unique jobs")
                
                for idx, (href, job_info) in enumerate(list(unique_jobs.items())[:10], 1):
                    print(f"\n   --- Job {idx}/10 ---")
                    print(f"   Title: {job_info['title']}")
                    
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
                        print(f"   ✅ Added")
                    
                    self.human_delay(1, 2)

                self.human_delay(2, 4)

            except Exception as e:
                print(f"   ❌ Error: {e}")
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
                title = re.sub(r'^(فوری|کارفرمای پاسخگو|در حال بررسی رزومه ها|امکان دورکاری|امکان جذب کارآموز)', '', title).strip()
            
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
            contract_elem = container.find('span', class_=lambda x: x and 'contract' in str(x).lower())
            if contract_elem:
                contract_type = contract_elem.get_text(strip=True)
            
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
    
    def get_jobvision_details(self, job_url):
        """Get JobVision details"""
        details = {'requirements': 'N/A', 'salary': 'توافقی', 'working_hours': 'استاندارد'}
        
        try:
            self.driver.get(job_url)
            self.human_delay(3, 4)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            combined_text = []
            
            headings = soup.find_all(['h2', 'h3', 'h4', 'div', 'p'])
            
            key_indicators_section = None
            for heading in headings:
                heading_text = heading.get_text(strip=True)
                if 'شاخص' in heading_text and 'کلیدی' in heading_text:
                    key_indicators_section = heading.find_next(['div', 'ul', 'section'])
                    break
            
            if key_indicators_section:
                key_text = key_indicators_section.get_text(" ", strip=True)
                combined_text.append("** شاخص‌های کلیدی **\n" + key_text)
            
            job_desc_section = None
            for heading in headings:
                heading_text = heading.get_text(strip=True)
                if 'شرح شغل' in heading_text:
                    job_desc_section = heading.find_next(['div', 'ul', 'section'])
                    break
            
            if job_desc_section:
                desc_text = job_desc_section.get_text(" ", strip=True)
                combined_text.append("\n** شرح شغل **\n" + desc_text)
            
            if combined_text:
                full_text = "\n".join(combined_text)
                details['requirements'] = full_text[:5000]
            
        except:
            pass
        
        return details
    
    def save_to_google_sheets(self, spreadsheet_name='AI_ML_Jobs', credentials_file='credentials.json', your_email=None):
        """Save to Google Sheets"""
        print("\n📊 Saving to Google Sheets...")
        
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            client = gspread.authorize(creds)
            print("   ✅ Authenticated")
            
            try:
                spreadsheet = client.open(spreadsheet_name)
                sheet = spreadsheet.sheet1
                print(f"   ✅ Opened: {spreadsheet.url}")
            except gspread.SpreadsheetNotFound:
                spreadsheet = client.create(spreadsheet_name)
                sheet = spreadsheet.sheet1
                print(f"   🆕 Created: {spreadsheet.url}")
                
                if your_email:
                    try:
                        spreadsheet.share(your_email, perm_type='user', role='writer')
                        print(f"   ✅ Shared with {your_email}")
                    except:
                        pass
                
                headers = ['Date Added', 'Job Title', 'Company', 'Location', 'Requirements', 
                          'Salary', 'Contract Type', 'Working Hours', 'Job Link', 'Source']
                sheet.append_row(headers)
            
            try:
                all_values = sheet.get_all_values()
                if len(all_values) > 1:
                    existing_links = set(row[8] for row in all_values[1:] if len(row) > 8)
                else:
                    existing_links = set()
            except:
                existing_links = set()
            
            new_jobs = [job for job in self.jobs if job['link'] not in existing_links]
            
            if not new_jobs:
                print(f"   ℹ️ No new jobs ({len(self.jobs)} already exist)")
                return
            
            print(f"   ✏️ Adding {len(new_jobs)} new jobs...")
            added_count = 0
            for job in new_jobs:
                try:
                    row = [
                        job['date_added'], job['title'], job['company'],
                        job.get('location', 'N/A'), job['requirements'],
                        job['salary'], job['contract_type'], job['working_hours'],
                        job['link'], job['source']
                    ]
                    sheet.append_row(row)
                    added_count += 1
                except:
                    continue
            
            print(f"\n   🎉 Added {added_count} new jobs!")
            print(f"   🔗 {spreadsheet.url}")
            
        except FileNotFoundError:
            print("❌ credentials.json not found!")
            self.save_to_csv_append()
        except Exception as e:
            print(f"❌ Error: {e}")
            self.save_to_csv_append()
    
    def save_to_csv_append(self, filename='jobs.csv'):
        """Save to CSV"""
        print(f"\n💾 Saving to {filename}...")
        
        if not self.jobs:
            print("⚠️ No jobs to save")
            return
        
        df_new = pd.DataFrame(self.jobs)
        
        if os.path.exists(filename):
            df_existing = pd.read_csv(filename, encoding='utf-8-sig')
            existing_links = set(df_existing['link'].values) if 'link' in df_existing.columns else set()
            df_new = df_new[~df_new['link'].isin(existing_links)]
            
            if len(df_new) == 0:
                print(f"   ℹ️ No new jobs")
                return
            
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"   ✅ Added {len(df_new)} jobs")
        else:
            df_new.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"   ✅ Created with {len(df_new)} jobs")
    
    def close(self):
        """Close browser"""
        self.driver.quit()


def run_analysis():
    """Run job analysis"""
    print("\n" + "="*60)
    print("📊 RUNNING ANALYSIS")
    print("="*60)
    
    analysis_script = "job_model.py"
    
    if not os.path.exists(analysis_script):
        print(f"⚠️ {analysis_script} not found")
        return
    
    try:
        print(f"🚀 Executing {analysis_script}...")
        subprocess.run([sys.executable, analysis_script], capture_output=False, text=True, check=True)
        print("✅ Analysis complete!")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main execution"""
    print("🚀 Enhanced Job Scraper with Anti-Detection\n")
    
    JOBINJA_EMAIL = "moienblack8888@gmail.com"
    JOBINJA_PASSWORD = "ijyJc.3gemnuwQh"
    JOBVISION_EMAIL = "moienblack8888@gmail.com"
    JOBVISION_PASSWORD = "ijyJc.3gemnuwQh"
    
    scraper = StealthJobScraper(
        headless=False,
        jobinja_user=JOBINJA_EMAIL,
        jobinja_pass=JOBINJA_PASSWORD,
        jobvision_user=JOBVISION_EMAIL,
        jobvision_pass=JOBVISION_PASSWORD
    )
    
    try:
        keywords = ['هوش مصنوعی', 'machine learning']
        
        # Scrape both sites
        scraper.scrape_jobvision(keywords=keywords)
        scraper.scrape_jobinja(keywords=keywords)
        
        if scraper.jobs:
            print(f"\n{'='*60}")
            print(f"✅ Total jobs: {len(scraper.jobs)}")
            print(f"{'='*60}")
            
            scraper.save_to_google_sheets(
                spreadsheet_name='AI Job Iran',
                your_email=None
            )
            
            run_analysis()
        else:
            print("\n⚠️ No jobs found")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        scraper.close()
        print("\n👋 Complete!")


if __name__ == "__main__":
    main()