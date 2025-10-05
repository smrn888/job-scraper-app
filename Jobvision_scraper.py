# jobvision_scraper_fixed.py
import os
import time
import random
import re
import requests
import urllib.parse
from datetime import datetime

import cv2
import numpy as np
from bs4 import BeautifulSoup
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# -----------------------------
# تنظیمات و کلاس اصلی
# -----------------------------
class JobVisionScraper:
    def __init__(self,
                 email: str,
                 password: str,
                 headless: bool = False,
                 chromedriver_path: str = 'chromedriver.exe',
                 max_login_attempts: int = 5,
                 captcha_attempts_per_cycle: int = 3,
                 refresh_cycles: int = 3):
        self.email = email
        self.password = password
        self.jobs = []
        self.scraped_links = set()
        self.chromedriver_path = chromedriver_path
        self.max_login_attempts = max_login_attempts
        self.captcha_attempts = captcha_attempts_per_cycle
        self.refresh_cycles = refresh_cycles
        self.setup_browser(headless)

    def setup_browser(self, headless=False):
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option('prefs', {'profile.default_content_setting_values.notifications': 2})
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--disable-gpu')
        # set a common User-Agent
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0 Safari/537.36"
        )
        if headless:
            chrome_options.add_argument('--headless=new')

        service = Service(executable_path=self.chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            # Hide webdriver flag
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception:
            pass

    # -----------------------------
    # ورود (login) با تلاش‌های بیشتر برای کپچا
    # -----------------------------
    def login_to_jobvision(self):
        login_url = "https://account.jobvision.ir/Candidate"
        print("\n" + "="*60)
        print("LOGIN TO JOBVISION")
        print("="*60)

        for attempt in range(1, self.max_login_attempts + 1):
            print(f"\nAttempt {attempt}/{self.max_login_attempts}")
            try:
                self.driver.get(login_url)
                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.NAME, "Username")))
                time.sleep(0.8)

                # وارد کردن ایمیل
                email_input = self.driver.find_element(By.NAME, "Username")
                email_input.clear()
                email_input.send_keys(self.email)
                time.sleep(0.3)
                # کلیک روی دکمه ادامه (ممکن است `<a>` یا `<button>` باشد)
                clicked = False
                try:
                    continue_btn = self.driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
                    self.driver.execute_script("arguments[0].click();", continue_btn)
                    clicked = True
                except Exception:
                    try:
                        continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
                        self.driver.execute_script("arguments[0].click();", continue_btn)
                        clicked = True
                    except Exception:
                        pass

                if not clicked:
                    print("Couldn't find continue button after email — trying ENTER key")
                    email_input.send_keys(Keys.ENTER)

                time.sleep(2)

                # اکنون ممکن است کپچا ظاهر شده باشد یا فیلد پسورد
                # چرخه‌ی تلاش برای حل کپچا (و در صورت شکست، refresh و وارد کردن ایمیل دوباره)
                login_success = False
                for refresh_try in range(1, self.refresh_cycles + 1):
                    # اگر کپچا هست تلاش می‌کنیم حلش کنیم (تا self.captcha_attempts بار)
                    if self.check_captcha_exists():
                        print(f"Captcha detected — trying to solve (cycle {refresh_try}/{self.refresh_cycles})")
                        solved = self.try_solve_captcha_with_retries()
                        if not solved:
                            print("Auto-solve failed this cycle — refreshing and re-entering email/password")
                            self.driver.refresh()
                            time.sleep(2)
                            # دوباره ایمیل را وارد کن
                            try:
                                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "Username")))
                                e_in = self.driver.find_element(By.NAME, "Username")
                                e_in.clear()
                                e_in.send_keys(self.email)
                                time.sleep(0.5)
                                # click continue again
                                try:
                                    cont = self.driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
                                    self.driver.execute_script("arguments[0].click();", cont)
                                except:
                                    try:
                                        cont = self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
                                        self.driver.execute_script("arguments[0].click();", cont)
                                    except:
                                        e_in.send_keys(Keys.ENTER)
                                time.sleep(2)
                            except Exception as e:
                                print("After refresh couldn't re-enter email:", e)
                                # continue to next refresh cycle
                                continue
                        else:
                            print("Captcha solved (or no longer present).")
                    else:
                        # اگر کپچا نیست، سعی کن پسورد وارد بشه و لاگین کلیک شه
                        pass

                    # اگر فیلد پسورد پیدا شد، واردش کن
                    try:
                        passwd = WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.NAME, "Password")))
                        passwd.clear()
                        passwd.send_keys(self.password)
                        time.sleep(0.6)
                    except TimeoutException:
                        # ممکن است سایت کاربر را مستقیماً وارد کند یا صفحه متفاوت باشد — ادامه
                        pass

                    # تلاش برای کلیک روی دکمه لاگین
                    self._try_click_login_button()

                    # بررسی وضعیت لاگین
                    time.sleep(2.5)
                    if self.is_logged_in():
                        print("Login successful!")
                        return True
                    else:
                        # اگر لاگین نشد، ادامه به چرخه‌ی refresh_try
                        print("Still not logged in after this cycle.")
                        # اگر کپچا دوباره ظاهر شد، حلقه ادامه می‌یابد و refresh انجام می‌شود
                        continue

                # اگر همه refresh_cycles انجام و موفق نشدیم، دوباره از ابتدا تلاش می‌کنیم (attempt loop)
                print(f"Attempt {attempt} finished without successful login.")
            except WebDriverException as e:
                print("WebDriver error during login attempt:", str(e)[:200])
            except Exception as e:
                print("Error in attempt:", str(e)[:200])

            time.sleep(2 + random.random()*2)

        raise Exception("Login failed after multiple attempts")

    def _try_click_login_button(self):
        # helper: تلاش می‌کند دکمه لاگین را کلیک کند (ممکن است چند selector وجود داشته باشد)
        try:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
                self.driver.execute_script("arguments[0].click();", btn)
                return True
            except:
                pass
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, "a.btn-primary")
                self.driver.execute_script("arguments[0].click();", btn)
                return True
            except:
                pass
        except Exception:
            pass
        return False

    def check_captcha_exists(self):
        # بررسی وجود challenge یا دکمه/بلاک کپچا
        possible_selectors = [
            "#challenge", ".captcha", ".slider-container", ".captcha-challenge", ".g-recaptcha"
        ]
        for sel in possible_selectors:
            try:
                elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if elems:
                    return True
            except Exception:
                pass
        # در برخی پیاده‌سازی‌ها تصویری داخل iframe است؛ جلوگیری نمی‌کنیم ولی به صورت پایه بررسی می‌کنیم
        return False

    def try_solve_captcha_with_retries(self):
        # تلاش چندباره برای حل کپچا که متد solve_arcaptcha را فراخوانی می‌کند
        for i in range(1, self.captcha_attempts + 1):
            print(f"Solving captcha (try {i}/{self.captcha_attempts})...")
            try:
                ok = self.solve_arcaptcha()
            except Exception as e:
                ok = False
                print("Captcha solver exception:", str(e)[:150])
            if ok:
                # اگر حل شد، بلافاصله یک تاخیر کوتاه بدیم و ادامه بدیم
                time.sleep(1.2 + random.random()*1.2)
                # در بسیاری از مواقع بعد از حل کپچا، فیلد پسورد ظاهر می‌شود یا لاگین موفق می‌شود
                return True
            else:
                # اگر حل نشد، ممکنه slider برگشته باشه یا challenge مجدد ساخته شده — کمی صبر و تلاش مجدد
                time.sleep(1.0 + random.random()*1.5)
        return False

    # -----------------------------
    # کپچا (ArcCaptcha slider) با OpenCV
    # -----------------------------
    def solve_arcaptcha(self):
        """
        تلاش برای حل کپچاهای تصویری نوع slider:
        1. تصویر پس زمینه و قطعه (puzzle) را دانلود می‌کند
        2. با تطبیق الگو (template matching) موقعیت شکاف را محاسبه می‌کند
        3. اسلایدر را با حرکات کوچک انسانی حرکت می‌دهد
        """
        try:
            time.sleep(1.0)
            # selectors متنوع برای سازگاری با پیاده‌سازی‌های مختلف
            bg_selectors = ["#challenge .tw-relative img", "#challenge img", ".captcha-bg img", ".challenge-bg img"]
            piece_selectors = ["#challenge .tw-absolute img.puzzle", "#challenge img.puzzle", ".captcha-piece img", ".puzzle-img"]
            slider_selectors = ["#challenge .draggable", ".draggable", ".slider", ".handle"]

            bg_url = None
            piece_url = None
            for sel in bg_selectors:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    bg_url = el.get_attribute("src")
                    if bg_url:
                        break
                except Exception:
                    continue

            for sel in piece_selectors:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    piece_url = el.get_attribute("src")
                    if piece_url:
                        break
                except Exception:
                    continue

            if not bg_url or not piece_url:
                # ممکن است captcha در iframe یا با ساختار متفاوت باشد
                print("Couldn't find captcha images by standard selectors.")
                return False

            bg = self.download_image(bg_url)
            piece = self.download_image(piece_url)
            if bg is None or piece is None:
                print("Failed to download captcha images.")
                return False

            target_x = self.find_gap_position(bg, piece)

            # پیدا کردن اسلایدر
            slider_el = None
            for sel in slider_selectors:
                try:
                    slider_el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if slider_el:
                        break
                except:
                    continue

            if slider_el is None:
                print("Slider element not found.")
                return False

            # حرکت انسانی شبیه‌سازی‌شده
            actions = ActionChains(self.driver)
            try:
                actions.click_and_hold(slider_el).perform()
            except Exception:
                # fallback: move to element then click_and_hold
                actions.move_to_element(slider_el).click_and_hold().perform()

            # target_x ممکن است به پیکسل واقعی نیاز داشته باشد (بسته به اندازه تصاویر)
            # ما کمی تخمین و حرکت مرحله‌ای انجام می‌دهیم
            move_x = int(max(0, target_x - 10))  # کمی adjust
            # تقسیم حرکت به گام‌های کوچک با نویز
            steps = max(6, int(move_x / 10))
            remaining = move_x
            for i in range(steps):
                step = int(remaining / (steps - i)) if steps - i > 0 else remaining
                # add micro random
                jitter = random.randint(-2, 3)
                try:
                    actions.move_by_offset(step + jitter, random.randint(-1, 1)).perform()
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mousemove', {bubbles:true}));", slider_el)
                    except:
                        pass
                remaining -= step
                time.sleep(0.03 + random.random()*0.06)

            # final small adjustments
            try:
                actions.move_by_offset(3 + random.randint(0, 5), 0).perform()
            except:
                pass
            time.sleep(0.12 + random.random()*0.2)
            try:
                actions.release().perform()
            except:
                try:
                    actions.release().perform()
                except:
                    pass

            # صبر برای بررسی نتیجه
            time.sleep(2.0 + random.random()*1.5)

            # بررسی این که آیا کپچا حذف شده یا فیلد پسورد ظاهر شده
            if not self.check_captcha_exists():
                return True

            # بعضی مواقع slider باید دوباره حرکت کند؛ در این حالت False برگردان
            return False
        except Exception as e:
            print("Captcha error:", str(e)[:200])
            return False

    def download_image(self, url):
        try:
            r = requests.get(url, timeout=15)
            arr = np.asarray(bytearray(r.content), dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            print("download_image error:", str(e)[:150])
            return None

    def find_gap_position(self, bg, piece, bg_elem):
        bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
        piece_gray = cv2.cvtColor(piece, cv2.COLOR_BGR2GRAY)

        bg_gray = cv2.GaussianBlur(bg_gray, (3, 3), 0)
        piece_gray = cv2.GaussianBlur(piece_gray, (3, 3), 0)

        bg_edges = cv2.Canny(bg_gray, 100, 200)
        piece_edges = cv2.Canny(piece_gray, 100, 200)

        # 1. Template matching gray
        res_gray = cv2.matchTemplate(bg_gray, piece_gray, cv2.TM_CCOEFF_NORMED)

        # 2. Template matching edges
        res_edges = cv2.matchTemplate(bg_edges, piece_edges, cv2.TM_CCOEFF_NORMED)

        # 3. Combine both
        combined = (res_gray * 0.6) + (res_edges * 0.4)
        _, _, _, max_loc = cv2.minMaxLoc(combined)

        # 4. Move to center of the gap
        target_x = max_loc[0] + piece.shape[1] // 2

        # 5. Apply scale factor to match DOM
        bg_dom_width = bg_elem.size['width']
        scale_factor = bg_dom_width / bg.shape[1]
        target_x = int(target_x * scale_factor)

        return target_x


    # -----------------------------
    # چک وضعیت لاگین
    # -----------------------------
    def is_logged_in(self):
        try:
            time.sleep(1.0)
            current_url = self.driver.current_url
            # اگر URL دیگر روی account.jobvision.ir نباشد، احتمالاً وارد شده است
            if "account.jobvision.ir" not in current_url:
                return True
            # اگر فیلدهای Username/Password هنوز وجود دارد => لاگین نشده
            try:
                if self.driver.find_elements(By.NAME, "Username") or self.driver.find_elements(By.NAME, "Password"):
                    return False
            except:
                pass
            return False
        except Exception:
            return False

    # -----------------------------
    # استخراج لینک‌ها (برای صفحات SPA با استفاده از Selenium)
    # -----------------------------
    def scrape_jobvision(self, keywords=['هوش مصنوعی', 'machine learning'], max_jobs_per_keyword=30):
        print("\n" + "="*60)
        print("SCRAPING JOBVISION")
        print("="*60)

        if not self.is_logged_in():
            raise Exception("Not logged in — will not start scraping. Login is required.")

        for keyword in keywords:
            encoded = urllib.parse.quote(keyword)
            url = f"https://jobvision.ir/jobs/keyword/{encoded}"
            print(f"\nSearching: {keyword} -> {url}")
            self.driver.get(url)
            time.sleep(2)

            # تلاش برای scroll تا همه کارت‌ها لود شوند
            for _ in range(4):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.2 + random.random()*1.0)

            # منتظر باش تا حداقل یک لینک job در DOM ظاهر شود
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/jobs/']"))
                )
            except TimeoutException:
                print("No job links appeared after wait — saving debug snapshot.")
                # ذخیره صفحه برای دیباگ (اختیاری)
                try:
                    with open("debug_search_results.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    self.driver.save_screenshot("debug_search_results.png")
                    print("Saved debug_search_results.html and debug_search_results.png")
                except:
                    pass

            anchors = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/']")
            unique_links = []
            seen_ids = set()
            for a in anchors:
                try:
                    href = a.get_attribute("href")
                    if not href:
                        continue
                    href_clean = href.split('?')[0]
                    if '/jobs/' not in href_clean:
                        continue
                    # فیلتر کردن لینک‌هایی که خود صفحه جستجو را نشون می‌دهند
                    if 'keyword' in href_clean and href_clean.endswith('/jobs/keyword'):
                        continue
                    job_id = self.extract_job_id_from_url(href_clean)
                    if job_id not in seen_ids and job_id not in self.scraped_links:
                        seen_ids.add(job_id)
                        unique_links.append(href_clean)
                except Exception:
                    continue

            print(f"Found {len(unique_links)} unique jobs (raw anchors: {len(anchors)})")

            initial_count = len(self.jobs)
            processed = 0
            skipped = 0
            errors = 0

            for idx, job_url in enumerate(unique_links[:max_jobs_per_keyword], 1):
                print(f"\n[{idx}/{min(len(unique_links), max_jobs_per_keyword)}] Processing: {job_url}")
                job_data = self.scrape_job_details(job_url)
                if job_data:
                    job_id = self.extract_job_id_from_url(job_url)
                    if job_id not in self.scraped_links:
                        self.scraped_links.add(job_id)
                        self.jobs.append(job_data)
                        processed += 1
                        print(f"Saved: {job_data['title'][:60]}")
                    else:
                        skipped += 1
                        print("Duplicate - skipped")
                else:
                    errors += 1
                    print("Failed to extract data")
                time.sleep(random.uniform(1.5, 3.0))

            print(f"\nSummary for '{keyword}': Processed={processed}, Duplicates={skipped}, Errors={errors}")
            print(f"{len(self.jobs)-initial_count} jobs extracted for '{keyword}'")

        print(f"\nTotal: {len(self.jobs)} unique jobs")

    # -----------------------------
    # استخراج جزئیات هر آگهی (ترکیبی از Selenium + BeautifulSoup)
    # -----------------------------
    def scrape_job_details(self, url):
        try:
            self.driver.get(url)
            # منتظر title یا عنصر مشخصی که معمولا وجود دارد باش
            possible_title_selectors = [
                "h1", ".job-card-title", ".job-title", "h2", "div.job-title"
            ]
            title = "N/A"
            try:
                for sel in possible_title_selectors:
                    els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if els:
                        candidate = els[0].text.strip()
                        if candidate and len(candidate) > 5:
                            title = candidate
                            break
                # اگر با Selenium چیزی پیدا نشد از BeautifulSoup استفاده کن
                if title == "N/A":
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    for tag in soup.find_all(['h1', 'h2']):
                        txt = tag.get_text(strip=True)
                        if 10 < len(txt) < 150:
                            title = txt
                            break
            except Exception:
                pass

            # تکمیل و تمیز کردن عنوان
            if title != "N/A":
                title = re.split(r'[،\|]', title)[0].strip()
                title = re.sub(r'\s*\d+\s*(روز|ساعت|دقیقه)\s*پیش.*$', '', title)

            # شرکت
            company = "N/A"
            try:
                el = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/companies/']")
                if el:
                    company = el[0].text.strip()
            except:
                pass
            if company == "N/A":
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                ctag = soup.find('a', href=re.compile(r'/companies/'))
                if ctag:
                    company = ctag.get_text(strip=True)

            # متن کامل برای regex fallback
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            full_text = soup.get_text(separator="\n")

            # مکان (location) با regex‌ها و fallback
            location = "N/A"
            location_patterns = [
                r'(تهران)\s*،\s*([^\n،]+)',
                r'(اصفهان)\s*،\s*([^\n،]+)',
                r'(مشهد)\s*،\s*([^\n،]+)',
                r'(شیراز)\s*،\s*([^\n،]+)',
                r'(کرج)\s*،\s*([^\n،]+)',
            ]
            for pattern in location_patterns:
                match = re.search(pattern, full_text)
                if match:
                    location = f"{match.group(1)}، {match.group(2)}"
                    break
            if location == "N/A":
                cities = ['تهران', 'اصفهان', 'شیراز', 'مشهد', 'کرج', 'تبریز']
                for city in cities:
                    if city in full_text:
                        location = city
                        break

            # نوع همکاری و ساعات کاری
            working_hours = "N/A"
            time_pattern = r'(شنبه\s+تا\s+\w+\s+از\s+ساعت\s+[\d:]+\s+تا\s+[\d:]+)'
            time_match = re.search(time_pattern, full_text)
            if time_match:
                working_hours = time_match.group(1)
            elif 'تمام‌وقت' in full_text or 'تمام وقت' in full_text:
                working_hours = 'تمام‌وقت'
            elif 'پاره‌وقت' in full_text:
                working_hours = 'پاره‌وقت'
            elif 'دورکاری' in full_text or 'remote' in full_text.lower():
                working_hours = 'دورکاری'

            contract_type = "N/A"
            if 'تمام وقت' in full_text or 'تمام‌وقت' in full_text:
                contract_type = 'تمام وقت'
            elif 'پاره وقت' in full_text or 'پاره‌وقت' in full_text:
                contract_type = 'پاره وقت'
            elif 'پروژه‌ای' in full_text:
                contract_type = 'پروژه‌ای'
            elif 'قراردادی' in full_text:
                contract_type = 'قراردادی'

            # حقوق
            salary = "N/A"
            salary_patterns = [
                r'(\d+)\s*-\s*(\d+)\s*میلیون\s*تومان',
                r'(\d{1,3}(?:[,،]\d{3})*)\s*تومان',
                r'حقوق[:\s]+(\d+(?:\s*-\s*\d+)?)',
            ]
            for pattern in salary_patterns:
                match = re.search(pattern, full_text)
                if match:
                    salary = match.group(0)
                    break
            if salary == "N/A" and 'توافقی' in full_text:
                salary = 'توافقی'

            # استخراج شرح شغل، شرایط و شاخص‌ها (fallback با جستجوی هدرها)
            requirements_parts = []
            key_indicators = []
            if 'شاخص' in full_text and 'کلیدی' in full_text:
                for header in soup.find_all(['h2', 'h3', 'h4', 'h5', 'strong']):
                    if 'شاخص' in header.get_text() and 'کلیدی' in header.get_text():
                        next_elem = header.find_next_sibling()
                        count = 0
                        while next_elem and count < 10:
                            if next_elem.name in ['h2', 'h3', 'h4', 'h5']:
                                break
                            text = next_elem.get_text(strip=True)
                            if text and len(text) > 10:
                                key_indicators.append(text)
                            next_elem = next_elem.find_next_sibling()
                            count += 1
                        break
            if key_indicators:
                requirements_parts.append("شاخص‌های کلیدی:\n" + "\n".join(f"• {item}" for item in key_indicators))

            job_desc = []
            for header in soup.find_all(['h2', 'h3', 'h4', 'h5', 'strong']):
                header_text = header.get_text(strip=True)
                if any(kw in header_text for kw in ['شرح شغل', 'وظایف', 'مسئولیت']):
                    next_elem = header.find_next_sibling()
                    count = 0
                    while next_elem and count < 12:
                        if next_elem.name in ['h2', 'h3', 'h4', 'h5']:
                            break
                        text = next_elem.get_text(strip=True)
                        if text and len(text) > 10:
                            job_desc.append(text)
                        next_elem = next_elem.find_next_sibling()
                        count += 1
                    break
            if job_desc:
                requirements_parts.append("شرح شغل و وظایف:\n" + "\n".join(f"• {item}" for item in job_desc))

            qualifications = []
            for header in soup.find_all(['h2', 'h3', 'h4', 'h5', 'strong']):
                header_text = header.get_text(strip=True)
                if any(kw in header_text for kw in ['شرایط احراز', 'الزامات', 'مهارت']):
                    next_elem = header.find_next_sibling()
                    count = 0
                    while next_elem and count < 12:
                        if next_elem.name in ['h2', 'h3', 'h4', 'h5']:
                            break
                        text = next_elem.get_text(strip=True)
                        if text and len(text) > 10:
                            qualifications.append(text)
                        next_elem = next_elem.find_next_sibling()
                        count += 1
                    break
            if qualifications:
                requirements_parts.append("شرایط احراز:\n" + "\n".join(f"• {item}" for item in qualifications))

            requirements = "\n\n".join(requirements_parts) if requirements_parts else "N/A"
            if len(requirements) > 2000:
                requirements = requirements[:2000] + "..."

            return {
                'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'title': title,
                'company': company,
                'location': location,
                'requirements': requirements,
                'salary': salary,
                'contract_type': contract_type,
                'working_hours': working_hours,
                'link': url,
                'source': 'JobVision'
            }

        except Exception as e:
            print("Error in scrape_job_details:", str(e)[:200])
            return None

    def extract_job_id_from_url(self, url):
        match = re.search(r'/jobs/(\d+)', url)
        return match.group(1) if match else url

    # -----------------------------
    # ذخیره‌سازی نهایی
    # -----------------------------
    def save_to_excel(self, filename='jobs.xlsx'):
        if not self.jobs:
            print("No jobs to save")
            return

        print(f"\nPreparing to save {len(self.jobs)} jobs...")
        df = pd.DataFrame(self.jobs)
        columns = ['date_added', 'title', 'company', 'location', 'requirements',
                   'salary', 'contract_type', 'working_hours', 'link', 'source']
        df = df[columns]

        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Jobs')
                worksheet = writer.sheets['Jobs']
                worksheet.column_dimensions['A'].width = 20
                worksheet.column_dimensions['B'].width = 40
                worksheet.column_dimensions['C'].width = 30
                worksheet.column_dimensions['D'].width = 25
                worksheet.column_dimensions['E'].width = 60
                worksheet.column_dimensions['F'].width = 25
                worksheet.column_dimensions['G'].width = 20
                worksheet.column_dimensions['H'].width = 30
                worksheet.column_dimensions['I'].width = 50
                worksheet.column_dimensions['J'].width = 15

                from openpyxl.styles import Alignment
                for row in range(2, len(df) + 2):
                    worksheet[f'E{row}'].alignment = Alignment(wrap_text=True, vertical='top')

            print(f"Successfully saved {len(df)} jobs to {filename}")
        except Exception as e:
            print("Error saving Excel:", e)
            csv_filename = filename.replace('.xlsx', '.csv')
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"Saved as CSV backup: {csv_filename}")

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

# -----------------------------
# اجرای نمونه (main)
# -----------------------------
if __name__ == "__main__":
    # توصیه: ایمیل/پسورد را از متغیر محیطی بخوان یا از کاربر بپرس
    EMAIL = os.environ.get("JOBVISION_EMAIL") or input("Email for JobVision: ").strip()
    PASSWORD = os.environ.get("JOBVISION_PASSWORD") or input("Password for JobVision: ").strip()

    scraper = JobVisionScraper(email=EMAIL, password=PASSWORD, headless=False,
                               chromedriver_path='chromedriver.exe',
                               max_login_attempts=5,
                               captcha_attempts_per_cycle=3,
                               refresh_cycles=3)
    try:
        if scraper.login_to_jobvision():
            time.sleep(1)
            # مثال: کلمات کلیدی و حداکثر تعداد را تنظیم کن
            scraper.scrape_jobvision(keywords=["هوش مصنوعی", "machine learning"], max_jobs_per_keyword=30)
            scraper.save_to_excel("jobvision_jobs_fixed.xlsx")
        else:
            print("Login failed, aborting scraping.")
    except Exception as e:
        print("Fatal error:", e)
    finally:
        input("\nPress Enter to close and quit the browser...")
        scraper.close()
