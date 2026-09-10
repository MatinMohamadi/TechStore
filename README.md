<div align="center">

# 🖥️ TechStore

**فروشگاه آنلاین محصولات کامپیوتری — بک‌اند API با Django REST Framework**

پلتفرم فروش لپ‌تاپ، قطعات سخت‌افزاری و لوازم جانبی با کاتالوگ پیشرفته، سبد خرید، پرداخت آنلاین و پنل مدیریت.

[![CI Pipeline](https://github.com/MatinMohamadi/PC-Online-Shop/actions/workflows/ci.yml/badge.svg)](https://github.com/MatinMohamadi/PC-Online-Shop/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.1-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-A30000)](https://www.django-rest-framework.org/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## 📑 فهرست مطالب

- [درباره پروژه](#about)
- [تکنولوژی‌ها](#tech-stack)
- [پیش‌نیازها](#prerequisites)
- [راه‌اندازی سریع (Docker)](#quick-start)
- [راه‌اندازی بدون Docker (توسعه لوکال)](#local-dev)
- [ساختار پروژه](#structure)
- [اجرای تست‌ها](#tests)
- [مستندات API](#api-docs)
- [متغیرهای محیطی](#env-vars)
- [CI/CD](#cicd)
- [نقشه راه](#roadmap)
- [مشارکت](#contributing)
- [لایسنس](#license)

---

<a id="about"></a>
## 📖 درباره پروژه

**TechStore** یک فروشگاه آنلاین تخصصی فروش قطعات و محصولات کامپیوتری (لپ‌تاپ، قطعات سخت‌افزاری، مانیتور و لوازم جانبی) است که به‌صورت یک **Backend REST API** با Django و Django REST Framework پیاده‌سازی شده است. تجربه‌ای مشابه فروشگاه‌های بزرگ (دیجی‌کالا / Newegg) اما در مقیاس کوچک‌تر، ماژولار و کاملاً قابل توسعه — آماده برای اتصال به هر فرانت‌اند (React/Next.js) یا اپ موبایل.

### ✨ ویژگی‌های اصلی

- 🔐 **احراز هویت JWT** — ثبت‌نام، ورود، تمدید توکن، پروفایل و مدیریت آدرس‌ها
- 🗂 **کاتالوگ درختی** — دسته‌بندی‌های سلسله‌مراتبی، برندها و محصولات با فیلتر، جستجو، مرتب‌سازی و صفحه‌بندی
- 🛒 **سبد خرید هوشمند** — پشتیبانی از سبد مهمان (session-based) و ادغام خودکار سبد پس از ورود
- 🏷 **کد تخفیف** — اعتبارسنجی تاریخ انقضا، حداقل مبلغ خرید و سقف تعداد استفاده
- 📦 **مدیریت موجودی** — رزرو اتمیک موجودی هنگام خرید با جلوگیری از فروش بیش از حد (overselling)
- 💳 **پرداخت آنلاین** — درگاه زرین‌پال (پشتیبانی از Sandbox و Production) با verify تراکنش
- 🚚 **سفارش‌ها** — فرآیند Checkout کامل، شماره سفارش و تاریخچه وضعیت
- ⭐ **نظرات و امتیاز** — ثبت نظر فقط برای خریداران واقعی محصول + محاسبه میانگین امتیاز
- 🎫 **تیکت پشتیبانی** — گفتگوی کاربر و ادمین با مدیریت وضعیت تیکت
- 📧 **اعلان‌های Async** — ارسال ایمیل‌های تراکنشی (تایید سفارش و...) با Celery + Redis
- 🛠 **پنل مدیریت** — Django Admin سفارشی‌شده با django-jazzmin
- 📚 **مستندات خودکار** — Swagger / OpenAPI 3 با drf-spectacular

---

<a id="tech-stack"></a>
## 🛠 تکنولوژی‌ها

| دسته | تکنولوژی |
|---|---|
| زبان | Python 3.12 |
| فریم‌ورک | Django 5.1 + Django REST Framework 3.15 |
| دیتابیس | PostgreSQL 16 (SQLite فقط برای توسعه لوکال) |
| کش و صف پیام | Redis 7 + Celery 5 |
| احراز هویت | djangorestframework-simplejwt (JWT) |
| مستندات API | drf-spectacular (Swagger / OpenAPI) |
| پنل ادمین | django-jazzmin |
| سرور برنامه | Gunicorn + Nginx (Reverse Proxy) |
| فایل‌های استاتیک | WhiteNoise |
| استوریج مدیا | Local (توسعه) / S3-compatible (Production) |
| کانتینر | Docker + Docker Compose |
| تست و کیفیت کد | pytest، pytest-cov، Ruff، Black، isort |

---

<a id="prerequisites"></a>
## 📋 پیش‌نیازها

| ابزار | نسخه پیشنهادی | توضیح |
|---|---|---|
| [Docker](https://docs.docker.com/get-docker/) | 24+ | تنها پیش‌نیاز برای اجرای کامل پروژه |
| [Docker Compose](https://docs.docker.com/compose/) | v2+ | همراه Docker Desktop نصب می‌شود |
| [Python](https://www.python.org/downloads/) | 3.12+ | فقط برای توسعه لوکال (بدون Docker) |
| Git | آخرین نسخه | برای کلون کردن ریپازیتوری |

> 💡 اگر فقط می‌خواهید پروژه را با Docker اجرا کنید، به نصب Python نیازی نیست.

---

<a id="quick-start"></a>
## 🚀 راه‌اندازی سریع (Docker)

```bash
# ۱) کلون کردن پروژه
https://github.com/MatinMohamadi/TechStore.git
cd PC-Online-Shop

# ۲) متغیرهای محیطی
#    فایل .env.docker (خوانده‌شده توسط docker-compose) از قبل در ریپو موجود است
#    و با مقادیر پیش‌فرض توسعه کار می‌کند. برای شخصی‌سازی، آن را ویرایش کنید.
#    (نمونه کامل متغیرها: .env.example)

# ۳) ساخت و اجرای همه سرویس‌ها (PostgreSQL + Redis + Django + Celery + Nginx)
docker-compose up -d --build

# ۴) ساخت ابرکاربر ادمین
#    (Migrationها هنگام بالا آمدن سرویس web به‌صورت خودکار اجرا می‌شوند)
docker-compose exec web python manage.py createsuperuser

# ۵) (اختیاری) درج داده‌های نمونه در کاتالوگ
docker-compose exec web python manage.py seed_catalog
```

پس از اجرای موفق، سرویس‌ها در این آدرس‌ها در دسترس هستند:

| سرویس | آدرس |
|---|---|
| 📚 Swagger UI (مستندات API) | http://localhost:8000/api/docs/ |
| 🔌 پایه API | http://localhost:8000/api/ |
| 🛠 پنل مدیریت Django | http://localhost:8000/admin/ |
| ❤️ Health Check | http://localhost:8000/api/health/ |
| 🌐 Nginx (Reverse Proxy — سرو کردن static/media) | http://localhost/ (پورت 80) |

توقف و حذف سرویس‌ها:

```bash
docker-compose down       # توقف سرویس‌ها
docker-compose down -v    # توقف + حذف کامل volume دیتابیس
```

> 📝 نکته: سرویس `web` هنگام اجرا، به‌طور خودکار `migrate` و `collectstatic` را انجام می‌دهد (بخش `command` در `docker-compose.yml`)، بنابراین نیازی به اجرای دستی migration نیست.

---

<a id="local-dev"></a>
## 🐍 راه‌اندازی بدون Docker (توسعه لوکال)

اگر ترجیح می‌دهید مستقیم روی سیستم خودتان توسعه دهید، پیش‌فرض‌های محیط توسعه ساده هستند: **SQLite** به‌جای PostgreSQL، ایمیل در **کنسول** و اجرای **eager** تسک‌های Celery (بدون نیاز به Redis).

```bash
# ۱) ساخت و فعال‌سازی virtualenv
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# ۲) نصب وابستگی‌ها (شامل ابزارهای توسعه و تست)
pip install -r requirements-dev.txt

# ۳) متغیرهای محیطی
cp .env.example .env

# ۴) اعمال migrationها و ساخت ابرکاربر
python manage.py migrate
python manage.py createsuperuser

# ۵) (اختیاری) درج داده‌های نمونه
python manage.py seed_catalog

# ۶) اجرای سرور توسعه
python manage.py runserver
```

سپس API روی `http://127.0.0.1:8000/api/` و مستندات Swagger روی `http://127.0.0.1:8000/api/docs/` در دسترس است.

اجرای دستی Celery Worker (فقط اگر Redis لوکال دارید و می‌خواهید تسک‌ها واقعاً async اجرا شوند):

```bash
celery -A config worker --loglevel=info
```

> 🗄 برای استفاده از PostgreSQL در محیط توسعه، متغیر `DATABASE_URL` را در فایل `.env` از کامنت خارج کنید و مقدار اتصال خود را قرار دهید.

---

<a id="structure"></a>
## 📁 ساختار پروژه

```text
PC-Online-Shop/
├── accounts/            # کاربران: Custom User، ثبت‌نام/ورود JWT، آدرس‌ها
├── catalog/             # کاتالوگ: دسته‌بندی درختی، برند، محصول، ویژگی‌های فنی
│   └── management/commands/seed_catalog.py   # درج داده‌های نمونه
├── inventory/           # موجودی: انبار، StockItem، رزرو اتمیک و جلوگیری از overselling
├── cart/                # سبد خرید مهمان/کاربر + merge پس از لاگین
├── orders/              # سفارش‌ها: Checkout، وضعیت، تاریخچه وضعیت
├── payments/            # پرداخت: درگاه زرین‌پال، initiate/callback، verify تراکنش
├── promotions/          # تخفیف: کد تخفیف و اعتبارسنجی آن
├── reviews/             # نظرات و امتیاز محصولات (فقط خریداران واقعی)
├── shipping/            # روش‌های ارسال و هزینه (در توسعه)
├── support/             # تیکت پشتیبانی و پیام‌ها
├── notifications/       # اعلان‌ها و ایمیل‌های Async با Celery
├── config/              # پیکربندی: settings (base/dev/ci/production)، urls، wsgi/asgi
├── templates/
│   └── emails/          # قالب ایمیل‌های HTML
├── static/              # فایل‌های استاتیک
├── media/               # فایل‌های آپلودی (تصاویر محصول و...)
├── nginx/               # کانفیگ Nginx (Reverse Proxy)
├── tests/               # تست‌های یکپارچه (تست‌های هر اپ داخل خود اپ قرار دارند)
├── .github/workflows/   # پایپ‌لاین CI (GitHub Actions)
├── Dockerfile           # ایمیج multi-stage با non-root user و healthcheck
├── docker-compose.yml   # PostgreSQL + Redis + Web + Celery + Nginx
├── requirements.txt     # وابستگی‌های Production
├── requirements-dev.txt # ابزارهای توسعه (pytest, ruff, black, isort)
├── PRD.md               # سند نیازمندی‌های محصول
├── SECURITY_CHECKLIST.md# چک‌لیست امنیتی
└── manage.py
```

---

<a id="tests"></a>
## 🧪 اجرای تست‌ها

تست‌ها با **pytest** و پلاگین `pytest-django` نوشته شده‌اند و گزارش **Coverage** به‌صورت پیش‌فرض تولید می‌شود (تنظیمات در `setup.cfg`):

```bash
# اجرای همه تست‌ها + گزارش coverage متنی (term-missing)
pytest

# اجرای موازی و سریع‌تر با pytest-xdist
pytest -n auto

# فقط تست‌های یک اپ خاص
pytest accounts

# گزارش HTML تعاملی (خروجی: پوشه htmlcov/)
pytest --cov-report=html
```

برای مشاهده گزارش تعاملی Coverage، فایل `htmlcov/index.html` را در مرورگر باز کنید.

> ℹ️ تست‌ها با تنظیمات `config.settings.dev` و روی SQLite اجرا می‌شوند؛ نیازی به PostgreSQL یا Redis لوکال نیست.

---

<a id="api-docs"></a>
## 📚 مستندات API

مستندات تعاملی API با **drf-spectacular** تولید می‌شود:

- **Swagger UI:** [`/api/docs/`](http://localhost:8000/api/docs/) — مشاهده و اجرای تستی همه Endpointها از داخل مرورگر
- **OpenAPI Schema:** [`/api/schema/`](http://localhost:8000/api/schema/) — خروجی استاندارد OpenAPI 3 (نمونه ذخیره‌شده: `api_schema.json`)

### 🔌 خلاصه Endpointها

| حوزه | Endpoint | توضیح |
|---|---|---|
| احراز هویت | `POST /api/auth/register/` | ثبت‌نام |
| | `POST /api/auth/login/` | ورود و دریافت توکن JWT |
| | `POST /api/auth/token/refresh/` | تمدید access token |
| | `GET/PUT/PATCH /api/auth/me/` | مشاهده و ویرایش پروفایل |
| آدرس‌ها | `GET/POST /api/addresses/` | لیست و ثبت آدرس |
| | `GET/PUT/PATCH/DELETE /api/addresses/{id}/` | جزئیات، ویرایش و حذف آدرس |
| کاتالوگ | `GET /api/categories/` | دسته‌بندی‌های درختی |
| | `GET /api/brands/` | لیست برندها |
| | `GET /api/products/` | محصولات با فیلتر، جستجو و مرتب‌سازی |
| سبد خرید | `GET /api/cart/` | مشاهده سبد جاری (مهمان یا کاربر) |
| | `POST /api/cart/items/` | افزودن آیتم به سبد |
| | `PATCH/DELETE /api/cart/items/{id}/` | تغییر تعداد / حذف آیتم |
| | `POST /api/cart/merge/` | ادغام سبد مهمان با سبد کاربر پس از لاگین |
| تخفیف | `POST /api/cart/apply-coupon/` | اعمال کد تخفیف روی سبد |
| سفارش‌ها | `POST /api/orders/checkout/` | تبدیل سبد به سفارش |
| | `GET /api/orders/` | لیست سفارش‌های کاربر |
| | `GET /api/orders/{id}/` | جزئیات یک سفارش |
| پرداخت | `POST /api/payments/initiate/` | شروع پرداخت و دریافت URL درگاه |
| | `GET /api/payments/callback/` | بازگشت از درگاه و verify تراکنش |
| نظرات | `GET/POST /api/products/{id}/reviews/` | مشاهده و ثبت نظر محصول |
| پشتیبانی | `GET/POST /api/tickets/` | لیست و ایجاد تیکت |
| | `GET /api/tickets/{id}/` | جزئیات تیکت |
| | `POST /api/tickets/{id}/messages/` | ارسال پیام در تیکت |
| | `POST /api/tickets/{id}/status/` | تغییر وضعیت تیکت (ادمین) |
| سلامت | `GET /api/health/` | Health check |

---

<a id="env-vars"></a>
## 🔐 متغیرهای محیطی

همه تنظیمات از طریق متغیرهای محیطی خوانده می‌شوند (با `django-environ`). نمونه کامل در فایل [`.env.example`](.env.example) موجود است — برای شروع کافی است آن را به `.env` کپی کنید:

| متغیر | مقدار نمونه | توضیح |
|---|---|---|
| `DJANGO_SECRET_KEY` | `your-secret-key-here` | کلید مخفی Django — در Production حتماً مقدار قوی و منحصربه‌فرد قرار دهید |
| `DJANGO_DEBUG` | `True` | حالت دیباگ — در Production باید `False` باشد |
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | ماژول تنظیمات: `dev` / `ci` / `production` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | هاست‌های مجاز (جدا شده با کاما) |
| `DATABASE_URL` | `postgres://user:pass@host:5432/db` | آدرس اتصال PostgreSQL — اگر خالی باشد از SQLite استفاده می‌شود (فقط توسعه) |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,...` | دامنه‌های مجاز CORS (فرانت‌اند) |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `30` | عمر access token (دقیقه) |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | عمر refresh token (روز) |
| `ZARINPAL_MERCHANT_ID` | `your-zarinpal-merchant-id` | شناسه پذیرنده درگاه زرین‌پال |
| `ZARINPAL_SANDBOX` | `True` | استفاده از محیط آزمایشی زرین‌پال |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | آدرس Broker سلری |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | بک‌اند ذخیره نتایج سلری |
| `AWS_ACCESS_KEY_ID` | — | کلید دسترسی S3 (استوریج Production) |
| `AWS_SECRET_ACCESS_KEY` | — | کلید مخفی S3 |
| `AWS_STORAGE_BUCKET_NAME` | — | نام Bucket |
| `AWS_S3_ENDPOINT_URL` | — | Endpoint سرویس S3-compatible (MinIO / Liara / ArvanCloud) |
| `AWS_S3_REGION_NAME` | — | Region سرویس S3 |
| `EMAIL_HOST` | `smtp.gmail.com` | سرور SMTP |
| `EMAIL_PORT` | `587` | پورت SMTP |
| `EMAIL_USE_TLS` | `True` | استفاده از TLS |
| `EMAIL_HOST_USER` | — | نام کاربری ایمیل |
| `EMAIL_HOST_PASSWORD` | — | رمز عبور ایمیل |
| `DEFAULT_FROM_EMAIL` | `TechStore <noreply@techstore.com>` | آدرس فرستنده پیش‌فرض ایمیل‌ها |
| `DB_PASSWORD` | `change-me-in-production` | رمز دیتابیس در محیط Docker |

> ⚠️ **امنیت:** هرگز مقادیر واقعی و حساس (Secret Key، رمز دیتابیس، Merchant ID واقعی و...) را در ریپو commit نکنید. فایل `.env` در `.gitignore` قرار دارد و فایل `.env.docker` فقط شامل مقادیر پیش‌فرض توسعه است.

---

<a id="cicd"></a>
## 🔄 CI/CD

پایپ‌لاین CI با **GitHub Actions** در فایل [`.github/workflows/ci.yml`](.github/workflows/ci.yml) تعریف شده است.

**زمان اجرا:** روی هر `push` به شاخه‌های `main` و `develop` و روی هر Pull Request به `main`.

### Job اول: `lint-and-test`

- بالا آوردن **PostgreSQL 16** و **Redis 7** به‌عنوان Service Containers (هم‌نسخه با `docker-compose.yml`)
- نصب وابستگی‌ها از `requirements-dev.txt` با کش pip
- بررسی کیفیت کد: `ruff check` + `black --check` + `isort --check-only`
- بررسی‌های سیستمی Django: `manage.py check --deploy`
- اجرای کامل تست‌ها با `pytest` و تولید گزارش **Coverage** (متنی + HTML + XML)
- آپلود گزارش HTML به‌صورت Artifact (نگهداری ۳۰ روز) و ارسال به Codecov (اختیاری — فقط روی push به `main`)

### Job دوم: `docker-build`

- پس از موفقیت Job اول اجرا می‌شود (`needs: lint-and-test`)
- ایمیج Docker پروژه را Build می‌کند تا سلامت `Dockerfile` تضمین شود (بدون Push)

> 🚧 مرحله **CD** (استقرار خودکار) هنوز پیاده‌سازی نشده و در نقشه راه قرار دارد — جزئیات آن به انتخاب هاست مقصد بستگی دارد.

---

<a id="roadmap"></a>
## 🗺 نقشه راه

وضعیت پیاده‌سازی فازهای تعریف‌شده در [PRD.md](PRD.md):

- [] **فاز ۰** — راه‌اندازی پروژه (settings تفکیک‌شده، django-environ، Git)
- [] **فاز ۱** — احراز هویت و کاربران (Custom User، JWT، آدرس‌ها)
- [] **فاز ۲** — کاتالوگ محصولات (دسته‌بندی، برند، محصول + فیلتر و جستجو)
- [] **فاز ۳** — موجودی (StockItem، جلوگیری از overselling)
- [] **فاز ۴** — سبد خرید (مهمان + کاربر، merge)
- [] **فاز ۵** — سفارش‌ها (Checkout و تاریخچه وضعیت)
- [] **فاز ۶** — پرداخت (زرین‌پال Sandbox)
- [] **فاز ۷** — تخفیف و کمپین (کد تخفیف)
- [] **فاز ۸** — نظرات و امتیاز
- [] **فاز ۹** — پشتیبانی (تیکت)
- [] **فاز ۱۰** — اعلان‌ها و Celery (ایمیل Async)
- [] **فاز ۱۱** — سخت‌سازی و Docker (آماده Production)
- [] **فاز ۱۲** — مستندسازی API (Swagger)
- [] **فاز ۱۳** — CI با GitHub Actions
- [ ] **فاز ۱۳.۲** — CD و استقرار خودکار (در انتظار انتخاب هاست)
- [ ] **خارج از محدوده MVP** — مارکت‌پلیس چندفروشنده، اپ موبایل، سیستم توصیه‌گر، چت زنده

---

<a id="contributing"></a>
## 🤝 مشارکت

مشارکت در این پروژه خوش‌آمد است! 🎉 برای ارسال تغییرات مراحل زیر را دنبال کنید:

**۱.** پروژه را Fork کنید و یک شاخه جدید بسازید:

```bash
git checkout -b feature/my-feature    # ویژگی جدید
git checkout -b fix/my-fix            # رفع باگ
```

**۲.** تغییرات را با پیام‌های Commit در قالب **Conventional Commits** ثبت کنید:

```text
feat: افزودن endpoint علاقه‌مندی‌ها
fix: اصلاح محاسبه مبلغ نهایی سبد خرید
docs: به‌روزرسانی README
test: افزودن تست برای apply-coupon
refactor: ساده‌سازی سرویس موجودی
chore: به‌روزرسانی وابستگی‌ها
```

**۳.** قبل از ارسال Pull Request، این بررسی‌ها را لوکال اجرا کنید (همان بررسی‌های CI):

```bash
ruff check .                            # لینتر
black --check .                         # فرمت کد
isort --check-only --profile black .    # مرتب‌سازی importها
pytest                                  # تست‌ها + coverage
```

**۴.** شاخه را Push کنید و یک Pull Request به شاخه `main` باز کنید — پایپ‌لاین CI به‌صورت خودکار اجرا می‌شود و برای Merge باید **سبز** باشد. ✅

### 🌿 نام‌گذاری شاخه‌ها

| پیشوند | کاربرد |
|---|---|
| `feature/` | افزودن ویژگی جدید |
| `fix/` | رفع باگ |
| `docs/` | تغییر مستندات |
| `refactor/` | بازآرایی کد بدون تغییر رفتار |

---

<a id="license"></a>
## 📄 لایسنس

این پروژه تحت لایسنس **[MIT](LICENSE)** منتشر شده است — آزادانه می‌توانید از آن استفاده، تغییر و توزیع کنید.

---

<div align="center">

ساخته‌شده با ❤️ توسط [Matin Mohamadi](https://github.com/MatinMohamadi)

⭐ اگر این پروژه برایتان مفید بود، به آن Star بدهید!

</div>
