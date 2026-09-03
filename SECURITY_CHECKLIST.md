# TechStore — Security Checklist (Phase 11)

## Authentication & Authorization

- [x] **Custom User Model** — email-based, no default username
- [x] **JWT Authentication** — short-lived access tokens (30 min), refresh rotation
- [x] **Password validation** — Django's built-in validators (min length, complexity)
- [x] **IsAuthenticated** on all personal endpoints (cart, orders, payments, addresses, tickets)
- [x] **Owner-only access** — every user can only see/modify their own resources:
  - Addresses: `Address.objects.filter(user=request.user)`
  - Orders: `Order.objects.filter(user=request.user)`
  - Payments: ownership validated via order ownership
  - Tickets: owner or staff only (`IsOwnerOrStaff` permission)
  - Cart: user-based or session-based (guest)
- [x] **Admin-only** endpoints: ticket status change (`IsAdminUser`)

## IDOR Protection (Insecure Direct Object Reference)

- [x] **Orders** — `get_queryset()` filters by `user=request.user` (404 for others)
- [x] **Payments** — order lookup validates `order.user == request.user`
- [x] **Addresses** — queryset filtered by user, 404 for non-owner
- [x] **Tickets** — `IsOwnerOrStaff` permission class
- [x] **Cart** — user-based or session-based isolation

## Rate Limiting (Throttling)

- [x] **Global default**: anon 100/hour, authenticated 1000/hour
- [x] **Login/Register**: 10/minute (brute-force protection)
- [x] **Payment initiation**: 20/hour

## Input Validation

- [x] **DRF Serializers** — all inputs validated through serializers
- [x] **Password confirmation** — required on registration
- [x] **Quantity validation** — min_value=1 on cart items
- [x] **Email validation** — EmailField on User model

## Database Security

- [x] **PostgreSQL** in production (not SQLite)
- [x] **F() expressions** — atomic stock operations prevent race conditions
- [x] **select_for_update** — row locking on inventory operations
- [x] **Database constraints** — `reserved_lte_quantity` CHECK constraint

## Django Security Settings (Production)

- [x] `DEBUG = False`
- [x] `SECRET_KEY` from environment variable
- [x] `SECURE_SSL_REDIRECT = True`
- [x] `SECURE_HSTS_SECONDS = 31536000`
- [x] `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- [x] `SESSION_COOKIE_SECURE = True`
- [x] `CSRF_COOKIE_SECURE = True`
- [x] `X_FRAME_OPTIONS = "DENY"`
- [x] `SECURE_CONTENT_TYPE_NOSNIFF = True`
- [x] `ALLOWED_HOSTS` configured via environment

## Payment Security

- [x] **API keys in .env** — never hardcoded
- [x] **Payment verification** — always verified server-side with gateway
- [x] **Amount verification** — gateway verify uses stored payment amount
- [x] **Transaction reference** — unique per payment, logged for audit

## Infrastructure

- [x] **Docker** — isolated containers for web, db, redis, celery
- [x] **Non-root user** — Docker container runs as `app` user
- [x] **Health checks** — on all Docker services
- [x] **Nginx** — reverse proxy, security headers, static file serving
- [x] **Structured logging** — separate files for payments/orders/errors

## Remaining (Manual Steps)

- [ ] Obtain SSL certificate (Let's Encrypt / cloud provider)
- [ ] Set strong `SECRET_KEY` in production `.env`
- [ ] Set strong `DB_PASSWORD` in production `.env`
- [ ] Configure `ALLOWED_HOSTS` with actual domain
- [ ] Configure CORS for actual frontend domain
- [ ] Set up email SMTP credentials
- [ ] Configure S3 storage keys (if using cloud storage)
- [ ] Run `python manage.py check --deploy` for final audit
