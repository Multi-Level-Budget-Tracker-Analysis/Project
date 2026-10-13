# Deployment & Git Guide
### Multi-Level Budget Tracker Analytics

This project is configured and prepared for:
1. **GitHub Repository Sync** (Complete local repository already initialized and committed on `main`).
2. **Vercel Serverless Deployment** (`vercel.json`, `api/index.py`, `/tmp` SQLite persistence fallback, and root `requirements.txt` are configured).

---

## 🐙 Step 1: Push to GitHub

1. Open your browser and go to: **[github.com/new](https://github.com/new)**
2. Create a new repository:
   - **Repository name**: `multi-level-budget-analytics` (or any name you prefer)
   - Set to **Public** or **Private**
   - **Do NOT** check "Add a README file", ".gitignore", or "license" (we already have them committed).
   - Click **"Create repository"**.
3. In your terminal (PowerShell or Command Prompt) in `D:\Multi level budget`, run:
   ```bash
   git remote add origin https://github.com/RohithSV2/<YOUR-REPOSITORY-NAME>.git
   git branch -M main
   git push -u origin main
   ```
   *(Replace `<YOUR-REPOSITORY-NAME>` with the repository name you created, e.g. `multi-level-budget-analytics`)*

---

## ⚡ Step 2: Deploy to Vercel

### Method A: One-Click GitHub Import (Recommended)
1. Go to **[vercel.com](https://vercel.com)** and log in with your GitHub account.
2. Click **"Add New..." → "Project"**.
3. Find your repository `multi-level-budget-analytics` in the list and click **"Import"**.
4. Leave all default settings as they are:
   - Framework Preset: **Other**
   - Root Directory: `./`
   - Vercel automatically reads `vercel.json` and runs `api/index.py` with `@vercel/python`.
5. Click **"Deploy"**.
6. Within 60 seconds, your application will be live at:
   `https://multi-level-budget-analytics.vercel.app` (or your assigned Vercel domain).

---

### Method B: Deploy Directly from Command Line (Vercel CLI)
If you prefer deploying directly from your terminal:
1. Open PowerShell in `D:\Multi level budget` and run:
   ```bash
   npx vercel login
   ```
   *(Select "Continue with GitHub" or your email in the browser)*
2. Once logged in, deploy to production:
   ```bash
   npx vercel --prod
   ```
3. When prompted:
   - **Set up and deploy?**: `Y`
   - **Which scope?**: Press `Enter` (your account)
   - **Link to existing project?**: `N`
   - **What's your project's name?**: Press `Enter` (or type a name)
   - **In which directory is your code located?**: Press `Enter` (`./`)
4. Vercel will build and output your live production URL!

---

## 🛠️ How Vercel Configuration Works
- **`vercel.json`**: Directs all web requests to `api/index.py` using `@vercel/python`.
- **`api/index.py`**: Serverless entry point exposing the Flask WSGI instance.
- **Serverless SQLite Handling**: Vercel has a read-only filesystem except for `/tmp`. The application's `backend/database.py` automatically detects Vercel and copies `budget_tracker.db` to `/tmp/budget_tracker.db` so all user input actions (adding transactions, updating budgets, adding enterprise orders) execute smoothly without read-only filesystem errors!
