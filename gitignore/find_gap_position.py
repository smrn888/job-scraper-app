# jobvision_login_debug.py
import sys
import io
import time
import random
import traceback

print("✅ شروع اسکریپت...")
print(f"✅ Python version: {sys.version}")

try:
    from PIL import Image
    print("✅ PIL imported")
except Exception as e:
    print(f"❌ خطا در import PIL: {e}")
    sys.exit(1)

try:
    import cv2
    print("✅ OpenCV imported")
except Exception as e:
    print(f"❌ خطا در import cv2: {e}")
    sys.exit(1)

try:
    import numpy as np
    print("✅ NumPy imported")
except Exception as e:
    print(f"❌ خطا در import numpy: {e}")
    sys.exit(1)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    print("✅ Selenium imported")
except Exception as e:
    print(f"❌ خطا در import Selenium: {e}")
    sys.exit(1)

# ----------------- تنظیمات لاگین -----------------
EMAIL = "moienblack8888@gmail.com"
PASSWORD = "ijyJc.3gemnuwQh"
LOGIN_URL = "https://www.jobvision.ir/login"

# ----------------- کمک‌کننده‌ها -----------------
def random_sleep(min_sec=1.5, max_sec=3.5):
    """تاخیر تصادفی برای شبیه‌سازی رفتار انسانی."""
    time.sleep(random.uniform(min_sec, max_sec))

def human_typing(element, text, min_delay=0.08, max_delay=0.18):
    """تایپ کاراکتر به کاراکتر در یک عنصر."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))
    time.sleep(random.uniform(0.4, 0.9))

# ----------------- راه‌اندازی درایور -----------------
def setup_driver():
    print("\n🚀 راه‌اندازی Chrome Driver...")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')

    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome Driver راه‌اندازی شد")
        return driver
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی Chrome: {e}")
        print("\n💡 راهنمایی:")
        print("1. آیا Chrome نصب است؟")
        print("2. آیا ChromeDriver نصب است؟")
        print("3. دستور زیر را اجرا کنید:")
        print("   pip install selenium webdriver-manager")
        sys.exit(1)

# ----------------- باز کردن صفحه و debug -----------------
def debug_page(driver):
    print("\n" + "="*60)
    print("🔍 اطلاعات صفحه فعلی:")
    print("="*60)
    print(f"📍 URL: {driver.current_url}")
    print(f"📄 Title: {driver.title}")
    
    # ذخیره HTML
    try:
        with open('current_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("💾 HTML ذخیره شد: current_page.html")
    except Exception as e:
        print(f"⚠️ خطا در ذخیره HTML: {e}")
    
    # لیست iframe ها
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"🖼️  تعداد iframe: {len(iframes)}")
        for i, iframe in enumerate(iframes):
            try:
                src = iframe.get_attribute('src')
                print(f"   iframe {i}: {src[:80] if src else 'بدون src'}")
            except:
                pass
    except Exception as e:
        print(f"⚠️ خطا در بررسی iframe: {e}")
    
    # اسکرین‌شات
    try:
        driver.save_screenshot('screenshot.png')
        print("📸 اسکرین‌شات ذخیره شد: screenshot.png")
    except Exception as e:
        print(f"⚠️ خطا در اسکرین‌شات: {e}")
    
    print("="*60 + "\n")

# ----------------- تابع اصلی -----------------
def main():
    print("\n" + "🎯"*30)
    print("شروع فرآیند لاگین به JobVision - نسخه Debug")
    print("🎯"*30 + "\n")
    
    driver = setup_driver()
    
    try:
        # مرحله 1: باز کردن صفحه لاگین
        print(f"\n📂 باز کردن صفحه: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        random_sleep(3, 5)
        debug_page(driver)
        
        # مرحله 2: وارد کردن ایمیل
        print("\n📧 گام 1: وارد کردن ایمیل...")
        try:
            username_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "Username"))
            )
            print("✅ فیلد Username پیدا شد")
            human_typing(username_field, EMAIL)
            username_field.send_keys(Keys.ENTER)
            print("✅ ایمیل ارسال شد")
            random_sleep(3, 5)
            debug_page(driver)
        except Exception as e:
            print(f"❌ خطا در وارد کردن ایمیل: {e}")
            traceback.print_exc()
            input("\n⏸️ Enter برای بستن...")
            return
        
        # مرحله 3: بررسی کپچا
        print("\n🧩 گام 2: بررسی کپچا...")
        
        # جستجوی کپچا در صفحه اصلی
        captcha_selectors = [
            (By.CLASS_NAME, "slide-verify-box"),
            (By.CSS_SELECTOR, ".slide-verify-box"),
            (By.XPATH, "//div[contains(@class, 'slide-verify')]"),
            (By.TAG_NAME, "canvas"),
        ]
        
        captcha_found = False
        for sel_type, sel_value in captcha_selectors:
            try:
                elements = driver.find_elements(sel_type, sel_value)
                if elements:
                    print(f"✅ کپچا پیدا شد با {sel_type}: {sel_value}")
                    print(f"   تعداد عناصر: {len(elements)}")
                    captcha_found = True
                    break
            except:
                pass
        
        if not captcha_found:
            print("⚠️ کپچا در صفحه اصلی پیدا نشد. بررسی iframe ها...")
            
            # بررسی iframe ها
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for i, iframe in enumerate(iframes):
                try:
                    print(f"\n🔍 بررسی iframe {i}...")
                    driver.switch_to.frame(iframe)
                    random_sleep(1, 2)
                    
                    for sel_type, sel_value in captcha_selectors:
                        try:
                            elements = driver.find_elements(sel_type, sel_value)
                            if elements:
                                print(f"✅ کپچا در iframe {i} پیدا شد!")
                                captcha_found = True
                                debug_page(driver)
                                break
                        except:
                            pass
                    
                    if captcha_found:
                        break
                    
                    driver.switch_to.default_content()
                except Exception as e:
                    print(f"⚠️ خطا در بررسی iframe {i}: {e}")
                    driver.switch_to.default_content()
        
        if not captcha_found:
            print("\n❌ کپچا پیدا نشد!")
            print("\n💡 احتمالات:")
            print("1. کپچا بعد از مدتی ظاهر می‌شود")
            print("2. ساختار سایت تغییر کرده")
            print("3. کپچا فقط در شرایط خاصی نمایش داده می‌شود")
            print("\n📝 لطفاً فایل‌های زیر را بررسی کنید:")
            print("   - current_page.html")
            print("   - screenshot.png")
        else:
            print("\n✅ کپچا پیدا شد!")
            print("⚠️ حل خودکار کپچا در این نسخه Debug فعال نیست")
            print("لطفاً خودتان کپچا را حل کنید...")
        
        input("\n⏸️ Enter برای بستن مرورگر...")
        
    except KeyboardInterrupt:
        print("\n⚠️ عملیات توسط کاربر لغو شد")
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
        traceback.print_exc()
        input("\n⏸️ Enter برای خروج...")
    finally:
        try:
            driver.quit()
            print("\n👋 مرورگر بسته شد")
        except:
            pass

# ----------------- نقطه ورود -----------------
if __name__ == '__main__':
    print("="*60)
    print("JobVision Auto-Login - Debug Version")
    print("="*60)
    main()
    print("\n✅ اسکریپت به پایان رسید")