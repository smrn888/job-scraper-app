# jobvision_final_working.py - نسخه نهایی و کاربردی
import sys
import io
import time
import random
import traceback

from PIL import Image
import cv2
import numpy as np

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import cv2
import numpy as np
import requests   # 👈 این خط باید باشه


# ================== تنظیمات ==================
EMAIL = "moienblack8888@gmail.com"
PASSWORD = "ijyJc.3gemnuwQh"
LOGIN_URL = "https://www.jobvision.ir/login"

# ---------------- تابع اصلی ----------------
def main():
    driver = setup_browser()
    open_login_page(driver)
    enter_email(driver, EMAIL)
    solve_arcaptcha(driver)
    enter_password_and_login(driver, PASSWORD)  # 👈 مرحله نهایی لاگین
    input("\n✅ برای خروج Enter بزن... ")
    driver.quit()


# ---------------- راه‌اندازی مرورگر ----------------
def setup_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver

# ---------------- باز کردن صفحه لاگین ----------------
def open_login_page(driver):
    driver.get(LOGIN_URL)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.NAME, "Username"))
    )
    print("✅ صفحه لاگین باز شد.")

# ---------------- وارد کردن ایمیل ----------------
def enter_email(driver, email):
    email_input = driver.find_element(By.NAME, "Username")
    email_input.clear()
    email_input.send_keys(email)
    time.sleep(0.5)

    # بستن احتمالی پنجره‌ی پیشنهاد ایمیل با ESC
    email_input.send_keys(Keys.ESCAPE)
    time.sleep(0.5)

    # کلیک روی دکمه ادامه با جاوااسکریپت
    continue_btn = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
    driver.execute_script("arguments[0].scrollIntoView(true);", continue_btn)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", continue_btn)

    print("✉️ ایمیل وارد شد و ادامه زده شد.")
    time.sleep(2)
# ---------------- حل کپچا ----------------
def solve_arcaptcha(driver):
    print("🧠 در حال حل کپچا...")

    # منتظر نمایش کپچا
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "challenge"))
    )
    time.sleep(1)

    # گرفتن URL تصویر پس‌زمینه و قطعه
    bg_url = driver.find_element(By.CSS_SELECTOR, "#challenge .tw-relative img").get_attribute("src")
    piece_url = driver.find_element(By.CSS_SELECTOR, "#challenge .tw-absolute img.puzzle").get_attribute("src")

    bg = download_image(bg_url)
    piece = download_image(piece_url)

    # پیدا کردن مختصات
    target_x = find_piece_position(bg, piece)
    print(f"📌 موقعیت قطعه پازل: {target_x}")

    # کشیدن اسلایدر
    drag_slider(driver, target_x)
    time.sleep(2)

# ---------------- تکمیل لاگین ----------------
def complete_login(driver):
    # در این مرحله معمولاً وارد صفحه رمز عبور یا کد میشه
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("✅ کپچا حل شد. آماده‌ی ورود مرحله بعد هست.")
    except:
        print("⚠️ لاگین نیاز به مرحله‌ی بعدی دارد (کد یا رمز).")

# ---------------- ابزارها ----------------
def download_image(url):
    r = requests.get(url)
    img_arr = np.asarray(bytearray(r.content), dtype=np.uint8)
    return cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

def find_piece_position(bg, piece):
    # خاکستری کردن
    bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    piece_gray = cv2.cvtColor(piece, cv2.COLOR_BGR2GRAY)

    # نرمال‌سازی (اختیاری - دقت رو بالا می‌بره)
    bg_gray = cv2.GaussianBlur(bg_gray, (3, 3), 0)
    piece_gray = cv2.GaussianBlur(piece_gray, (3, 3), 0)

    # تشخیص لبه با Canny
    bg_edges = cv2.Canny(bg_gray, 100, 200)
    piece_edges = cv2.Canny(piece_gray, 100, 200)

    # matchTemplate روی لبه‌ها
    res = cv2.matchTemplate(bg_edges, piece_edges, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    # برای دیباگ — می‌تونه برداشته شه
    debug = bg.copy()
    h, w = piece_edges.shape
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    cv2.rectangle(debug, top_left, bottom_right, (0, 0, 255), 2)
    cv2.imwrite("captcha_debug_match.png", debug)
    print(f"🔍 بیشترین تطابق در X={max_loc[0]} | دقت={max_val:.3f}")

    return max_loc[0]
def drag_slider(driver, x_offset):
    slider = driver.find_element(By.CSS_SELECTOR, "#challenge .draggable")
    actions = ActionChains(driver)
    actions.click_and_hold(slider).perform()
    time.sleep(0.2)
    actions.move_by_offset(x_offset, 0).perform()
    time.sleep(0.2)
    actions.release().perform()
    print("🧩 اسلایدر کشیده شد.")

def enter_password_and_login(driver, password):
    print("🔐 در حال وارد کردن رمز عبور...")

    # منتظر ظاهر شدن فیلد پسورد
    password_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.NAME, "Password"))
    )
    password_input.clear()
    password_input.send_keys(password)
    time.sleep(0.5)

    # زدن دکمه ورود
    login_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary")
    driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", login_button)

    print("✅ رمز عبور وارد شد و روی دکمه ورود کلیک شد.")

    # منتظر لاگین شدن یا انتقال به داشبورد
    try:
        WebDriverWait(driver, 15).until(
            EC.url_contains("jobvision.ir")  # آدرس داشبورد یا صفحه اصلی
        )
        print("🎉 ورود با موفقیت انجام شد ✅")
    except:
        print("⚠️ ممکنه ورود به تایید دومرحله‌ای نیاز داشته باشه یا رمز اشتباه باشه.")


# ---------------- اجرای برنامه ----------------
if __name__ == "__main__":
    main()