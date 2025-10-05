import time
import random
import re
import os
import cv2
import numpy as np
import requests
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class FixedJobScraper:
    def __init__(self, email, password, headless=False):
        self.email = email
        self.password = password
        self.jobs = []
        self.setup_browser(headless)

    # 🧭 راه‌اندازی مرورگر
    def setup_browser(self, headless):
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option('prefs', {'profile.default_content_setting_values.notifications': 2})
        if headless:
            chrome_options.add_argument('--headless=new')

        service = Service(executable_path='chromedriver.exe')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # ✅ مرحله لاگین به JobVision (با کپچا)
    def login_to_jobvision(self):
        print("\n========================")
        print("LOGIN TO JOBVISION")
        print("========================")

        self.driver.get("https://account.jobvision.ir/Candidate")
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.NAME, "Username")))

        # ایمیل
        email_input = self.driver.find_element(By.NAME, "Username")
        email_input.send_keys(self.email)
        email_input.send_keys(Keys.ESCAPE)
        time.sleep(0.5)

        continue_btn = self.driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
        self.driver.execute_script("arguments[0].click();", continue_btn)
        time.sleep(2)

        # حل کپچا تا موفقیت
        self.solve_arcaptcha_loop()

        # پسورد
        password_input = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.NAME, "Password"))
        )
        password_input.clear()
        password_input.send_keys(self.password)
        time.sleep(0.5)

        # صبر برای اینکه دکمه ورود بارگذاری شود
        try:
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary"))
            )
        except TimeoutException:
            try:
                login_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary"))
                )
            except TimeoutException:
                raise Exception("❌ دکمه ورود پیدا نشد!")

        self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        time.sleep(0.2)
        self.driver.execute_script("arguments[0].click();", login_button)
        print("🔐 رمز وارد شد و روی ورود کلیک شد.")

        try:
            WebDriverWait(self.driver, 15).until(
                EC.url_contains("jobvision.ir")
            )
            print("🎉 ورود با موفقیت انجام شد ✅")
        except TimeoutException:
            print("⚠️ ورود ممکن است موفق نشده باشد. URL فعلی:", self.driver.current_url)

    # 🧠 حل کپچای ARCaptcha
    def solve_arcaptcha(self):
        """
        حل کپچای پازلی ARCaptcha
        Returns True if successful, False otherwise
        """
        try:
            # منتظر بمان تا iframe کپچا بارگذاری شود
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='arcaptcha']"))
            )
            
            # پیدا کردن iframe کپچا
            captcha_iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='arcaptcha']")
            self.driver.switch_to.frame(captcha_iframe)
            time.sleep(2)

            # پیدا کردن تصاویر پس‌زمینه و قطعه پازل
            bg_img = self.driver.find_element(By.CSS_SELECTOR, "img.captcha-bg")
            piece_img = self.driver.find_element(By.CSS_SELECTOR, "img.captcha-piece")
            
            bg_url = bg_img.get_attribute('src')
            piece_url = piece_img.get_attribute('src')

            # دانلود تصاویر
            bg = self.download_image(bg_url)
            piece = self.download_image(piece_url)

            # پیدا کردن موقعیت شکاف
            gap_x = self.find_gap_position(bg, piece)
            print(f"🎯 موقعیت شکاف: {gap_x}px")

            # پیدا کردن slider
            slider = self.driver.find_element(By.CSS_SELECTOR, ".slider-button")
            
            # کشیدن slider به موقعیت مناسب
            actions = ActionChains(self.driver)
            actions.click_and_hold(slider).perform()
            time.sleep(0.2)
            
            # حرکت به صورت طبیعی‌تر (با تکه‌های کوچک)
            move_distance = gap_x
            steps = random.randint(15, 25)
            for i in range(steps):
                step_size = move_distance / steps
                actions.move_by_offset(step_size, random.uniform(-2, 2)).perform()
                time.sleep(random.uniform(0.01, 0.03))
            
            time.sleep(0.3)
            actions.release().perform()
            
            # برگشت به محتوای اصلی
            self.driver.switch_to.default_content()
            time.sleep(2)
            
            # بررسی موفقیت: آیا کپچا حل شده؟
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "Password"))
                )
                return True
            except TimeoutException:
                return False
                
        except Exception as e:
            print(f"⚠️ خطا در حل کپچا: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False

    # 🧠 حل کپچای ARCaptcha با تلاش مکرر
    def solve_arcaptcha_loop(self, max_attempts=5):
        for attempt in range(1, max_attempts + 1):
            print(f"🧠 تلاش برای حل کپچا... (مرتبه {attempt})")
            try:
                if self.solve_arcaptcha():
                    print("✅ کپچا با موفقیت حل شد")
                    return
            except Exception as e:
                print(f"⚠️ خطا در تلاش {attempt}: {e}")

            # اگه موفق نبود، ریفرش کپچا یا صفحه
            time.sleep(2)
            try:
                # تلاش برای ریفرش کپچا
                refresh_btn = self.driver.find_element(By.CSS_SELECTOR, "#challenge button")
                self.driver.execute_script("arguments[0].click();", refresh_btn)
                time.sleep(2)
            except NoSuchElementException:
                # اگه دکمه refresh نبود، صفحه رو دوباره لود کن
                print("🔄 رفرش صفحه...")
                self.driver.refresh()
                time.sleep(4)

                # بررسی دوباره: آیا فیلد ایمیل برگشته؟
                try:
                    email_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.NAME, "Username"))
                    )
                    email_input.clear()
                    email_input.send_keys(self.email)
                    email_input.send_keys(Keys.ESCAPE)
                    time.sleep(0.5)

                    continue_btn = self.driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
                    self.driver.execute_script("arguments[0].click();", continue_btn)
                    time.sleep(2)
                except TimeoutException:
                    pass

        raise Exception("❌ حل کپچا بعد از چند تلاش ناموفق بود.")

    # 📥 دانلود عکس
    def download_image(self, url):
        r = requests.get(url)
        arr = np.asarray(bytearray(r.content), dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)

    # 🔍 تشخیص موقعیت شکاف پازل با Canny
    def find_gap_position(self, bg, piece):
        bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
        piece_gray = cv2.cvtColor(piece, cv2.COLOR_BGR2GRAY)
        bg_gray = cv2.GaussianBlur(bg_gray, (3, 3), 0)
        piece_gray = cv2.GaussianBlur(piece_gray, (3, 3), 0)
        bg_edges = cv2.Canny(bg_gray, 100, 200)
        piece_edges = cv2.Canny(piece_gray, 100, 200)
        res = cv2.matchTemplate(bg_edges, piece_edges, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        return max_loc[0]

    # 📝 اسکرپینگ بعد از ورود
    def scrape_jobvision(self, keywords=['هوش مصنوعی', 'machine learning']):
        print("\n========================")
        print("SCRAPING JOBVISION")
        print("========================")

        for keyword in keywords:
            encoded = urllib.parse.quote(keyword)
            url = f"https://jobvision.ir/jobs/keyword/{encoded}"
            self.driver.get(url)
            time.sleep(3)

            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            job_links = soup.find_all('a', href=lambda x: x and '/jobs/' in x)

            for link in job_links:
                href = link['href']
                if not href.startswith('http'):
                    href = "https://jobvision.ir" + href

                title = link.get_text(strip=True)
                if not title:
                    continue

                self.jobs.append({
                    'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'title': title,
                    'company': 'N/A',
                    'location': 'N/A',
                    'requirements': 'N/A',
                    'salary': 'N/A',
                    'contract_type': 'N/A',
                    'working_hours': 'N/A',
                    'link': href,
                    'source': 'JobVision'
                })
            print(f"✅ {len(self.jobs)} job(s) found so far.")

    # 💾 ذخیره در CSV
    def save_to_csv_append(self, filename='jobs.csv'):
        if not self.jobs:
            return
        df_new = pd.DataFrame(self.jobs)
        if os.path.exists(filename):
            df_old = pd.read_csv(filename, encoding='utf-8-sig')
            combined = pd.concat([df_old, df_new], ignore_index=True).drop_duplicates('link')
            combined.to_csv(filename, index=False, encoding='utf-8-sig')
        else:
            df_new.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 {len(self.jobs)} شغل ذخیره شد در {filename}")

    def close(self):
        self.driver.quit()


# 🏁 اجرای برنامه
if __name__ == "__main__":
    EMAIL = "your_email@example.com"  # جایگزین کنید
    PASSWORD = "your_password"  # جایگزین کنید

    scraper = FixedJobScraper(email=EMAIL, password=PASSWORD)
    try:
        scraper.login_to_jobvision()
        scraper.scrape_jobvision(keywords=["هوش مصنوعی", "machine learning"])
        scraper.save_to_csv_append("jobs.csv")
    except Exception as e:
        print(f"❌ خطا: {e}")
    finally:
        scraper.close()