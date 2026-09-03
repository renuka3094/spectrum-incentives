# Deploying Spectrum Incentives — a beginner's step-by-step guide

This walks you through getting a real, public link (like `https://spectrum-incentives.onrender.com`)
that your manager can open in any browser, on any device — no setup on their end at all.

There are two parts: first you put your project code on **GitHub** (a place to store code online),
then you connect that to **Render** (the service that actually runs your app and gives you a link).
Both are free for what you need here. Budget about 20–30 minutes the first time.

---

## Part 1 — Create your accounts (skip any you already have)

1. Go to **[github.com](https://github.com)** and click **Sign up**. Verify your email when it asks.
2. Go to **[render.com](https://render.com)** and click **Get Started**. When it asks how to sign up,
   choose **"Sign up with GitHub"** — this links the two accounts automatically, which saves you a
   step later. Approve the permission screen GitHub shows you.

---

## Part 2 — Put your project on GitHub

You'll use **GitHub Desktop** — a free app with buttons and windows, no typing commands.

1. Download it from **[desktop.github.com](https://desktop.github.com)** and install it.
2. Open GitHub Desktop and sign in with your GitHub account when it asks.
3. In the top-left menu, click **File → New repository...**
4. Fill in:
   - **Name:** `spectrum-incentives` (or anything you like — no spaces)
   - **Local path:** click **Choose...** and pick the *parent* folder that contains your
     `spectrum_project` folder (e.g. if your project is at
     `C:\Users\you\Desktop\spectrum_project`, choose `C:\Users\you\Desktop`)
   - Leave everything else as-is, and click **Create repository**.

   > **If GitHub Desktop says a repository already exists at that path or you get confused by the
   > folder picker:** it's simplest to instead choose **File → Add local repository...**, point it
   > straight at your `spectrum_project` folder, and when it says "This directory does not appear to
   > be a Git repository," click **create a repository** in that same dialog.

5. Back in the main GitHub Desktop window, you'll see a long list of changed files under
   **Changes** — this is normal, it's every file in your project the first time. You should
   **not** see a `venv` folder or a `db.sqlite3` file in that list — if you do, stop and let me know,
   since those shouldn't be uploaded (the project's `.gitignore` file is supposed to exclude them
   automatically).
6. At the bottom left, type a short summary like `Initial commit` in the **"Summary"** box, then
   click the blue **Commit to main** button.
7. Click **Publish repository** in the top bar. Make sure **"Keep this code private"** is checked
   (recommended — you can still share the *deployed link* with anyone, the private repo just means
   strangers can't browse your source code), then click **Publish repository** again to confirm.

Your code is now on GitHub. You can double check by going to **github.com**, clicking your profile
picture (top right) → **Your repositories**, and opening the one you just created.

---

## Part 3 — Deploy it on Render

1. Go to **[dashboard.render.com](https://dashboard.render.com)** and click **New +** (top right),
   then choose **Web Service**.
2. Under **"Build and deploy from a Git repository,"** click **Next**, then find and click
   **Connect** next to the repository you just published (e.g. `spectrum-incentives`). If you don't
   see it listed, click **Configure account** and grant Render access to that repository.
3. You'll land on a settings page. Fill it in like this:
   - **Name:** anything — this becomes part of your link, e.g. `spectrum-incentives` gives you
     `spectrum-incentives.onrender.com`
   - **Region:** pick whichever is closest to you or your manager
   - **Branch:** `main` (should already be selected)
   - **Root Directory:** leave blank
   - **Runtime:** should auto-detect as **Python 3** — if it shows something else, change it to Python
   - **Build Command:** replace whatever's there with exactly:
     ```
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py seed_data && python manage.py ensure_superuser
     ```
     (Yes, this is long — it's five commands chained with `&&`. This does everything needed to get
     the database fully set up automatically, on every single deploy, with no separate step
     afterward — see the note at the end of step 4 for why.)
   - **Start Command:** replace whatever's there with exactly:
     ```
     gunicorn spectrum.wsgi
     ```
   - **Instance Type:** choose **Free**
4. Scroll down to **Environment Variables** and click **Add Environment Variable** seven times to
   add all of these (exact names on the left, your own values on the right):

   | Key | Value |
   |---|---|
   | `DJANGO_SECRET_KEY` | click **Generate** if Render offers it, or type any long random text yourself (e.g. mash your keyboard for 40+ characters) |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | leave a placeholder like `temp.onrender.com` for now — **you'll fix this in step 6 below** once Render tells you your real address |
   | `PYTHON_VERSION` | `3.11.15` |
   | `DJANGO_SUPERUSER_USERNAME` | whatever you want your own admin login to be, e.g. `admin` |
   | `DJANGO_SUPERUSER_PASSWORD` | a password for that login |
   | `DJANGO_SUPERUSER_EMAIL` | optional — can leave the value blank |

   **Why the long build command:** Render's free tier puts the interactive **Shell** tab behind a
   paid plan, so there's no simple way to SSH in afterward and run one-time setup commands by hand.
   Chaining `migrate`, `seed_data`, and a custom `ensure_superuser` command onto the build instead
   means the database, demo accounts, and your own admin login are all ready the moment the very
   first deploy finishes — and it's completely safe to leave in place permanently: all three commands
   are written to do nothing on a second, third, or hundredth deploy once they've already run once.

5. Click **Create Web Service** at the bottom. Render will now build and start your app —
   watch the log output scroll by. The first deploy usually takes 2–5 minutes. It's done when the
   log shows something like `Your service is live 🎉` and the status dot at the top turns green.
6. **Now fix the allowed-hosts placeholder:** at the top of the page, copy the real URL Render
   assigned you (something like `https://spectrum-incentives-ab12.onrender.com`). Go to the
   **Environment** tab in the left sidebar, edit `DJANGO_ALLOWED_HOSTS`, and replace the placeholder
   with just the hostname part — e.g. `spectrum-incentives-ab12.onrender.com` (no `https://`, no
   trailing slash). Click **Save Changes** — Render will automatically redeploy with the fix.

---

## Part 4 — Share it

Nothing left to set up by hand — the database, demo accounts, and your admin login were all created
automatically as part of the build in Part 3. Open the URL from step 6 above in your own browser
first to make sure it loads the login page. Then just send that same link to your manager — `https://your-app-name.onrender.com`. They can open
it on their laptop, phone, whatever — nothing to install.

They can log in with any of the demo accounts (`agent1` / `spectrum123`, or `analyst1`, `director1`,
same password) to see all three portals, or with the admin login you just created to see the
Django admin at `/admin/`.

---

## Good to know

- **The free plan spins down when nobody's used it for a while**, and takes 30-60 seconds to wake
  back up on the next visit. If your manager opens the link and it looks stuck loading, that's why —
  just wait, it'll come up. There's no way to avoid this on the free tier.
- **The database resets on redeploys** (Render's free tier storage isn't permanent). Fine for
  showing off the UI; if you want data to actually stick around long-term, say so and we can add
  Render's free PostgreSQL database instead of SQLite.
- **The demo incentive can go stale.** If the dashboard ever shows "No active incentive," go to your
  service's **Manual Deploy** button (top right) and choose **Deploy latest commit** — this re-runs
  the whole build command, which includes `seed_data`, and generates a fresh incentive centered on
  today without touching your existing agents, sales, or history (no code change needed to trigger
  it). See the README for why this happens.
- **Updating the app later:** make your changes locally, then in GitHub Desktop you'll see them
  under **Changes** again — write a summary, **Commit to main**, then click **Push origin** at the
  top. Render notices the new commit and redeploys automatically within a minute or two.

## If something goes wrong

- **Build fails (red X, log shows an error):** scroll up in the build log to find the actual error
  line (usually near the top of the red text) and send it to me — I can tell you exactly what to fix.
- **"Application error" page after a successful build:** almost always means an environment variable
  is missing or wrong — double-check all seven from Part 3, step 4 are present under the
  **Environment** tab.
- **Login page loads but looks unstyled (no colors, plain text):** means `collectstatic` didn't run —
  double check your Build Command exactly matches step 3 above, including the
  `&& python manage.py collectstatic --noinput` part.
