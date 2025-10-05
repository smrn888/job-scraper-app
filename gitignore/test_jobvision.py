"""
JobVision Login Script with ARCaptcha Support
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys


def setup_browser():
    """Configure Chrome"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(executable_path='chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def human_delay(min_sec=1, max_sec=3):
    """Random delay"""
    time.sleep(random.uniform(min_sec, max_sec))

def wait_for_captcha_token(driver, timeout=30):
    """Wait for ARCaptcha token to be generated"""
    print("\n⏳ Waiting for ARCaptcha token...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        token = driver.execute_script("""
            let tokenInput = document.querySelector('input[name="arcaptcha-token"]');
            return tokenInput ? tokenInput.value : null;
        """)
        
        if token and len(token) > 10:
            print(f"   ✅ ARCaptcha token received: {token[:20]}...")
            return token
        
        time.sleep(0.5)
    
    print("   ⚠️ ARCaptcha token not generated automatically")
    return None

def trigger_arcaptcha(driver):
    """Trigger ARCaptcha validation"""
    print("\n🔐 Triggering ARCaptcha...")
    
    # روش 1: تریگر کردن با JavaScript
    result = driver.execute_script("""
        try {
            // پیدا کردن widget ARCaptcha
            let widget = document.querySelector('[data-site-key]');
            if (widget) {
                let widgetId = widget.getAttribute('data-widget-id');
                console.log('Widget ID:', widgetId);
                
                // اگر API ARCaptcha لود شده، execute کن
                if (typeof arcaptcha !== 'undefined' && arcaptcha.execute) {
                    arcaptcha.execute(widgetId);
                    return {success: true, method: 'api_execute'};
                }
            }
            
            // روش جایگزین: trigger کردن checkbox
            let checkbox = document.querySelector('#input-checkbox input');
            if (checkbox) {
                checkbox.click();
                return {success: true, method: 'checkbox_click'};
            }
            
            return {success: false, method: 'none'};
        } catch(e) {
            return {success: false, error: e.message};
        }
    """)
    
    print(f"   Result: {result}")
    return result.get('success', False)

def test_jobvision_login():
    """Test JobVision login process"""
    
    EMAIL = "moienblack8888@gmail.com"
    PASSWORD = "ijyJc.3gemnuwQh"
    driver = setup_browser()
    
    try:
        print("\n🔐 Testing JobVision Login with ARCaptcha Support...")
        print("="*60)
        
        # مرحله 1: رفتن به صفحه لاگین
        print("\n📍 Step 1: Opening login page...")
        driver.get("https://jobvision.ir/login")
        human_delay(5, 7)
        
        print(f"   Current URL: {driver.current_url}")
        
        # مرحله 2: وارد کردن ایمیل
        print("\n📍 Step 2: Entering email...")
        
        try:
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "Username"))
            )
            
            email_field.click()
            human_delay(0.3, 0.5)
            email_field.clear()
            
            for char in EMAIL:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.08, 0.15))
            
            driver.execute_script("""
                let input = arguments[0];
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.dispatchEvent(new Event('blur', { bubbles: true }));
            """, email_field)
            
            print("   ✅ Email entered successfully")
            
        except Exception as e:
            print(f"   ❌ Failed to enter email: {e}")
            return
        
        human_delay(1, 2)
        
        # مرحله 3: کلیک روی دکمه ادامه
        print("\n📍 Step 3: Clicking continue button...")
        
        email_field.send_keys(Keys.ENTER)
        print("   ✅ Pressed Enter")
        
        human_delay(3, 4)
        
        # مرحله 4: وارد کردن رمز عبور
        print("\n📍 Step 4: Entering password...")
        
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "Password"))
            )
            
            password_field.click()
            human_delay(0.3, 0.5)
            password_field.clear()
            
            for char in PASSWORD:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.08, 0.15))
            
            driver.execute_script("""
                let input = arguments[0];
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """, password_field)
            
            print("   ✅ Password entered successfully")
            
        except Exception as e:
            print(f"   ❌ Failed to enter password: {e}")
            return
        
        human_delay(1, 2)
        
        # مرحله 5: Submit سریع فرم (قبل از چک کردن کپچا)
        print("\n📍 Step 5: Quick form submission (before captcha check)...")
        
        # روش 1: فشردن Enter روی password field
        try:
            print("   Trying Enter key on password field...")
            password_field.send_keys(Keys.ENTER)
            print("   ✅ Pressed Enter")
            
            # صبر کوتاه برای ببینیم چی میشه
            human_delay(3, 4)
            
            current_url = driver.current_url
            if "account.jobvision.ir" not in current_url and "jobvision.ir" in current_url:
                print("\n" + "="*60)
                print("   ✅✅✅ LOGIN SUCCESSFUL! ✅✅✅")
                print("="*60)
                return driver  # لاگین موفق، تابع به main برمی‌گرده
            else:
                print("\n⚠️ Login failed")
                return None
            
            # اگر redirect نشد، ادامه بده
            print("   ⚠️ Enter didn't work, checking captcha status...")
            
        except Exception as e:
            print(f"   ⚠️ Enter key failed: {e}")
        
        # مرحله 6: بررسی و حل کپچا
        print("\n📍 Step 6: Handling ARCaptcha if needed...")
        
        # روش 1: صبر برای تولید خودکار توکن
        token = wait_for_captcha_token(driver, timeout=10)
        
        if not token:
            # روش 2: تریگر دستی
            trigger_arcaptcha(driver)
            token = wait_for_captcha_token(driver, timeout=15)
        
        if not token:
            print("\n⚠️ ARCaptcha requires manual interaction!")
            print("   Please solve the CAPTCHA in the browser window...")
            print("   The script will wait for 30 seconds...")
            
            # صبر برای حل دستی
            token = wait_for_captcha_token(driver, timeout=30)
            
            if not token:
                print("\n❌ CAPTCHA not solved. You need to:")
                print("   1. Solve the CAPTCHA manually")
                print("   2. Click the login button manually")
                input("\n   Press ENTER after completing login manually...")
                
                # بررسی نهایی
                current_url = driver.current_url
                if "account.jobvision.ir" not in current_url:
                    print("   ✅ LOGIN SUCCESSFUL! 🎉")
                else:
                    print("   ⚠️ Still on login page")
                return
        
        # مرحله 7: Submit با کپچا
        print("\n📍 Step 7: Submitting form with captcha token...")
        
        # ذخیره password_field برای استفاده بعدی
        current_password_field = password_field
        try:
            login_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary"))
            )
            
            # اسکرول تا دکمه
            driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            human_delay(0.5, 1)
            
            # کلیک با JavaScript برای trigger کردن event handlers
            driver.execute_script("""
                let btn = arguments[0];
                // تریگر تمام eventها
                btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
            """, login_button)
            
            print("   ✅ Login button events triggered")
            human_delay(2, 3)
            
            # چک کردن آیا صفحه تغییر کرد
            if driver.current_url != current_url:
                print("   ✅ Page changed, login seems successful")
            else:
                print("   ⚠️ Page didn't change, trying alternative methods...")
                raise Exception("Page didn't change")
            
        except Exception as e:
            print(f"   ⚠️ Method 1 failed, trying fallbacks...")
            
            # روش 2: پیدا کردن و submit کردن فرم با POST
            form_submitted = driver.execute_script("""
                try {
                    // جمع‌آوری تمام داده‌های فرم
                    let formData = {};
                    let inputs = document.querySelectorAll('input');
                    inputs.forEach(inp => {
                        if (inp.name) {
                            formData[inp.name] = inp.value;
                        }
                    });
                    
                    // پیدا کردن فرم
                    let form = document.querySelector('form');
                    if (form) {
                        // ایجاد hidden input برای توکن اگر وجود نداره
                        let tokenInput = form.querySelector('input[name="arcaptcha-token"]');
                        if (!tokenInput) {
                            tokenInput = document.createElement('input');
                            tokenInput.type = 'hidden';
                            tokenInput.name = 'arcaptcha-token';
                            tokenInput.value = formData['arcaptcha-token'] || '';
                            form.appendChild(tokenInput);
                        }
                        
                        // Submit
                        form.submit();
                        return {success: true, method: 'form_submit'};
                    }
                    
                    // روش جایگزین: ارسال با fetch
                    let loginBtn = document.querySelector('a.btn.btn-primary');
                    if (loginBtn && loginBtn.__vue__) {
                        // اگر Vue instance داره
                        loginBtn.click();
                        return {success: true, method: 'vue_instance_click'};
                    }
                    
                    return {success: false, method: 'none', formData: formData};
                } catch(e) {
                    return {success: false, error: e.message};
                }
            """)
            
            print(f"   Result: {form_submitted}")
            
            if not form_submitted.get('success'):
                # روش 3: فشردن Enter روی password field
                print("   ⚠️ Trying Enter key on password field...")
                try:
                    current_password_field.send_keys(Keys.ENTER)
                    print("   ✅ Pressed Enter")
                except:
                    print("   ❌ Enter key failed too")
        
        # مرحله 7: بررسی موفقیت لاگین
        print("\n📍 Step 7: Checking login status...")
        human_delay(5, 7)
        
        current_url = driver.current_url
        print(f"   Current URL: {current_url}")
        
        # بررسی دقیق‌تر خطاها
        error_info = driver.execute_script("""
            let result = {
                errors: [],
                captchaToken: '',
                captchaVisible: false,
                formAction: '',
                allInputs: {}
            };
            
            // خطاها
            let errors = document.querySelectorAll('.validation.text-danger, .error, .text-danger');
            errors.forEach(e => {
                let text = e.textContent.trim();
                if (text.length > 0) result.errors.push(text);
            });
            
            // وضعیت کپچا
            let tokenInput = document.querySelector('input[name="arcaptcha-token"]');
            if (tokenInput) {
                result.captchaToken = tokenInput.value;
            }
            
            let captchaWidget = document.querySelector('.arcaptcha');
            result.captchaVisible = captchaWidget && captchaWidget.offsetParent !== null;
            
            // اطلاعات فرم
            let form = document.querySelector('form');
            if (form) {
                result.formAction = form.action;
            }
            
            // تمام inputها
            let inputs = document.querySelectorAll('input');
            inputs.forEach(inp => {
                if (inp.name) {
                    result.allInputs[inp.name] = {
                        value: inp.value ? inp.value.substring(0, 20) + '...' : '',
                        type: inp.type
                    };
                }
            });
            
            return result;
        """)
        
        print("\n📊 Detailed Analysis:")
        print(f"   Captcha Token: {error_info['captchaToken'][:30]}..." if error_info['captchaToken'] else "   No Captcha Token")
        print(f"   Captcha Visible: {error_info['captchaVisible']}")
        print(f"   Form Action: {error_info['formAction']}")
        
        if error_info['errors']:
            print(f"\n   ❌ Errors found:")
            for err in error_info['errors']:
                print(f"      - {err}")
        
        print("\n   Form Inputs:")
        for name, info in error_info['allInputs'].items():
            print(f"      {name}: {info['value']} (type: {info['type']})")
        
        if "account.jobvision.ir" not in current_url and "jobvision.ir" in current_url:
            print("\n" + "="*60)
            print("   ✅✅✅ LOGIN SUCCESSFUL! ✅✅✅")
            print("="*60)
            return True   # فقط برگردون که لاگین موفق شد

        else:
            if not error_info['errors']:
                print("\n   ⚠️ No errors shown but login failed")
                print("   Possible causes:")
                print("      1. Invalid credentials")
                print("      2. Captcha validation failed on server")
                print("      3. Additional verification required")
                print("\n   💡 Check the browser window for any popups or messages")
        
        print("\n" + "="*60)
        print("Browser will stay open for inspection.")
        print("Press ENTER to close browser...")
        input()
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press ENTER to close...")
    finally:
        pass

if __name__ == "__main__":
    test_jobvision_login()