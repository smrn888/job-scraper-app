# find_slider_elements.py - پیدا کردن المنت‌های اسلایدر
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

EMAIL = "moienblack8888@gmail.com"
LOGIN_URL = "https://www.jobvision.ir/login"

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    return webdriver.Chrome(options=options)

def find_all_slider_candidates(driver):
    """جستجوی تمام عناصر احتمالی اسلایدر"""
    
    print("\n" + "="*60)
    print("🔍 جستجوی عناصر اسلایدر...")
    print("="*60)
    
    search_patterns = [
        # Class-based
        ("CLASS_NAME", "slide-button"),
        ("CLASS_NAME", "slider"),
        ("CLASS_NAME", "slide-block"),
        ("CLASS_NAME", "slider-button"),
        ("CLASS_NAME", "drag-button"),
        ("CLASS_NAME", "slider-move-btn"),
        
        # CSS Selectors
        ("CSS_SELECTOR", ".slide-button"),
        ("CSS_SELECTOR", "[class*='slide']"),
        ("CSS_SELECTOR", "[class*='slider']"),
        ("CSS_SELECTOR", "[class*='drag']"),
        
        # XPath
        ("XPATH", "//div[contains(@class,'slide')]"),
        ("XPATH", "//div[contains(@class,'slider')]"),
        ("XPATH", "//div[contains(@class,'drag')]"),
        ("XPATH", "//span[contains(@class,'slide')]"),
        ("XPATH", "//*[contains(@class,'button') and contains(@class,'slide')]"),
    ]
    
    found_elements = []
    
    for method, selector in search_patterns:
        try:
            if method == "CLASS_NAME":
                elements = driver.find_elements(By.CLASS_NAME, selector)
            elif method == "CSS_SELECTOR":
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            elif method == "XPATH":
                elements = driver.find_elements(By.XPATH, selector)
            
            if elements:
                print(f"\n✅ {method}: {selector}")
                print(f"   تعداد: {len(elements)}")
                
                for i, elem in enumerate(elements[:3]):  # فقط 3 تای اول
                    try:
                        tag = elem.tag_name
                        classes = elem.get_attribute('class')
                        visible = elem.is_displayed()
                        size = elem.size
                        location = elem.location
                        
                        print(f"\n   Element {i+1}:")
                        print(f"      Tag: {tag}")
                        print(f"      Classes: {classes}")
                        print(f"      Visible: {visible}")
                        print(f"      Size: {size}")
                        print(f"      Location: {location}")
                        
                        if visible and size['width'] > 0 and size['height'] > 0:
                            found_elements.append({
                                'method': method,
                                'selector': selector,
                                'element': elem,
                                'tag': tag,
                                'classes': classes
                            })
                    except Exception as e:
                        print(f"      ⚠️ خطا در بررسی element: {e}")
        
        except Exception as e:
            pass
    
    return found_elements

def inspect_captcha_area(driver):
    """بررسی کامل ناحیه کپچا"""
    
    print("\n" + "="*60)
    print("🔍 بررسی ساختار کپچا...")
    print("="*60)
    
    try:
        # پیدا کردن canvas
        canvas = driver.find_element(By.TAG_NAME, "canvas")
        print(f"\n✅ Canvas پیدا شد")
        print(f"   Size: {canvas.size}")
        print(f"   Location: {canvas.location}")
        
        # پیدا کردن parent
        parent = canvas.find_element(By.XPATH, "..")
        print(f"\n📦 Parent element:")
        print(f"   Tag: {parent.tag_name}")
        print(f"   Classes: {parent.get_attribute('class')}")
        
        # تمام child elements
        children = parent.find_elements(By.XPATH, ".//*")
        print(f"\n👶 Children elements: {len(children)}")
        
        for i, child in enumerate(children[:10]):
            try:
                tag = child.tag_name
                classes = child.get_attribute('class')
                visible = child.is_displayed()
                size = child.size
                
                if size['width'] > 10 and size['height'] > 10:
                    print(f"\n   Child {i+1}:")
                    print(f"      Tag: {tag}")
                    print(f"      Classes: {classes}")
                    print(f"      Visible: {visible}")
                    print(f"      Size: {size}")
            except:
                pass
        
        # ذخیره HTML کپچا
        parent_html = parent.get_attribute('outerHTML')
        with open('captcha_structure.html', 'w', encoding='utf-8') as f:
            f.write(parent_html)
        print(f"\n💾 ساختار کپچا ذخیره شد: captcha_structure.html")
        
    except Exception as e:
        print(f"❌ خطا: {e}")

def main():
    print("\n🎯 شروع جستجو...")
    
    driver = setup_driver()
    
    try:
        # باز کردن صفحه
        print(f"\n📂 باز کردن: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        time.sleep(3)
        
        # ورود ایمیل
        print("\n📧 وارد کردن ایمیل...")
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "Username"))
        )
        username_field.send_keys(EMAIL)
        username_field.send_keys(Keys.ENTER)
        time.sleep(4)
        
        # بررسی iframe
        print("\n🖼️ بررسی iframe ها...")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"تعداد iframe: {len(iframes)}")
        
        # جستجوی اسلایدر
        found = find_all_slider_candidates(driver)
        
        # بررسی ساختار کپچا
        inspect_captcha_area(driver)
        
        # خلاصه نتایج
        print("\n" + "="*60)
        print("📊 خلاصه نتایج:")
        print("="*60)
        print(f"تعداد عناصر پیدا شده: {len(found)}")
        
        if found:
            print("\n✅ عناصر قابل استفاده:")
            for item in found:
                print(f"   • {item['method']}: {item['selector']}")
                print(f"     Tag: {item['tag']}, Classes: {item['classes'][:50]}...")
        else:
            print("\n❌ هیچ عنصر اسلایدری پیدا نشد!")
        
        print("\n💾 فایل‌های ذخیره شده:")
        print("   - captcha_structure.html")
        
        # اسکرین‌شات
        driver.save_screenshot('slider_search.png')
        print("   - slider_search.png")
        
        input("\n⏸️ Enter برای بستن...")
        
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        input("\n⏸️ Enter برای خروج...")
    finally:
        driver.quit()

if __name__ == '__main__':
    main()