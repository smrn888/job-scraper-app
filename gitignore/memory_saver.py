# record_captcha_solutions.py - ضبط راه‌حل کپچاها
"""
این اسکریپت راه‌حل‌ها را یاد می‌گیرد:
1. شما هر کپچا را حل می‌کنید
2. اسکریپت حرکات شما را ضبط می‌کند  
3. دفعه بعد خودش حل می‌کند
"""
import json
import time
import cv2
import numpy as np
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io

EMAIL = "moienblack8888@gmail.com"
PASSWORD = "ijyJc.3gemnuwQh"
LOGIN_URL = "https://www.jobvision.ir/login"

SOLUTIONS_FILE = Path("captcha_solutions.json")
TEMPLATES_DIR = Path("captcha_templates")
TEMPLATES_DIR.mkdir(exist_ok=True)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
        })
    except:
        pass
    
    return driver

def get_canvas_screenshot(driver):
    """گرفتن عکس از canvas"""
    canvas = driver.find_element(By.TAG_NAME, "canvas")
    screenshot = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(screenshot))
    
    loc = canvas.location
    size = canvas.size
    left, top = int(loc['x']), int(loc['y'])
    right, bottom = left + int(size['width']), top + int(size['height'])
    
    cropped = img.crop((left, top, right, bottom))
    return cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)

def compute_image_hash(img):
    """محاسبه hash ساده برای تصویر"""
    # تبدیل به grayscale و resize
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (32, 32))
    
    # محاسبه average hash
    avg = resized.mean()
    hash_bits = (resized > avg).astype(int)
    
    # تبدیل به string
    return ''.join(str(b) for b in hash_bits.flatten())

def load_solutions():
    """بارگذاری راه‌حل‌های ذخیره شده"""
    if SOLUTIONS_FILE.exists():
        with open(SOLUTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_solutions(solutions):
    """ذخیره راه‌حل‌ها"""
    with open(SOLUTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(solutions, f, indent=2, ensure_ascii=False)

def find_matching_solution(current_img, solutions):
    """پیدا کردن راه‌حل مطابق"""
    current_hash = compute_image_hash(current_img)
    
    best_match = None
    min_distance = float('inf')
    
    for img_hash, solution in solutions.items():
        # محاسبه hamming distance
        distance = sum(c1 != c2 for c1, c2 in zip(current_hash, img_hash))
        
        if distance < min_distance:
            min_distance = distance
            best_match = solution
    
    # اگر شباهت بالا باشد
    similarity = 1 - (min_distance / len(current_hash))
    
    if similarity > 0.85:  # 85% شباهت
        return best_match, similarity
    
    return None, 0

def record_manual_solution(driver):
    """ضبط راه‌حل دستی کاربر"""
    print("\n📹 ضبط راه‌حل...")
    print("حالا کپچا را حل کنید")
    print("من منتظرم تا ببینم چطور حل می‌کنید...")
    
    # عکس قبل از حل
    img_before = get_canvas_screenshot(driver)
    cv2.imwrite('before_solve.png', img_before)
    img_hash = compute_image_hash(img_before)
    
    # منتظر حل شدن
    print("منتظر می‌مانم...")
    
    try:
        # وقتی canvas ناپدید شد = حل شد
        WebDriverWait(driver, 120).until(
            EC.invisibility_of_element_located((By.TAG_NAME, "canvas"))
        )
        
        print("✅ کپچا حل شد!")
        
        # ذخیره راه‌حل (فعلاً فقط hash)
        solution = {
            "hash": img_hash,
            "method": "manual",
            "timestamp": time.time()
        }
        
        return img_hash, solution
        
    except Exception as e:
        print(f"خطا: {e}")
        return None, None

def auto_solve_captcha(driver, solutions):
    """حل خودکار با استفاده از راه‌حل‌های یاد گرفته شده"""
    print("\n🤖 تلاش حل خودکار...")
    
    try:
        current_img = get_canvas_screenshot(driver)
        cv2.imwrite('current_captcha.png', current_img)
        
        solution, similarity = find_matching_solution(current_img, solutions)
        
        if solution:
            print(f"✅ راه‌حل پیدا شد! (شباهت: {similarity:.1%})")
            print("⚠️ متأسفانه بخش اجرای راه‌حل هنوز کامل نشده")
            print("💡 برای حل کامل، نیاز به ضبط حرکات ماوس است")
            return False
        else:
            print("❌ راه‌حل یافت نشد - این کپچای جدیدی است")
            return False
            
    except Exception as e:
        print(f"خطا: {e}")
        return False

def main():
    print("="*60)
    print("Captcha Solution Recorder")
    print("یادگیری و ضبط راه‌حل‌های کپچا")
    print("="*60)
    
    # بارگذاری راه‌حل‌های قبلی
    solutions = load_solutions()
    print(f"\n📚 {len(solutions)} راه‌حل در حافظه")
    
    driver = setup_driver()
    
    try:
        mode = input("\nانتخاب کنید:\n1. ضبط راه‌حل‌های جدید\n2. استفاده از راه‌حل‌های موجود\n\nانتخاب (1/2): ")
        
        # رفتن به صفحه لاگین
        print(f"\nباز کردن {LOGIN_URL}...")
        driver.get(LOGIN_URL)
        time.sleep(3)
        
        # ورود ایمیل
        print("ورود ایمیل...")
        username = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "Username"))
        )
        username.send_keys(EMAIL)
        username.send_keys(Keys.ENTER)
        time.sleep(4)
        
        if mode == '1':
            # حالت ضبط
            for i in range(6):
                print(f"\n--- کپچا {i+1}/6 ---")
                
                img_hash, solution = record_manual_solution(driver)
                
                if img_hash and solution:
                    solutions[img_hash] = solution
                    save_solutions(solutions)
                    print(f"✅ راه‌حل ذخیره شد (مجموع: {len(solutions)})")
                
                # refresh برای کپچای جدید
                if i < 5:
                    time.sleep(2)
                    try:
                        driver.refresh()
                        time.sleep(3)
                        # دوباره ایمیل
                        username = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.NAME, "Username"))
                        )
                        username.send_keys(EMAIL)
                        username.send_keys(Keys.ENTER)
                        time.sleep(4)
                    except:
                        print("نیاز به refresh دستی")
                        input("Enter بعد از رفتن به کپچای جدید...")
        
        else:
            # حالت استفاده
            if not solutions:
                print("\n❌ هیچ راه‌حلی ذخیره نشده!")
                print("ابتدا گزینه 1 را انتخاب کنید")
            else:
                solved = auto_solve_captcha(driver, solutions)
                
                if not solved:
                    print("\nحل دستی...")
                    input("Enter بعد از حل...")
        
        print("\n" + "="*60)
        print("💡 نکته مهم:")
        print("="*60)
        print("این نسخه فقط تصاویر را شناسایی می‌کند")
        print("برای حل خودکار کامل نیاز به:")
        print("  1. ضبط حرکات ماوس (mouse tracking)")
        print("  2. Object detection برای قطعات")
        print("  3. Path planning برای drag & drop")
        print("\nبرای پیاده‌سازی کامل زمان بیشتری نیاز است")
        
        input("\nEnter برای خروج...")
        
    except Exception as e:
        print(f"\nخطا: {e}")
        import traceback
        traceback.print_exc()
        input("\nEnter...")
    finally:
        driver.quit()

if __name__ == '__main__':
    main()