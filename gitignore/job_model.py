import pandas as pd
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans

# -----------------------------
# 1. استاپ‌وردهای گسترده (فقط کلمات توضیحی/عمومی)
# -----------------------------
stopwords_fa = set([
    # کلمات ربطی و حروف اضافه
    "های","ها","در","به","با","از","برای","یا","که","می","را","و","یک",
    "این","آن","تا","بین","هم","روی","کردن","شود","است","بود","نیز","اما",
    "چون","اگر","هر","همه","خود","نیز","باید","دارای","داشتن","شده","بودن",
    
    # کلمات عمومی که مهارت نیستند
    "هوش","مصنوعی","یادگیری","ماشین","داده","سازی","مدل","کار","تجربه",
    "آشنایی","مهارت","توسعه","تیم","تسلط","پروژه","مانند","همکاری","ای",
    "توانایی","حوزه","پردازش","تحلیل","طراحی","ابزارهای","بر","استفاده",
    "مدیریت","ارزیابی","پیش","بهینه","سیستم","الگوریتم","برنامه","حل",
    "مسئله","ریزی","نرم","افزار","علمی","پیاده","فنی","قوی","عمیق","ساختن",
    "داشتن","نوشتن","ساخت","اجرا","فرآیند","روش","تکنیک","شیوه","نحوه",
    "سال","ماه","روز","سابقه","حداقل","حداکثر","بالا","پایین","خوب","عالی",
    "قدرتمند","مناسب","لازم","ضروری","مورد","نیاز","شامل","دارد","باشد",
    "شود","گردد","نماید","آموزش","یاد","گیری","دیده","دانش","معرفت",
    "اطلاعات","محیط","شرایط","موقعیت","فرصت","زمینه","بخش","قسمت",
    "عنوان","نقش","وظیفه","مسئولیت","انجام","ارائه","تولید","ایجاد"
])

stopwords_en = set([
    # Common words
    "the","and","for","with","from","this","that","using","use","you","your",
    "our","are","will","can","should","etc","may","or","of","to","in","on",
    "at","by","as","be","is","was","were","been","being","have","has","had",
    "do","does","did","but","if","then","than","such","so","no","not","only",
    
    # Generic skills/job-related words
    "experience","years","year","skills","knowledge","strong","good","excellent",
    "ability","abilities","work","working","worked","team","project","projects",
    "development","develop","developing","developer","model","models","modeling",
    "data","learning","machine","artificial","intelligence","deep","systems",
    "system","design","designing","production","tools","tool","framework",
    "frameworks","library","libraries","understanding","familiar","familiarity",
    "proficiency","proficient","expert","expertise","background","plus","bonus",
    "required","preferred","nice","must","responsibilities","role","position",
    "job","collaborate","collaboration","build","building","create","creating"
])

# -----------------------------
# 2. دیکشنری نرمال‌سازی مهارت‌ها
# -----------------------------
replace_dict = {
    "پایتون": "python",
    "جاوا": "java",
    "جاوااسکریپت": "javascript",
    "جاوا اسکریپت": "javascript",
    "متلب": "matlab",
    "تنسورفلو": "tensorflow",
    "پی تورچ": "pytorch",
    "پی‌تورچ": "pytorch",
    "اس کی‌لرن": "scikit-learn",
    "اسکیکت لرن": "scikit-learn",
    "اسکی لرن": "scikit-learn",
    "پانداز": "pandas",
    "پانداس": "pandas",
    "نامپای": "numpy",
    "نامپی": "numpy",
    "کراس": "keras",
    "کرس": "keras",
    "اسپارک": "spark",
    "داکر": "docker",
    "کوبرنتیز": "kubernetes",
    "گیت": "git",
}

def normalize_skills(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    
    # جایگزینی نام‌های فارسی
    for fa, en in replace_dict.items():
        text = text.replace(fa, en)
    
    # حذف کاراکترهای خاص ولی نگه‌داشتن + . - # که در نام تکنولوژی‌ها هست
    text = re.sub(r"[^آ-یa-zA-Z0-9\s\+\.\-#]", " ", text)
    
    # حذف فاصله‌های اضافی
    text = " ".join(text.split())
    
    return text

# -----------------------------
# 3. بارگذاری داده‌ها
# -----------------------------
df = pd.read_csv("jobs.csv")
df["requirements_normalized"] = df["requirements"].astype(str).apply(normalize_skills)

# -----------------------------
# 4. استخراج کلمات پرتکرار (با n-grams)
# -----------------------------
vectorizer = CountVectorizer(
    max_df=0.75,          # حذف کلمات که در بیش از 75% اسناد هستند
    min_df=3,             # باید حداقل در 3 آگهی تکرار شده باشد
    ngram_range=(1, 3),   # تک‌کلمه، دو‌کلمه، سه‌کلمه
    stop_words=list(stopwords_en) + list(stopwords_fa),
    token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z0-9\+\.\-#]*\b'  # الگوی انعطاف‌پذیر
)

X = vectorizer.fit_transform(df["requirements_normalized"])
words = vectorizer.get_feature_names_out()
word_counts = X.toarray().sum(axis=0)

# مرتب‌سازی براساس تکرار
freqs = sorted(zip(words, word_counts), key=lambda x: x[1], reverse=True)

# فیلتر نهایی: حذف کلمات خیلی کوتاه یا اعداد خالص
filtered_freqs = []
for word, count in freqs:
    # حذف کلمات کوتاه‌تر از 3 کاراکتر (مگر c++ یا r)
    if len(word) < 3 and word not in ['r', 'c++', 'c#', 'go']:
        continue
    # حذف اعداد خالص
    if word.isdigit():
        continue
    # اضافه کردن به لیست نهایی
    filtered_freqs.append((word, count))

print("🔝 50 مهارت پرتکرار:")
print("=" * 60)
for word, count in filtered_freqs[:50]:
    percent = 100 * count / len(df)
    print(f"{word:30s}: {count:3d} ({percent:5.1f}%)")

# -----------------------------
# 5. خوشه‌بندی KMeans
# -----------------------------
k = 5  # تعداد خوشه‌ها
km = KMeans(n_clusters=k, random_state=42, n_init=10)
km.fit(X)

df["cluster"] = km.labels_

# -----------------------------
# 6. نمایش خوشه‌ها + ذخیره CSV
# -----------------------------
print("\n\n🗂️ نتایج خوشه‌بندی:")
print("=" * 60)

rows = []
for i in range(k):
    mask = (df["cluster"] == i).to_numpy()
    if mask.sum() == 0:
        continue
    
    # استخراج مهارت‌های برتر این خوشه
    top_indices = X[mask].sum(axis=0).A1.argsort()[-20:][::-1]
    top_words = [words[j] for j in top_indices]
    
    # فیلتر نهایی
    filtered_words = [w for w in top_words if len(w) >= 3 or w in ['r', 'c++', 'c#']]
    
    print(f"\n--- خوشه {i} ({mask.sum()} آگهی) ---")
    print("مهارت‌ها:", ", ".join(filtered_words[:15]))
    
    for w in filtered_words[:15]:
        rows.append({"cluster": i, "skill": w, "frequency": X[mask, vectorizer.vocabulary_[w]].sum()})

# ذخیره خروجی با فرکانس
output_df = pd.DataFrame(rows)
output_df = output_df.sort_values(['cluster', 'frequency'], ascending=[True, False])
output_df.to_csv("skills_clusters.csv", index=False, encoding="utf-8-sig")

# ذخیره خلاصه آماری
summary_rows = []
for word, count in filtered_freqs[:100]:
    percent = 100 * count / len(df)
    summary_rows.append({"skill": word, "count": count, "percentage": round(percent, 1)})

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv("skills_summary.csv", index=False, encoding="utf-8-sig")

print("\n\n💾 نتایج ذخیره شد:")
print(f"   📄 skills_clusters.csv - {len(output_df)} مهارت در {k} خوشه")
print(f"   📄 skills_summary.csv - 100 مهارت برتر")
print(f"\n   تعداد کل آگهی: {len(df)}")
print(f"   تعداد کل ویژگی‌های استخراج‌شده: {len(words)}")