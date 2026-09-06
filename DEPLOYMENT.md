# Production deployment

## Render

Create a new Render Blueprint from this repository. Render will read
`render.yaml`, create the web service and PostgreSQL database, seed the
database, and start Gunicorn on Render's `$PORT`.

For an existing Render service, open **Settings** and change **Start Command**
to exactly:

```bash
python3 seed.py && exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --access-logfile - run:app
```

The preferred command is `run:app`; `app:app` is also supported for older
Render service settings. Do not use only `python3 seed.py`: `seed.py` exits after
seeding; `exec gunicorn ...` must run afterward so Render has a persistent web
process.

In the Vercel frontend project, set this environment variable and redeploy the
frontend:

```text
API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com/api
```

Replace `YOUR-RENDER-SERVICE` with the exact hostname shown in Render. Do not
use `http://localhost:5000` in a deployed frontend. The cart API supports both
`POST /api/cart` and `POST /api/cart/items`.

Set the `sync: false` values in the Render dashboard after the first Blueprint
sync:

- `CORS_ORIGINS`: the exact frontend URL, such as `https://app.example.com`.
- `PESAPAL_CONSUMER_KEY` and `PESAPAL_CONSUMER_SECRET`.
- `PESAPAL_IPN_ID`.
- `PESAPAL_CALLBACK_URL`: `https://pageturn-api.onrender.com/api/orders/pesapal/callback`.

Use the sandbox Pesapal URL until sandbox payment testing is complete. Change
it to `https://pay.pesapal.com/v3` for production Pesapal credentials.

## Required services

- A PostgreSQL database.
- A public HTTPS URL for this API. Pesapal cannot call localhost or a private URL.
- A frontend origin listed in `CORS_ORIGINS`.

## Environment

Copy `.env.example` into your deployment provider's environment settings. Do
not commit a real `.env` file. Generate `JWT_SECRET_KEY` with a password
manager or a cryptographically secure random generator.

Use the sandbox values in `.env.example` while testing Pesapal. Switch
`PESAPAL_BASE_URL` to `https://pay.pesapal.com/v3` for production credentials.
Register these public URLs in Pesapal:

- Callback: `/api/orders/pesapal/callback`
- IPN: `/api/orders/pesapal/ipn`

## Database migration

The current Render Blueprint runs `seed.py` during deployment because this
repository does not yet contain a committed Alembic migration directory. Before
using a multi-instance production plan, create and commit the initial migration
against the current models:

```bash
flask --app run.py db init
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
```

For the next release, generate a migration for the Pesapal order fields and
apply it with `flask --app run.py db upgrade`. Production startup deliberately
does not call `db.create_all()`.

## Run

Render uses this equivalent command automatically:

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 --access-logfile - run:app
```

The health check is `GET /api/health`. Use a managed process/container
platform for restarts, HTTPS termination, and secret injection.