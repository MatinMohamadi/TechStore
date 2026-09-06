# پرامپت‌های آماده — فاز ۱۳ و ۱۴: CI/CD و مستندسازی گیت‌هاب (TechStore)

**پیش‌نیاز:** این فایل ادامه‌ی `PRD-فروشگاه-محصولات-کامپیوتری.md` و `پرامپت‌های-آماده-Claude-Code.md` است و فرض می‌کند فازهای ۰ تا ۱۲ قبلاً پیاده‌سازی شده‌اند (پروژه Dockerized است، تست‌ها موجودند، Swagger فعال است).

**نحوه استفاده:** همین فایل را هم کنار دو فایل قبلی در ریشه پروژه بگذارید و پرامپت‌ها را به ترتیب به Claude Code بدهید.

---

## فاز ۱۳ — CI/CD (GitHub Actions)

### ۱۳.۱ پرامپت اصلی: راه‌اندازی CI (تست و کیفیت کد)

```
می‌خواهم برای این پروژه Django یک پایپ‌لاین CI با GitHub Actions بسازی.
قبل از شروع، ساختار فعلی پروژه (requirements، تست‌ها، Dockerfile، docker-compose)
را بررسی کن تا workflow را متناسب با همان بسازی.

فایل .github/workflows/ci.yml را با این مشخصات بساز:

1. Trigger: روی push به شاخه‌های main/develop و روی هر pull_request به main
2. Job با نام lint-and-test شامل:
   - checkout کد
   - نصب Python (نسخه‌ای که پروژه استفاده می‌کند)
   - کش کردن pip dependencies برای سرعت بیشتر
   - نصب requirements.txt (و requirements-dev.txt اگر جدا وجود دارد؛ اگر نه، بساز
     و ابزارهای dev را از production جدا کن: black, isort, flake8/ruff, pytest, pytest-cov)
   - اجرای linter (ترجیح: ruff یا flake8 + black --check + isort --check)
   - بالا آوردن سرویس‌های وابسته (PostgreSQL و Redis) به‌صورت service containers
     در همان workflow، با همان نسخه‌هایی که در docker-compose.yml پروژه استفاده شده
   - اجرای migrate روی دیتابیس تست
   - اجرای کامل تست‌ها با pytest --cov و تولید گزارش coverage
   - آپلود گزارش coverage به‌عنوان artifact (یا اتصال به Codecov اگر مایل بودی، اختیاری)
3. Job دوم با نام docker-build:
   - بعد از موفقیت lint-and-test اجرا شود (needs)
   - Dockerfile پروژه را build کند تا مطمئن شویم image به‌درستی ساخته می‌شود
   - image را push نکند (فقط build، برای اطمینان از سلامت Dockerfile) — push را به فاز CD می‌سپاریم
4. تمام مقادیر حساس (SECRET_KEY تستی، DATABASE_URL و ...) را به‌صورت
   environment variable در خود workflow (نه secrets واقعی، چون فقط برای تست است) تعریف کن

اگر فایل requirements-dev.txt یا pyproject.toml برای ابزارهای lint وجود ندارد،
آن را بساز و ابزارهای پیشنهادی (black, isort, ruff, pytest, pytest-cov, pytest-django)
را در آن اضافه کن.

در پایان خلاصه‌ای از ساختار workflow و اینکه چطور می‌توانم آن را لوکال هم اجرا/شبیه‌سازی کنم بده.
```

**✅ تست و تایید:**
```
یک commit کوچک (مثلاً تغییر جزئی در یک فایل) بزن، push کن،
و از من بخواه در تب Actions گیت‌هاب بررسی کنم که هر دو job (lint-and-test و docker-build)
سبز شده‌اند. اگر خطایی داد، لاگ را بررسی و اصلاح کن.
```

---

### ۱۳.۲ پرامپت: راه‌اندازی CD (استقرار خودکار)

> این پرامپت را بعد از انتخاب پلتفرم هاست بدهید. اگر هنوز مقصد deploy را انتخاب نکرده‌اید،
> اول از Claude Code بخواهید گزینه‌ها را (VPS با SSH، Railway، Render، Liara، ArvanCloud) با مزایا/معایب مختصر برایتان مقایسه کند.

```
حالا فایل .github/workflows/cd.yml را برای استقرار خودکار پروژه بساز.

Trigger: فقط روی push موفق به شاخه main (بعد از موفقیت CI)، یا با یک tag نسخه (مثل v*)
اگر ترجیح می‌دهی release-based deploy داشته باشیم.

مراحل:
1. Build و push کردن Docker image پروژه به GitHub Container Registry (ghcr.io)
   با تگ‌گذاری بر اساس commit SHA و همچنین تگ latest
2. اتصال به سرور مقصد از طریق SSH (با استفاده از appleboy/ssh-action یا مشابه)
   و اجرای دستورات:
   - docker pull ایمیج جدید
   - docker-compose down و docker-compose up -d با ایمیج جدید
     (یا docker-compose pull && docker-compose up -d اگر از docker-compose.prod.yml استفاده می‌کنیم)
   - اجرای migrate روی دیتابیس production داخل کانتینر
   - collectstatic اگر لازم است
3. تمام مقادیر حساس (SSH_HOST, SSH_USER, SSH_PRIVATE_KEY, GHCR_TOKEN و ...)
   را به‌عنوان GitHub Secrets تعریف کن (فقط نام آن‌ها را در workflow بنویس،
   من خودم مقدارشان را در تنظیمات Repository > Settings > Secrets اضافه می‌کنم)
4. یک مرحله health-check بعد از deploy اضافه کن که endpoint /api/health/ را
   چک کند و اگر پاسخ ۲۰۰ نداد، deploy را fail نشان دهد (و در صورت امکان rollback به ایمیج قبلی)

در پایان چک‌لیستی از Secretsهایی که باید در تنظیمات گیت‌هاب اضافه کنم به من بده،
همراه با توضیح هر کدام.
```

**✅ تست و تایید:**
```
یک deploy تستی به محیط staging (یا یک سرور تست) انجام بده و health-check
بعد از deploy را نشان بده. اگر سرور واقعی هنوز آماده نیست، workflow را با یک
دستور echo/placeholder به‌جای SSH واقعی شبیه‌سازی کن تا ساختار درست تست شود.
```

---

## فاز ۱۴ — README و مستندات گیت‌هاب

### ۱۴.۱ پرامپت اصلی: ساخت README.md حرفه‌ای

```
یک فایل README.md کامل و حرفه‌ای برای این پروژه بساز. قبل از نوشتن،
کل پروژه (apps، endpointها، docker-compose، PRD.md) را مرور کن تا محتوا دقیق باشد.

ساختار مورد انتظار README:

1. عنوان پروژه + یک جمله توضیح کوتاه + badgeهای بالای صفحه:
   - وضعیت CI (از GitHub Actions)
   - نسخه Python/Django
   - لایسنس (اگر تعیین نشده، MIT پیشنهاد بده و بپرس تایید می‌کنم یا نه)
2. فهرست مطالب (Table of Contents) با لینک داخلی
3. بخش «درباره پروژه»: توضیح مختصر TechStore و ویژگی‌های اصلی (خلاصه‌شده از PRD)
4. بخش «تکنولوژی‌ها»: لیست stack (Django, DRF, PostgreSQL, Redis, Celery, Docker, ...)
5. بخش «پیش‌نیازها»: نسخه Python، Docker، Docker Compose
6. بخش «راه‌اندازی سریع (Quick Start)» با دستورات واقعی و تست‌شده پروژه:
   - clone
   - کپی .env.example به .env و توضیح متغیرهای کلیدی
   - docker-compose up -d
   - اجرای migrate و createsuperuser
   - آدرس دسترسی به API (/api/) و مستندات Swagger (/api/docs/)
7. بخش «راه‌اندازی بدون Docker (توسعه لوکال)» برای کسانی که ترجیح می‌دهند
   مستقیم روی سیستم اجرا کنند (virtualenv، pip install، manage.py runserver)
8. بخش «ساختار پروژه»: درخت پوشه‌ها با توضیح مختصر هر اپ (از PRD.md استخراج کن)
9. بخش «اجرای تست‌ها»: دستور pytest و نحوه دیدن گزارش coverage
10. بخش «مستندات API»: لینک به /api/docs/ و توضیح کوتاه (Swagger/OpenAPI)
11. بخش «متغیرهای محیطی (Environment Variables)»: جدول کامل از .env.example
    با توضیح هرکدام (بدون افشای مقدار حساس واقعی)
12. بخش «CI/CD»: توضیح کوتاه از پایپ‌لاین (چه زمانی اجرا می‌شود، چه کاری انجام می‌دهد)
13. بخش «نقشه راه (Roadmap)»: خلاصه‌ای از فازهای PRD که پیاده‌سازی شده‌اند
    (می‌توانی این را به‌صورت چک‌باکس ✅ نشان بدهی)
14. بخش «مشارکت (Contributing)»: راهنمای کوتاه برای Pull Request
    (branch naming، commit message convention، اجرای تست قبل از PR)
15. بخش «لایسنس»

از فرمت Markdown استاندارد گیت‌هاب استفاده کن (badges با shields.io، بلوک‌های کد
با syntax highlighting مناسب bash/python/yaml). زبان README را انگلیسی بنویس
مگر اینکه ترجیح بدهم فارسی باشد — از من بپرس.
```

**✅ تست و تایید:**
```
تمام دستورات نوشته‌شده در بخش Quick Start را واقعاً به‌ترتیب اجرا کن
(روی یک clone تازه یا حداقل با یک بررسی دقیق) تا مطمئن شویم هیچ مرحله‌ای
جا نیفتاده یا اشتباه نیست.
```

---

### ۱۴.۲ پرامپت تکمیلی: فایل‌های استاندارد گیت‌هاب

```
علاوه بر README، این فایل‌های استاندارد را هم برای ریپازیتوری بساز:

1. CONTRIBUTING.md: راهنمای دقیق‌تر مشارکت (workflow گیت، نحوه اجرای تست‌ها
   قبل از commit، نحوه گزارش باگ)
2. .github/PULL_REQUEST_TEMPLATE.md: قالب استاندارد برای توضیح تغییرات،
   چک‌لیست (تست نوشته شده؟ مستندات به‌روز شده؟) و لینک به issue مرتبط
3. .github/ISSUE_TEMPLATE/bug_report.md و .github/ISSUE_TEMPLATE/feature_request.md
4. CHANGELOG.md با فرمت Keep a Changelog، شروع‌شده از نسخه اولیه (Unreleased)
5. LICENSE (بر اساس تصمیمی که در فاز قبل درباره لایسنس گرفتیم)

اگر هرکدام از این فایل‌ها از قبل وجود دارند، به‌جای بازنویسی کامل،
محتوای فعلی را با استاندارد بالا هماهنگ و تکمیل کن.
```

**✅ تست و تایید:**
```
لیست همه فایل‌های جدید ساخته‌شده در .github/ و ریشه پروژه را نشان بده
تا مطمئن شوم چیزی جا نیفتاده.
```

---

## 📌 نکات تکمیلی

- قبل از فاز ۱۳.۲ (CD)، حتماً تصمیم بگیرید پروژه کجا هاست می‌شود (VPS شخصی، Railway، Liara، ArvanCloud و...)؛
  دستورات SSH/Deploy بسته به پلتفرم متفاوت است. اگر مطمئن نیستید، از Claude Code بخواهید
  گزینه‌ها را برایتان مقایسه کند.
- **هیچ‌وقت** مقدار واقعی Secretها (SSH key، توکن‌ها، رمز دیتابیس production) را
  مستقیم در چت یا در فایل‌های پروژه ننویسید — همیشه از GitHub Secrets استفاده کنید.
- بعد از فعال شدن CI، پیشنهاد می‌شود روی شاخه `main` قانون **Branch Protection** فعال کنید
  (Require status checks to pass before merging) — می‌توانید از Claude Code بخواهید
  راهنمای تنظیم آن در گیت‌هاب را هم برایتان بنویسد.
- اگر می‌خواهید badge پوشش تست (coverage) واقعی روی README داشته باشید،
  اتصال به Codecov یا Coveralls یک قدم اضافه‌ست که می‌توانید جداگانه از Claude Code بخواهید.
