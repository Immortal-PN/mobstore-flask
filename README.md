# MobStore

Premium mobile storefront built with Flask, PostgreSQL, and optional Cloudinary image uploads.

## What is implemented

- Premium redesigned storefront with preserved dark theme direction
- Customer registration and login
- Search, filter, product details, cart, checkout, invoice
- Warranty/service request flow
- Admin dashboard for products, orders, revenue, and service queue
- PostgreSQL-backed schema bootstrap for Railway deployments
- Optional Cloudinary uploads for admin product images

## Railway environment variables

Set these in Railway before going live:

- `SECRET_KEY`
- `DATABASE_URL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

Optional for image uploads:

- `CLOUDINARY_URL`

Or:

- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

Recommended:

- `FLASK_ENV=production`

## Start command

The app uses:

```txt
web: gunicorn app:app
```

## Production checklist

1. Open the deployed site and create a user account.
2. Login and test add-to-cart, cart update, checkout, and invoice.
3. Open `/admin` and login with your Railway admin credentials.
4. Add one product with an image URL or Cloudinary upload.
5. Edit and delete a product from the dashboard.
6. Submit a service request and update its status from admin.
7. Confirm orders, products, and service requests are visible in PostgreSQL.

## Notes

- If Cloudinary is not configured, product creation still works with direct image URLs.
- The app auto-creates missing tables and fills in required new columns for older PostgreSQL schemas.
- Default seeded admin credentials are only a fallback. Override them in Railway.
