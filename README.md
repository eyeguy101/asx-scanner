# ASX Momentum & Relative Strength Scanner (Cloud Deployment)

Deploy your private ASX momentum scanner in under 2 minutes for free on **Streamlit Community Cloud** or **Hugging Face Spaces**.

---

## Method 1: Streamlit Community Cloud (Recommended — Free Permanent URL)

1. Go to [GitHub.com](https://github.com/) and create a new repository (e.g., `asx-scanner`).
   - You can set it to **Public** or **Private**.
2. Click **"Upload files"** in GitHub, and drag-and-drop:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - Click **Commit changes**.
3. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
4. Click **"New app"**:
   - Repository: `your-username/asx-scanner`
   - Branch: `main`
   - Main file path: `app.py`
   - Click **Deploy!**

In ~60 seconds, Streamlit deploys your app and gives you a private web link (e.g. `https://your-asx-scanner.streamlit.app`) that pulls live ASX data directly from Yahoo Finance on cloud servers with zero browser proxy errors.

---

## Method 2: Hugging Face Spaces (No GitHub / Drag-and-Drop)

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and create a free account.
2. Click **"Create new Space"**:
   - Space name: `asx-scanner`
   - Space SDK: **Streamlit** (Free)
3. Upload `app.py` and `requirements.txt`.
4. Click **Commit** — it will build and launch your live URL instantly.
