# Pushing to GitHub

The project has a local git repository with 15 staged commits already
created (`git log --oneline` to see them). Nothing has been pushed
anywhere — that step needs your own GitHub account.

## 1. Create the repository on GitHub

Go to https://github.com/new and create a repository:

- **Name**: `ai-invoice-expense-manager`
- **Description**: `AI-assisted receipt processing and expense analytics using OCR, NLP, ML, and optional LLM features.`
- **Visibility**: Public (recommended, so it's visible on your portfolio/resume)
- **Do NOT** initialize with a README, .gitignore, or license — this repo already has all three, and GitHub will reject the push if the histories conflict.

## 2. Push this repo

From inside the project folder:

```bash
git remote add origin https://github.com/<your-username>/ai-invoice-expense-manager.git
git branch -M main
git push -u origin main
```

If you use SSH instead of HTTPS:

```bash
git remote add origin git@github.com:<your-username>/ai-invoice-expense-manager.git
git branch -M main
git push -u origin main
```

## 3. Verify

- Open the repo on GitHub and confirm: `README.md` renders with the
  screenshots visible, `docs/` and `screenshots/` folders are present,
  `.env` is NOT in the file list (only `.env.example` should be), and
  `data/app.db` is NOT in the file list.
- Check the commit history matches what you see locally
  (`git log --oneline`) — 15 commits, not one giant "initial commit."

## 4. Optional: add topics on GitHub

For discoverability on your profile: `python`, `streamlit`, `ocr`,
`machine-learning`, `nlp`, `tesseract`, `scikit-learn`, `portfolio-project`.
