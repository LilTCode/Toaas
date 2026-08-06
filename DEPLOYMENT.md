# Deploying TO-AAS to Vercel

The backend and frontend deploy as **two separate Vercel projects** from this one
repository. Do the backend first, because the frontend needs the backend's URL.

## Why the backend was failing

Vercel functions are serverless: no persistent disk, no local MySQL, and a
read-only filesystem apart from `/tmp`. The original setup broke on all three,
plus a `package-lock.json` in `backend/` that made Vercel treat the folder as a
Node project instead of Python. What changed is listed at the bottom.

---

## Prerequisites

- The repo pushed to GitHub.
- A Vercel account.
- Your OpenAI API key and Gmail app password to hand.

---

## Part 1 — Backend

### 1.1 Create the project

1. Vercel dashboard → **Add New** → **Project** → import this repository.
2. **Root Directory**: click *Edit* and select `backend`. This is the single most
   important setting; without it Vercel looks at the repo root and finds nothing
   to run.
3. **Framework Preset**: leave as *Other*. Vercel detects Django from
   `requirements.txt` + `manage.py`.
4. Do **not** deploy yet — click *Environment Variables* first, or cancel the
   build and add them next. A build without `DJANGO_SECRET_KEY` fails on purpose.

### 1.2 Add the database (Neon Postgres)

Serverless functions cannot reach a MySQL server on your laptop, and Vercel does
not host MySQL. Use Postgres:

1. Project → **Storage** tab → **Create Database** → **Neon (Postgres)**.
2. Pick the region closest to you, create it, and connect it to this project.
3. Neon injects `DATABASE_URL` automatically. Nothing to copy by hand.

`settings.py` reads `DATABASE_URL` when present and falls back to your local
MySQL variables when it is absent, so local development is unaffected.

### 1.3 Add the file store (Vercel Blob)

Profile photo uploads need somewhere to live, since the function filesystem is
read-only and wiped between invocations.

1. Project → **Storage** → **Create Database** → **Blob**.
2. Connect it to the project. It injects `BLOB_READ_WRITE_TOKEN`.

The presence of that token is what switches `DEFAULT_FILE_STORAGE` to
`VercelBlobStorage`. With no token, uploads use the local filesystem as before.

### 1.4 Set the environment variables

Project → **Settings** → **Environment Variables**. Apply each to *Production*,
*Preview*, and *Development*.

| Variable | Value |
| --- | --- |
| `DJANGO_SECRET_KEY` | a fresh 50+ char random string (see below) |
| `DJANGO_DEBUG` | `False` |
| `AI_API_KEY` | your OpenAI key |
| `AI_API_URL` | `https://api.openai.com/v1/responses` |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | `smtp.gmail.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_HOST_USER` | your sending address |
| `EMAIL_HOST_PASSWORD` | Gmail **app password**, not your login password |
| `EMAIL_USE_TLS` | `True` |
| `DEFAULT_FROM_EMAIL` | `TO-AAS <your_address@example.com>` |

Generate the secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

`DATABASE_URL` and `BLOB_READ_WRITE_TOKEN` are already there from steps 1.2/1.3.
Leave `CORS_ALLOWED_ORIGINS` for step 3.1 — you need the frontend URL first.

### 1.5 Deploy

Click **Deploy**. Note the resulting URL, e.g.
`https://toaas-backend.vercel.app`. Vercel runs `collectstatic` automatically;
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` pick up the deployment hostname from
Vercel's own `VERCEL_URL` / `VERCEL_PROJECT_PRODUCTION_URL`, so you do not have
to hardcode it.

### 1.6 Run the migrations

The database is empty at this point. Migrations are run from your machine
against Neon rather than during the build — a failed migration mid-build would
otherwise leave the schema half-applied with no way to inspect it.

1. Vercel → **Storage** → your Neon database → copy the connection string.
2. From `backend/`:

```bash
# PowerShell
$env:DATABASE_URL="postgres://...paste...?sslmode=require"
$env:DJANGO_SECRET_KEY="anything-for-local-cli-use"
$env:DJANGO_DEBUG="False"
../.venv/Scripts/python.exe manage.py migrate
../.venv/Scripts/python.exe manage.py createsuperuser
```

```bash
# bash
export DATABASE_URL="postgres://...paste...?sslmode=require"
export DJANGO_SECRET_KEY="anything-for-local-cli-use"
export DJANGO_DEBUG="False"
python manage.py migrate
python manage.py createsuperuser
```

Re-run `migrate` the same way whenever you add migrations later.

### 1.7 Check it

Visit `https://your-backend.vercel.app/admin/` and log in with the superuser you
just created. If the CSS is missing, `collectstatic` did not run — check the
build log. `/api/` endpoints should respond to requests.

---

## Part 2 — Frontend

1. **Add New** → **Project** → import the *same* repository again.
2. **Root Directory**: `frontend`.
3. **Framework Preset**: Vite (auto-detected).
4. Environment variable:

   | Variable | Value |
   | --- | --- |
   | `VITE_API_BASE_URL` | `https://your-backend.vercel.app/api/` |

   The trailing `/api/` and its slash both matter — the frontend joins paths
   onto this string directly.
5. Deploy. Note the URL, e.g. `https://toaas.vercel.app`.

Vite inlines `VITE_*` variables at build time, so changing this value later
requires a redeploy, not just a restart.

---

## Part 3 — Connect the two

### 3.1 Allow the frontend to call the backend

Go back to the **backend** project → Environment Variables → add:

| Variable | Value |
| --- | --- |
| `CORS_ALLOWED_ORIGINS` | `https://toaas.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://toaas.vercel.app` |

Use your real frontend URL, with no trailing slash. Comma-separate if you have
more than one origin. Then **redeploy the backend** — environment variable
changes do not apply to existing deployments.

### 3.2 Verify end to end

1. Open the frontend URL.
2. Register an account, then log in.
3. Upload a profile photo. Its URL should be on
   `*.public.blob.vercel-storage.com`, which confirms Blob storage is wired up.
4. Exercise one AI-backed endpoint to confirm `AI_API_KEY` works.

---

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `DJANGO_SECRET_KEY must be set…` | Add it in the backend project env vars, then redeploy. |
| `DisallowedHost` | Add the hostname to `DJANGO_ALLOWED_HOSTS`. |
| CORS error in the browser console | `CORS_ALLOWED_ORIGINS` missing the frontend origin, has a trailing slash, or the backend was not redeployed after the change. |
| `500` on every request | Vercel → Deployment → **Runtime Logs** shows the traceback. Usually a missing env var. |
| Admin login says "CSRF verification failed" | Add the backend's own URL to `CSRF_TRUSTED_ORIGINS`. |
| Frontend calls `localhost:8000` | `VITE_API_BASE_URL` was not set at build time. Set it and redeploy. |
| `No module named 'MySQLdb'` | `DATABASE_URL` is not set, so Django fell back to MySQL. Attach Neon. |
| Uploads vanish after a while | `BLOB_READ_WRITE_TOKEN` missing — writes went to the ephemeral filesystem. |
| Build installs npm packages in `backend/` | A `package.json`/`package-lock.json` reappeared under `backend/`. Remove it. |
| 404 on a frontend route after refresh | The SPA rewrite in `frontend/vercel.json` was removed. |

---

## What changed in the backend

- **`requirements.txt`** — pinned every version; added the missing
  `django-cors-headers` (it was in `INSTALLED_APPS` but never installed, which
  crashed the function on import), plus `psycopg[binary]` for Postgres and
  `vercel_blob` for uploads.
- **`backend/package-lock.json`** — deleted. Its presence made Vercel treat
  `backend/` as a Node project.
- **`backend/backend/settings.py`** — `DATABASE_URL` support with MySQL
  fallback; Blob storage when the token is present; hostnames and CSRF origins
  derived from Vercel's env; HTTPS cookie/HSTS settings when `DEBUG=False`; a
  hard failure if the secret key is missing in production; `.env` is ignored on
  Vercel so a stray file cannot override the dashboard.
- **`backend/backend/storage_backends.py`** — new. Django `Storage`
  implementation over the Vercel Blob API.
- **`backend/backend/__init__.py`** — the `pymysql` shim is now guarded, so the
  function no longer crashes when PyMySQL is absent under Postgres.
- **`backend/vercel.json`** — dropped the `buildCommand` that was overriding
  Vercel's automatic `collectstatic`; raised the function timeout for AI calls;
  excluded tests and media from the bundle.
- **`backend/.python-version`** — pins Python 3.12.
- **`apps/accounts/models.py`** — `profile_photo` widened to 500 chars, since
  Blob returns a full URL rather than a relative path. Migration `0005` included.

`backend/media/` still holds three committed demo photos. They are excluded from
the deployed bundle and are not served in production; new uploads go to Blob.
Delete them from git when you no longer need them locally.
