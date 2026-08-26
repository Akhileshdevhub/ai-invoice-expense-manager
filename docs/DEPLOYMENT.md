# Deployment Guide

This documents how to deploy the app, and the production considerations
that come with the current architecture. **No live deployment has been
made for this project** — this is a guide for doing it, not a claim that
it's already hosted somewhere. See the note at the bottom for why.

## Streamlit Community Cloud (recommended for this project)

Streamlit Community Cloud is the natural fit: it's free, it deploys
directly from a GitHub repo, and it runs Streamlit apps with no other
infrastructure to manage.

1. Push this repository to GitHub (public or private).
2. Add a `packages.txt` file at the repo root listing system packages
   Streamlit Cloud should install via `apt` before your app starts:
   ```
   tesseract-ocr
   poppler-utils
   ```
3. Go to [share.streamlit.io](https://share.streamlit.io), sign in, and
   click "New app." Point it at this repo, branch `main`, and file path
   `main.py`.
4. Under **Advanced settings -> Secrets**, add (only if you want the
   optional LLM layer active):
   ```toml
   OPENAI_API_KEY = "sk-..."
   OPENAI_MODEL = "gpt-4o-mini"
   ```
   Leave this blank to run without it — the app works fully either way
   (see `docs/LLM_ARCHITECTURE.md`).
5. Deploy. Streamlit Cloud installs `requirements.txt` and the
   `packages.txt` system packages automatically.

## Docker (self-hosted / any container platform)

A `Dockerfile` is included at the repo root. Build and run:

```bash
docker build -t ai-invoice-expense-manager .
docker run -p 8501:8501 --env-file .env ai-invoice-expense-manager
```

This is the more portable option if deploying to Render, Railway, Fly.io,
or a plain VM rather than Streamlit Community Cloud specifically.

**Verification status**: the `Dockerfile` follows the standard pattern
for a Streamlit app needing system-level OCR dependencies (see
`docs/OCR_PIPELINE.md`), but `docker build` could not be run to
completion in the development sandbox — its network egress blocked pulls
from Docker Hub (`registry-1.docker.io`). The app itself was run and
verified directly with `streamlit run main.py` (see the screenshots in
this repo, all captured from a real running instance). Run
`docker build -t ai-invoice-expense-manager .` yourself before relying on
the image; if anything about the base image or apt packages needs
adjusting, it'll surface immediately.

## Secrets configuration

Never commit `.env` — it's gitignored. Configure `OPENAI_API_KEY` (and
`OPENAI_MODEL`, `DATABASE_PATH` if needed) through the hosting platform's
secrets mechanism (Streamlit Cloud's Secrets panel, Docker's `--env-file`
or `-e` flags, or the platform's environment-variable settings).

## Production considerations (read before actually relying on this)

- **SQLite + Streamlit Community Cloud's filesystem is ephemeral.** Free-
  tier containers can restart and lose local disk state. For any
  deployment where data needs to persist, either (a) accept that this is
  a demo deployment and data may reset, or (b) point `DATABASE_PATH` at a
  mounted persistent volume (Docker on a VM, or a platform that offers
  one), or (c) swap SQLite for a hosted Postgres instance — the
  `app/database/` layer would need its raw SQL adapted, but the
  repository function signatures wouldn't need to change.
- **SQLite is single-writer.** Fine for one user clicking through the
  app. Not appropriate for concurrent multi-user write traffic — see
  `docs/LIMITATIONS.md`.
- **No authentication.** Anyone with the URL can use the app and see
  whatever's in the database. Don't deploy with real financial data
  behind a public URL without adding auth first.
- **Tesseract must be present on the host.** This is the most common
  deployment failure for this kind of app — `pytesseract` is a Python
  wrapper, not an installation of Tesseract itself. Confirm
  `tesseract --version` works in the deployment environment before
  troubleshooting anything else.

## Why this project isn't deployed to a public URL

This project is meant to be run and inspected locally (or self-hosted)
by whoever is evaluating it — cloning the repo, running the seed
scripts, and using the app with the included synthetic sample data. A
public demo deployment with no authentication would mean anyone could
upload files to it; that wasn't worth doing for a portfolio
demonstration when running it locally takes under five minutes (see
README "Running Locally").
