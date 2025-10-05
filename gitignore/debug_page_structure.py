# debug_job_links.py - دیباگ استخراج لینک‌ها
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

EMAIL = "moienblack8888@gmail.com"
PASSWORD = "ijyJc.3gemnuwQh"

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    return driver

driver = setup_driver()

try:
    print("Logging in...")
    driver.get("https://account.jobvision.ir/Candidate")
    time.sleep(3)
    
    # ورود سریع
    email_field = driver.find_element(By.NAME, "Username")
    email_field.send_keys(EMAIL)
    time.sleep(1)
    
    continue_btn = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
    continue_btn.click()
    time.sleep(3)
    
    input("حل کپچا و Enter بزنید...")
    
    # رفتن به صفحه جستجو
    keyword = "هوش مصنوعی"
    url = f"https://jobvision.ir/jobs/keyword/{keyword.replace(' ', '%20')}"
    print(f"\nGoing to: {url}")
    driver.get(url)
    time.sleep(5)
    
    print("\n" + "="*60)
    print("DEBUGGING LINK EXTRACTION")
    print("="*60)
    
    # روش 1: تمام لینک‌ها
    all_links = driver.find_elements(By.TAG_NAME, "a")
    print(f"\n1. Total <a> tags: {len(all_links)}")
    
    # روش 2: لینک‌هایی که /jobs/ دارند
    job_pattern_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/']")
    print(f"2. Links with '/jobs/': {len(job_pattern_links)}")
    
    # روش 3: BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    bs_job_links = soup.find_all('a', href=lambda x: x and '/jobs/' in str(x))
    print(f"3. BeautifulSoup '/jobs/' links: {len(bs_job_links)}")
    
    # نمایش نمونه
    print("\n" + "="*60)
    print("SAMPLE LINKS (first 10)")
    print("="*60)
    
    sample_count = 0
    for link in job_pattern_links[:20]:
        try:
            href = link.get_attribute('href')
            if href and '/jobs/' in href and 'keyword' not in href:
                # استخراج ID
                import re
                match = re.search(r'/jobs/(\d+)/', href)
                job_id = match.group(1) if match else 'NO_ID'
                
                # استخراج عنوان
                text = link.text.strip()[:50]
                
                print(f"\n{sample_count + 1}. ID: {job_id}")
                print(f"   URL: {href[:100]}")
                print(f"   Text: {text}")
                
                sample_count += 1
                if sample_count >= 10:
                    break
        except:
            continue
    
    if sample_count == 0:
        print("\nNO VALID JOB LINKS FOUND!")
        print("\nChecking page structure...")
        
        # بررسی ساختار صفحه
        print("\nPage URL:", driver.current_url)
        print("\nPage Title:", driver.title)
        
        # ذخیره HTML برای بررسی
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("\nPage source saved to: debug_page_source.html")
        
        # اسکرین‌شات
        driver.save_screenshot('debug_screenshot.png')
        print("Screenshot saved to: debug_screenshot.png")
        
        # بررسی کلاس‌های احتمالی
        print("\nChecking common job card classes...")
        common_classes = [
            'job-card',
            'job-item',
            'JobCard',
            'job-list-item',
            'search-result'
        ]
        
        for cls in common_classes:
            elements = driver.find_elements(By.CSS_SELECTOR, f"[class*='{cls}']")
            if elements:
                print(f"  Found {len(elements)} elements with '{cls}'")
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    
    input("\nPress Enter to close...")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to close...")
finally:
    driver.quit()