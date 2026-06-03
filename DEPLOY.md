# Publish Chronicle (free, permanent link)

This puts Chronicle on the internet at a link like `https://chronicle-xxxx.onrender.com`
that works even when your Mac is off. ~10 minutes, no coding.

Your secret API keys are **never** put on GitHub (they're git-ignored). You paste
them straight into the host, which keeps them private.

---

## Step 1 — Put the code on GitHub (one time)

1. Make a free account at **https://github.com** (if you don't have one).
2. Click **New repository** → name it `chronicle` → keep it **Private** → **Create repository**.
3. GitHub shows a page with commands. In the **Terminal**, from this folder, run the
   lines GitHub gives you under *"…or push an existing repository"*. They look like:

   ```sh
   git remote add origin https://github.com/YOUR-NAME/chronicle.git
   git branch -M main
   git push -u origin main
   ```

   When it asks you to sign in, do so in the browser window that opens.

(Your `api-key.txt` and `gemini-key.txt` are ignored by git, so they stay on your Mac only.)

---

## Step 2 — Deploy on Render (free)

1. Make a free account at **https://render.com** and choose **Sign in with GitHub**.
2. Click **New +**  ▸  **Blueprint**.
3. Pick your **chronicle** repo. Render reads `render.yaml` and sets everything up.
4. It will ask you for two **environment variables** — paste your keys:
   - `ANTHROPIC_API_KEY`  → your Anthropic key (starts with `sk-`)
   - `GEMINI_API_KEY`     → your Gemini key
5. Click **Apply / Create**. Wait ~2–4 minutes for it to build and go live.
6. Your public link appears at the top, e.g. `https://chronicle-xxxx.onrender.com`. **That's the link to share.** 🎉

On the live site, the **📱 Open on phone** button shows a QR of that public link —
anyone can scan it (no same-Wi-Fi needed anymore).

---

## Good to know

- **First visit after a quiet spell is slow.** The free plan "sleeps" after ~15 min idle,
  so the first load takes ~30–60s to wake up, then it's fast.
- **Your bill is protected.** The app caps AI requests (≈20/min per visitor, ≈80/min total)
  and caches answers, so a busy day won't surprise you. You can tune `RATE_PER_IP` /
  `RATE_GLOBAL` env vars on Render.
- **Turn it off / on:** in Render, **Suspend** the service to pause it (and stop any costs),
  **Resume** to bring it back.
- **Update the live site later:** just `git push` — Render redeploys automatically.
- **Worried about cost?** Remove the two API keys in Render → the site still runs in
  "demo mode" (sample text + live images) for free.
