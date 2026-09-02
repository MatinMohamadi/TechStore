# PRD: فروشگاه آنلاین محصولات کامپیوتری (TechStore)

**نسخه:** 1.0
**تاریخ:** شهریور ۱۴۰۵
**Backend:** Django + Django REST Framework
**هدف سند:** این PRD طوری نوشته شده که بتوانید آن را فاز به فاز، به عنوان پرامپت‌های مجزا، به Claude Code بدهید و هر فاز یک deliverable کامل و قابل تست تحویل دهد.

---

## ۱. خلاصه محصول (Product Overview)

### ۱.۱ چشم‌انداز
TechStore یک فروشگاه آنلاین تخصصی فروش قطعات و محصولات کامپیوتری (لپ‌تاپ، قطعات سخت‌افزاری، لوازم جانبی، مانیتور، شبکه) است که تجربه‌ای مشابه فروشگاه‌های بزرگ (دیجی‌کالا/Newegg) اما در مقیاس کوچک‌تر و قابل توسعه ارائه می‌دهد.

### ۱.۲ کاربران هدف
| Persona | توضیح | نیاز اصلی |
|---|---|---|
| خریدار عادی | کاربری که به دنبال خرید یک قطعه یا محصول است | جستجوی سریع، مقایسه، پرداخت امن |
| گیمر/سازنده سیستم | کاربری که سیستم می‌بندد و به مشخصات فنی دقیق نیاز دارد | فیلتر پیشرفته بر اساس spec، Compatibility |
| مدیر فروشگاه (Admin) | مسئول مدیریت محصولات، سفارش‌ها، موجودی | پنل مدیریت قدرتمند |
| پشتیبانی فروش | پاسخ به تیکت و پیگیری سفارش‌ها | مدیریت سفارش و تیکت |

### ۱.۳ اهداف کسب‌وکار
- راه‌اندازی MVP قابل فروش در کوتاه‌ترین زمان
- معماری قابل توسعه (افزودن marketplace، اپ موبایل در آینده)
- SEO مناسب برای صفحات محصول
- آماده برای درگاه پرداخت ایرانی (زرین‌پال/آیدی‌پی) و/یا Stripe

---

## ۲. معماری فنی (Technical Architecture)

### ۲.۱ Stack پیشنهادی
- **Backend:** Django 5.x + Django REST Framework
- **Database:** PostgreSQL (SQLite فقط برای dev اولیه)
- **Cache/Queue:** Redis + Celery (برای ایمیل، پردازش سفارش، اعلان‌ها)
- **Auth:** JWT (djangorestframework-simplejwt) + امکان OTP/شماره موبایل
- **Search:** PostgreSQL Full-Text Search در MVP، امکان ارتقا به Elasticsearch
- **Media Storage:** Local در dev، S3-compatible (MinIO/Liara/ArvanCloud) در production
- **Frontend:** پیشنهاد React (Next.js) جدا از بک‌اند، مصرف‌کننده REST API — اما این PRD صرفاً بک‌اند Django و API را پوشش می‌دهد؛ فرانت را می‌توان در PRD جدا تعریف کرد
- **Admin Panel:** Django Admin سفارشی‌شده (django-jazzmin یا مشابه) برای مدیریت اولیه، با امکان توسعه به پنل اختصاصی

### ۲.۲ ساختار اپ‌های Django (پیشنهادی)
```
techstore/
├── config/                 # settings, urls, wsgi/asgi
├── apps/
│   ├── accounts/           # کاربران، احراز هویت، آدرس‌ها
│   ├── catalog/            # دسته‌بندی، برند، محصول، ویژگی‌های فنی
│   ├── inventory/          # موجودی، انبار
│   ├── cart/                # سبد خرید
│   ├── orders/              # سفارش، وضعیت سفارش
│   ├── payments/            # درگاه پرداخت، تراکنش
│   ├── shipping/            # روش‌های ارسال، هزینه
│   ├── reviews/             # نظرات و امتیاز محصول
│   ├── promotions/          # کد تخفیف، کمپین
│   ├── notifications/       # ایمیل/پیامک/اعلان
│   └── support/             # تیکت پشتیبانی
├── static/
├── media/
└── tests/
```

---

## ۳. مدل‌های داده کلیدی (Data Models)

> این بخش پایه‌ی اصلی برای شروع کدنویسی با Claude Code است. هر مدل باید دقیقاً با همین فیلدها (یا نزدیک به آن) پیاده‌سازی شود.

### ۳.۱ accounts
- **User** (Custom User Model): email, phone_number, first_name, last_name, is_verified, date_joined
- **Address**: user (FK), title, province, city, postal_code, full_address, receiver_name, receiver_phone, is_default

### ۳.۲ catalog
- **Category**: name, slug, parent (self FK برای دسته‌بندی درختی), icon, order
- **Brand**: name, slug, logo, description
- **Product**: title, slug, category (FK), brand (FK), description, base_price, discount_price, sku, status (draft/active/inactive), is_featured, warranty_months, created_at, updated_at
- **ProductImage**: product (FK), image, alt_text, order, is_main
- **ProductAttribute** (ویژگی فنی پویا مثل RAM، CPU Socket، توان پاور): name, unit
- **ProductAttributeValue**: product (FK), attribute (FK), value
- **ProductVariant** (برای رنگ/ظرفیت مختلف): product (FK), sku, attributes(JSON), price_diff, stock

### ۳.۳ inventory
- **Warehouse**: name, address
- **StockItem**: product/variant (FK), warehouse (FK), quantity, reserved_quantity, low_stock_threshold

### ۳.۴ cart
- **Cart**: user (FK, nullable برای مهمان), session_key, created_at
- **CartItem**: cart (FK), product/variant (FK), quantity, unit_price_snapshot

### ۳.۵ orders
- **Order**: user (FK), order_number, status (pending/paid/processing/shipped/delivered/canceled/refunded), shipping_address (FK), total_amount, discount_amount, shipping_cost, final_amount, created_at
- **OrderItem**: order (FK), product/variant (FK), quantity, unit_price, total_price
- **OrderStatusHistory**: order (FK), status, changed_at, note

### ۳.۶ payments
- **Payment**: order (FK), gateway (zarinpal/idpay/stripe), amount, status (pending/success/failed), transaction_ref, paid_at

### ۳.۷ shipping
- **ShippingMethod**: name, base_cost, estimated_days

### ۳.۸ reviews
- **Review**: product (FK), user (FK), rating (1-5), comment, is_approved, created_at

### ۳.۹ promotions
- **Coupon**: code, discount_type (percent/fixed), value, min_order_amount, max_uses, used_count, valid_from, valid_to, is_active

### ۳.۱۰ support
- **Ticket**: user (FK), subject, status (open/answered/closed), created_at
- **TicketMessage**: ticket (FK), sender (user/admin), message, created_at

---

## ۴. فهرست ویژگی‌ها (Feature List)

### ۴.۱ سمت کاربر (Customer-facing)
- ثبت‌نام/ورود (ایمیل یا شماره موبایل + OTP)، مدیریت پروفایل و آدرس‌ها
- مرور دسته‌بندی‌ها (درختی: مثلاً لپ‌تاپ > گیمینگ)
- جستجوی محصول با فیلتر (برند، قیمت، ویژگی فنی، موجودی) و مرتب‌سازی
- صفحه محصول با گالری تصویر، مشخصات فنی جدولی، نظرات و امتیاز
- سبد خرید (مهمان و کاربر لاگین‌شده، merge سبد بعد از لاگین)
- اعمال کد تخفیف
- انتخاب آدرس و روش ارسال
- پرداخت آنلاین (درگاه)
- پیگیری وضعیت سفارش
- ثبت نظر و امتیاز برای محصولات خریداری‌شده
- تیکت پشتیبانی
- لیست علاقه‌مندی‌ها (Wishlist)
- مقایسه محصولات (Compare)

### ۴.۲ سمت مدیریت (Admin)
- مدیریت کامل محصولات، دسته‌بندی، برند، موجودی
- مدیریت سفارش‌ها و تغییر وضعیت
- مدیریت کدهای تخفیف و کمپین
- مدیریت کاربران
- گزارش فروش پایه (Dashboard ساده: تعداد سفارش، درآمد، محصولات پرفروش)
- مدیریت نظرات (تایید/رد)
- مدیریت تیکت‌های پشتیبانی

### ۴.۳ خارج از محدوده MVP (Out of Scope فاز اول)
- مارکت‌پلیس چندفروشنده
- اپلیکیشن موبایل نیتیو
- سیستم توصیه‌گر هوشمند (Recommendation Engine)
- چت زنده real-time

---

## ۵. نقشه راه پیاده‌سازی برای Claude Code (Implementation Roadmap)

> هر فاز را می‌توانید به‌صورت یک پرامپت جداگانه به Claude Code بدهید. ترتیب فازها رعایت شود چون هر فاز به فاز قبل وابسته است. در انتهای هر فاز یک "معیار پذیرش" آمده تا بدانید فاز کامل شده یا نه.

### فاز ۰ — راه‌اندازی پروژه
**کار:** ایجاد پروژه Django با ساختار apps بالا، تنظیم settings (dev/prod جدا)، اتصال PostgreSQL، نصب DRF، تنظیم CORS، راه‌اندازی .env با django-environ، تنظیم Git.
**خروجی:** پروژه اجرا می‌شود، `python manage.py runserver` کار می‌کند، اتصال دیتابیس برقرار است.
**معیار پذیرش:** `manage.py check` بدون خطا، مایگریشن اولیه اجرا می‌شود.

### فاز ۱ — احراز هویت و کاربران (accounts)
**کار:** پیاده‌سازی Custom User Model، APIهای ثبت‌نام/ورود با JWT، مدیریت آدرس‌ها، تست‌های واحد.
**خروجی:** endpointهای `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`, `/api/addresses/`.
**معیار پذیرش:** یک کاربر می‌تواند ثبت‌نام کند، توکن بگیرد، آدرس اضافه/ویرایش/حذف کند.

### فاز ۲ — کاتالوگ محصولات (catalog)
**کار:** مدل‌های Category, Brand, Product, ProductImage, ProductAttribute/Value، سریالایزرها، APIهای لیست/جزئیات با فیلتر و جستجو و صفحه‌بندی، ثبت در Django Admin.
**خروجی:** endpointهای `/api/categories/`, `/api/brands/`, `/api/products/` (با query params برای فیلتر/سرچ/سورت).
**معیار پذیرش:** می‌توان محصول از طریق Admin اضافه کرد و از طریق API با فیلتر برند/دسته/قیمت آن را دریافت کرد.

### فاز ۳ — موجودی (inventory)
**کار:** اتصال StockItem به Product/Variant، منطق کاهش/افزایش موجودی هنگام سفارش، جلوگیری از overselling.
**خروجی:** فیلد stock در پاسخ API محصول به‌روز و دقیق است.
**معیار پذیرش:** با ثبت سفارش موجودی به‌درستی کم می‌شود و در صورت ناکافی بودن خطای مناسب برمی‌گردد.

### فاز ۴ — سبد خرید (cart)
**کار:** مدل Cart/CartItem، پشتیبانی سبد مهمان (session-based) و سبد کاربر، merge بعد از لاگین، APIهای افزودن/حذف/به‌روزرسانی تعداد.
**خروجی:** endpointهای `/api/cart/`, `/api/cart/items/`.
**معیار پذیرش:** کاربر مهمان سبد می‌سازد، بعد از لاگین سبدش حفظ می‌شود.

### فاز ۵ — سفارش‌ها (orders)
**کار:** فرآیند checkout: تبدیل سبد به سفارش، محاسبه هزینه ارسال و تخفیف، مدل OrderStatusHistory، APIهای مشاهده سفارش‌های کاربر.
**خروجی:** endpointهای `/api/orders/`, `/api/orders/{id}/`.
**معیار پذیرش:** کاربر می‌تواند سفارش ثبت کند و وضعیت آن را ببیند.

### فاز ۶ — پرداخت (payments)
**کار:** اتصال به یک درگاه (مثلاً زرین‌پال Sandbox)، مدل Payment، callback و verify، به‌روزرسانی وضعیت سفارش پس از پرداخت موفق.
**خروجی:** endpointهای `/api/payments/initiate/`, `/api/payments/callback/`.
**معیار پذیرش:** یک تراکنش تستی کامل (ایجاد → پرداخت → verify → تغییر وضعیت سفارش) با موفقیت انجام می‌شود.

### فاز ۷ — تخفیف و کمپین (promotions)
**کار:** مدل Coupon، اعمال روی سبد/سفارش با اعتبارسنجی (تاریخ، حداقل خرید، تعداد استفاده).
**خروجی:** endpoint `/api/cart/apply-coupon/`.
**معیار پذیرش:** کد تخفیف معتبر مبلغ نهایی را درست محاسبه می‌کند، کد نامعتبر خطای مناسب می‌دهد.

### فاز ۸ — نظرات و امتیاز (reviews)
**کار:** مدل Review، محدودیت ثبت نظر فقط برای خریداران محصول، محاسبه میانگین امتیاز روی Product.
**خروجی:** endpoint `/api/products/{id}/reviews/`.
**معیار پذیرش:** فقط کاربری که محصول را خریده می‌تواند نظر ثبت کند؛ میانگین امتیاز در صفحه محصول درست است.

### فاز ۹ — پشتیبانی (support)
**کار:** مدل Ticket/TicketMessage، APIهای ایجاد تیکت و ارسال پیام، تغییر وضعیت توسط ادمین.
**خروجی:** endpointهای `/api/tickets/`.
**معیار پذیرش:** کاربر تیکت باز می‌کند، پیام رد و بدل می‌شود، ادمین می‌تواند ببندد.

### فاز ۱۰ — اعلان‌ها (notifications) و Celery
**کار:** راه‌اندازی Celery + Redis، ارسال ایمیل تایید سفارش، ایمیل تغییر وضعیت سفارش.
**خروجی:** تسک async ارسال ایمیل فعال است.
**معیار پذیرش:** بعد از ثبت سفارش، ایمیل تایید (حداقل در کنسول/mailhog) ارسال می‌شود.

### فاز ۱۱ — سخت‌سازی و آماده‌سازی Production
**کار:** تنظیم permission classes دقیق روی همه endpointها، rate limiting، لاگ‌گیری، تنظیم CORS نهایی، تست‌های امنیتی پایه، تنظیم static/media برای production (S3)، Dockerfile و docker-compose.
**خروجی:** پروژه Dockerized و آماده deploy.
**معیار پذیرش:** `docker-compose up` کل پروژه (Django + PostgreSQL + Redis) را بالا می‌آورد.

### فاز ۱۲ — مستندسازی API
**کار:** افزودن drf-spectacular یا drf-yasg برای مستندات Swagger/OpenAPI.
**خروجی:** صفحه `/api/docs/` مستندات کامل همه endpointها را نشان می‌دهد.
**معیار پذیرش:** تمام endpointهای فازهای قبل در Swagger قابل مشاهده و تست هستند.

---

## ۶. الزامات غیرعملکردی (Non-Functional Requirements)

| دسته | الزام |
|---|---|
| امنیت | HTTPS اجباری در production، هش صحیح پسورد (Django default PBKDF2 یا Argon2)، Rate limiting روی login/OTP، اعتبارسنجی ورودی‌ها، جلوگیری از IDOR در همه endpointهای سفارش/پرداخت |
| کارایی | Pagination اجباری روی همه لیست‌ها (page_size پیش‌فرض ۲۰)، ایندکس دیتابیس روی فیلدهای پرکاربرد جستجو (slug, category, brand, price) |
| مقیاس‌پذیری | جداسازی apps، امکان جایگزینی PostgreSQL Search با Elasticsearch بدون تغییر معماری اصلی |
| SEO | slug برای محصول/دسته، متاتگ قابل تنظیم روی هر محصول |
| تست | حداقل test coverage روی مدل‌ها و APIهای حیاتی (auth, cart, order, payment) |
| لاگ و مانیتورینگ | لاگ خطاهای پرداخت و سفارش به‌صورت جداگانه و قابل ردیابی |

---

## ۷. معیارهای پذیرش نهایی MVP (Definition of Done)

- کاربر می‌تواند از جستجو تا پرداخت موفق، یک خرید کامل انجام دهد.
- ادمین می‌تواند محصول جدید اضافه کند و در سایت/API قابل مشاهده باشد.
- موجودی هنگام خرید به‌درستی مدیریت می‌شود (بدون overselling).
- تمام APIهای حیاتی دارای مستندات Swagger هستند.
- پروژه با Docker قابل اجرا در محیط production است.

---

## ۸. نکات برای استفاده این سند با Claude Code

1. هر فاز را به‌صورت جداگانه در یک پرامپت مطرح کنید (مثلاً: "فاز ۲ را طبق این PRD پیاده‌سازی کن").
2. قبل از شروع هر فاز، از Claude Code بخواهید خلاصه‌ای از فاز قبل و وضعیت فعلی پروژه را بررسی کند تا context حفظ شود.
3. بعد از هر فاز، تست‌های مربوطه را اجرا و از معیار پذیرش همان فاز مطمئن شوید، سپس فاز بعد را شروع کنید.
4. تغییرات مدل داده (فیلد اضافه/حذف) را ترجیحاً در همان فازِ مرتبط انجام دهید تا migration historyتمیز بماند.
5. برای فرانت‌اند (اگر مدنظر است)، پیشنهاد می‌شود یک PRD جداگانه برای Next.js/React نوشته و بعد از تکمیل فاز API مربوطه، به‌صورت موازی پیش برود.

---

*پایان سند*
