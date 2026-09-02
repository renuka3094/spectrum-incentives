# Spectrum Incentives — Field Agent Portal

A Django-only, no-JS-framework incentive platform for Spectrum Communications field agents. This is phase 1 of the Spectrum project: the **agent-facing dashboard**, with real (if intentionally minimal) logins for Incentive Analyst and Director accounts too — see "Three login types" below.

## What's in this phase

A field agent logs in and sees:

- **This month's incentive** and how many days are left in it.
- **A tier ring** (Silver → Gold → Diamond) showing points earned and points needed for the next tier, hand-drawn on `<canvas>` with an animated fill.
- **Per-product goals** — how many units of each featured product/service they still need to sell this period, with live progress bars.
- **AI Insights** — a rule-based "AI assistant" (no external API, no API key, works offline) that:
  - looks at what agents *near them* (same region) are selling this period and flags products they're under-selling relative to peers ("nearby scenarios"),
  - calculates the single fastest product to close the gap to their next tier,
  - reports week-over-week momentum (trending up/down).
- **A "Log a sale" flow, reviewed before it counts** — a modal with a product picker and quantity stepper posts to the server via `fetch()`. A sale you log yourself does **not** instantly move your points, tier, or goals anymore — it's saved as "Pending review" and only counts once an admin approves it (Django admin → Sales → select rows → "Approve selected sales"). See "Why a logged sale doesn't count instantly" below for the reasoning. A running **daily cap** (15 units/day by default, `DAILY_LOG_QUANTITY_CAP` in `insights.py`) limits how many attempts one agent can submit in a day, and the modal shows a live "Your recent submissions" list — product, points, and status (Pending/Approved/Rejected) — right there, no extra scrolling required.
- **A points-over-time chart** comparing this incentive to past ones (also hand-drawn on canvas — no charting library).
- **A real confetti burst + synthesized level-up sound** — when a sale pushes you into a new tier, a hand-rolled particle system fires on canvas and a short triumphant chime plays (generated live with the Web Audio API — no audio file, no network dependency). There's a mute toggle (🔊/🔇) in the header if the sound gets old.
- **A light/dark theme toggle** in the header — the whole palette (including the canvas charts, which redraw themselves) flips between a near-black look and a clean white one. Your choice is remembered per-browser.
- **A tabbed dashboard** — Overview / Goals / Tasks / Achievements / Rewards / Leaderboard, switched instantly with vanilla JS (no reload). Each gets real room to breathe instead of being crammed into one scroll.
- **Available Tasks** — a lighter-weight checklist that sits *alongside* the big per-product Goals: six bite-sized bonus quests like "log a sale within 3 days," "sell in 2 different categories," or "log 2 sales in one day," each worth a small bonus point payout. Quests reset every incentive period (unlike badges, which are permanent), completing one pops the same toast/celebration flow as everything else, and the Tasks tab shows a live done/total count plus how many bonus points you've banked this period.
- **Reward Catalog** — a new tab that finally surfaces `Tier.perk_description` (it was already in the database, just never rendered anywhere): Silver/Gold/Diamond each shown with their actual perk text ("10% bonus commission + swag box," etc.), your already-unlocked tiers highlighted in green and your next tier called out in the accent color, so "what do I actually get" has a real answer.
- **A slim, single-line stat strip on Overview** — the countdown, pace, lifetime points, units-left-to-sell, and total-cash-earned numbers used to be five separate cards stacked in a grid; they're now compact chips in one row (hover a chip to see what it means), freeing up a full screen's worth of scrolling before you get to the tier ring and AI insights.
- **A soft, slow-drifting ambient background** — three large, blurred color blobs behind the whole app, gently animating on a 20–30 second loop. Purely decorative, sits behind every card, never gets in the way of reading anything, and turns off automatically if the browser's reduced-motion setting is on.
- **Hover micro-interactions** — goal cards, task cards, badges, reward tiles, and leaderboard rows all lift and pick up a soft glow on hover instead of sitting completely static; the tier-progress hero card goes a step further with a subtle 3D tilt that follows your cursor.
- **A surprise mystery box** — the first time you complete a product goal in an incentive period (counting only *approved* sales), instead of just a toast, a gift box pops up center-screen, shakes, and bursts open (with confetti and its own little chime) to reveal a random bonus (10–25 points). It only ever fires once per goal per incentive — and since it's checked fresh on every page load, not just right after a sale, it still fires the moment you open the app after an admin approves the sale that tipped a goal over, even if that happened while you were away.
- **A total cash earned stat** — a third headline tile next to lifetime points, converting your all-time points into an estimated dollar payout at a fixed placeholder rate (`CASH_PER_POINT` in `insights.py`, currently $0.75/point — swap it for your real commission structure whenever you have one, or replace it with a true per-sale dollar model).
- **A live company-wide activity ticker** — a scrolling marquee under the header showing recent sales and badge unlocks from agents across the whole company, not just your region ("🚀 Jordan Ramirez sold 2x Fiber Gig", "🏅 Alex Chen unlocked Team MVP"). It polls quietly in the background every 25 seconds so it keeps feeling live, and pauses on hover so you can actually read an item.
- **A little more motion, kept subtle** — the "Log a sale" button now has a slow breathing glow to draw the eye toward the core action; badge, reward, tier, and quest emoji gently bob instead of sitting frozen; and goal progress bars get a soft light-sweep shimmer across their filled portion. All of it (plus the ambient background and hover effects from the round before) respects the browser's reduced-motion setting and turns itself off automatically.
- **A 9-badge achievement shelf** (First Blood, Fast Starter, Category Crusher, Century Club, Consistency Star, Team MVP, Diamond Elite, Streak Starter, Streak Legend) — locked badges are dim/greyscale, unlocked ones glow in the accent color. Unlocking one mid-session (e.g. right after logging a sale) pops a toast and lights the badge up live.
- **A daily login streak** — separate from the sales streak, this rewards just showing up: a 🔥 flame + day count sits next to your name, ticks up each consecutive day you log in, and resets if you skip a day. It's what powers the Streak Starter/Legend badges.
- **A pre-login teaser** on the sign-in screen — aggregate, anonymous stats about the *current* incentive ("342 sales logged by the team this week," "12 agents already leveled up," the hottest-selling product right now) so the app is selling you on logging in before you even type a password.
- **A Leaderboard tab** — ranked standings for the current incentive, toggled between "My region" and "Company-wide," medal emoji for the top 3, your own row highlighted. Agents with zero sales still show up (ranked last) — seeing you're not even on the board is its own nudge to go log one.
- **A live countdown clock** on the Overview tab, ticking down to the second toward the incentive's end date — real urgency, not a static date.
- **A "you're ahead of pace" banner** comparing your points so far this incentive to where you stood at the same number of days into the *previous* one — a small, honest, data-driven nudge either way.
- **Shareable achievement cards** — click "🔗 Share" on any unlocked badge and it renders a slick gradient trophy card on canvas (your name, the badge, the date) with a one-click PNG download — a screenshot-able flex moment, no design tool required.
- **Animated number count-ups** — points, the pace %, goal counts, and leaderboard scores count up smoothly instead of snapping to a new value, on page load and after logging a sale.
- **A queued toast system** — a level-up and one or more badge unlocks can all fire from the same action; they now show one at a time cleanly instead of overlapping.
- **A pick-your-own avatar** — click your name in the header to choose from a small emoji gallery; it saves instantly and updates everywhere your avatar shows.
- **A compact header on scroll** — the nav bar shrinks slightly once you scroll down, saving space without losing navigation.
- **A brief animated splash** the first time the app loads each browser session — the mark pops in, the wordmark fades up, then it gets out of the way.

Everything interactive is plain `fetch()` + vanilla JS + `<canvas>` + the Web Audio API. No React/Angular/Vue, no HTMX, no jQuery, no chart or confetti libraries — just Django templates, CSS, and hand-written JavaScript, per the assignment rules.

### Design language

Mostly monochrome (near-black/blue-black surfaces, off-white text in dark mode; near-white surfaces, near-black text in light mode) with exactly **one accent color** — a blue in the family of Charter/Spectrum's real brand blue (Spectrum is a real Charter Communications brand, so the palette leans into that rather than an arbitrary color; the exact hex is a close approximation from third-party brand-color trackers since Charter's official guidelines aren't public — swap `--accent` in `style.css` for the real value if you get access to their internal style guide) — used for actions and progress in both themes. Tier badges borrow silver/gold tones as a literal nod to the tier names, not as decoration — the same restraint that governs the confetti palette, which is deliberately kept to the app's existing tokens (accent, gold, silver, success) rather than a rainbow. Headlines use Space Grotesk, body text uses Inter — clean and a little GenZ without being loud.

### Why rule-based "AI" instead of a real model call

You said you only know Python and want this to run without extra cost or an API key — so the "AI" is transparent, explainable Python logic over the sales data already in the database (`agent_portal/insights.py`). It's easy to swap later: every function in that file returns plain data, so a future version could replace the internals with a real LLM call without touching any template or view.

### Why a logged sale doesn't count instantly

`+ Log a sale` exists because this phase-1 demo has no real order/CRM/billing system behind it — in an actual Spectrum deployment, "a sale happened" would be an event that arrives automatically from that real backend, not something an agent types in. Since there's nothing to integrate with here, the button stands in for that event so you (and anyone you demo this to) can see the whole loop — sale → points → tier → badges/quests/mystery box — live.

But a self-reported number that feeds real rewards, with zero verification, is trivially gameable — an agent could just keep clicking and inflate their own numbers forever. So a logged sale now starts as **"Pending review"** (`Sale.status`) and doesn't move a single point, tier, goal, badge, or quest until an admin approves it (Django admin → Sales → select rows → **Approve selected sales** / **Reject selected sales** — a stand-in for the Director-approval phase already on the roadmap). Two more guardrails on top of that: a **daily logging cap** (`DAILY_LOG_QUANTITY_CAP` in `insights.py`, 15 units/day by default) limits how many attempts one agent can submit regardless of outcome, and every submission — pending, approved, or rejected — is visible to the agent themselves in the "Your recent submissions" list right in the log-sale modal, so nothing about their own numbers is hidden from them.

One consequence worth knowing: because sales no longer count the instant they're logged, the celebratory stuff (confetti, level-up toast, badge/quest unlocks, the mystery box) no longer fires on the log-sale click either — it fires on the *next dashboard load* after whatever tipped it over actually gets approved, since that's the first moment the app can honestly say it happened. `agent_portal/views.py`'s `dashboard()` re-syncs achievements/quests/goal-bonuses on every visit for exactly this reason.

---

## Project structure

```
spectrum_project/
├── manage.py
├── requirements.txt
├── Procfile                  # for gunicorn on a host like Render
├── spectrum/                 # Django project (settings, urls)
├── agent_portal/             # the one app for this phase
│   ├── models.py             # Region, Tier, Category, Product, Incentive,
│   │                         # IncentiveTierRule, IncentiveProductGoal, AgentProfile, Sale (now
│   │                         # with a pending/approved/rejected status), AgentAchievement,
│   │                         # AgentTaskCompletion, AgentGoalBonus
│   ├── insights.py           # the rule-based "AI" engine + analyst/director overview queries
│   ├── roles.py              # role lookup (Agent/Analyst/Director), the role_required decorator,
│   │                         # and post-login redirect-to-own-portal logic
│   ├── context_processors.py # topbar avatar/role fallback for non-Agent accounts
│   ├── views.py              # dashboard + analyst/director views + 4 JSON endpoints
│   ├── urls.py
│   ├── admin.py              # manage incentives/products/agents via /admin/
│   └── management/commands/seed_data.py   # generates demo data (agents + analyst1/director1)
├── templates/                # base.html, login, dashboard, analyst/director dashboards + partials
└── static/agent_portal/      # style.css, dashboard.js, login.js
```

## How the data model maps to your requirements

| Your requirement | Model / mechanism |
|---|---|
| Incentives vary every month | `Incentive` is a monthly campaign row; `IncentiveTierRule` and `IncentiveProductGoal` are *per incentive*, so thresholds and featured products can differ month to month |
| Silver → Gold → Diamond goal | `Tier` + `IncentiveTierRule.points_required`, computed live in `insights.tier_progress()` |
| "How many products/services need to be sold" | `IncentiveProductGoal.target_quantity` per product, tracked against `Sale` rows |
| Nearby buying scenarios | `insights.nearby_trending()` groups `Sale` rows by the agent's `Region` |
| Analyst sets incentives / Director approves | Real logins exist for both roles now (see "Three login types" below); the actual incentive-editing and sale-approval *screens* still route to the Django admin — the models and access control are fully built, the bespoke UI for them is the next round |

---

## Three login types

The login page now has **Agent / Analyst / Director** tabs. They're purely presentational — which tab is highlighted has no bearing on what account you actually log in with, since routing is driven by the real account (see below), not the tab. That's deliberate: a visual tab is easy to click by mistake, so it can't be the thing that decides what a person can see.

Role is determined server-side in `agent_portal/roles.py`, not by a new field on the user model:

- **Agent** — has an `AgentProfile` row (the phase-1 dashboard already built).
- **Incentive Analyst** — belongs to the `Incentive Analyst` Django group.
- **Director** — belongs to the `Director` Django group (or is a superuser).

`seed_data` creates one demo login for each new role: **analyst1** and **director1**, both password **spectrum123**, alongside the existing `agent1`–`agent6`. After logging in, each account is sent straight to its own landing page (`get_success_url()` on the login view looks up the account's real role, never the tab that was clicked) — and if a logged-in account ever hits a URL that isn't theirs, they're quietly redirected to the one that is, rather than shown an error page. A Director can also open the Analyst view (a director should be able to see program-level health too); an Analyst can't open the Director view.

What Analyst and Director get right now is intentionally minimal — a real, server-rendered overview page each, built from live queries (`agent_portal/insights.py`'s `analyst_overview()` and `director_overview()`), not mocked data:

- **Analyst** (`/analyst/`) — agent count, points and units sold this period, points broken down by region, and the top-selling product. A note points at the Django admin for actually creating/editing incentives — that bespoke editor is the next round of work, not this one.
- **Director** (`/director/`) — agent count, team points, a pending-sales queue (with a link straight to the admin's pre-filtered "pending" filter), and a top-5 leaderboard. Approving/rejecting sales still happens in the Sale admin's bulk actions.

To promote a real user to one of these roles yourself, add them to the matching group from `/admin/auth/user/` (or `/admin/auth/group/`) — no code change needed.

---

## Run it locally (step by step)

You already have the project folder. From inside it:

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database tables
python manage.py migrate

# 4. Load demo data (agents, regions, products, this month's + 2 past incentives, sales history)
python manage.py seed_data

# 5. (optional) Create yourself an admin login to manage incentives/products
python manage.py createsuperuser

# 6. Run it
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Log in with any seeded agent: **agent1** through **agent6**, password **spectrum123** — or with **analyst1** / **director1**, same password, to see the two new role portals (see "Three login types" above). Try the "Log a sale" button — watch the ring and goal bars animate — and hit "Refresh" on the AI Insights card.

**Updating an existing checkout to this version:** run `python manage.py migrate` (adds nothing new to the schema this round — role is groups, not a model field) then `python manage.py seed_data` again to pick up the two new demo logins and the `Incentive Analyst`/`Director` groups; it's additive and safe to re-run (`get_or_create`), so nothing you've already got is touched.

**About CSS/JS changes not showing up:** this was a real bug in earlier versions of this project (fixed in two parts — the dev server no longer serves a stale snapshot of static files, and every stylesheet/script link now carries a version tag tied to the file's own last-modified time, so a browser can't keep reusing an old cached copy). With the current code you shouldn't need to do anything special — just refresh the page normally. If you have a `staticfiles/` folder sitting in the project root from an old checkout, it's safe (and a good idea) to delete it; it's dead weight left over from a one-time `collectstatic` run and isn't used by local dev at all anymore. `collectstatic` itself is only ever needed for the Render deploy step below, never for running locally.

Visit `http://127.0.0.1:8000/admin/` with your superuser login to add/edit incentives, tier thresholds, product goals, and regions — the Analyst and Director portals link straight into this admin for the editing/approval actions that don't have a bespoke screen yet (see "Three login types" above).

Re-running `python manage.py seed_data` is safe (it uses `get_or_create`); add `--flush` first if you want to wipe and regenerate everything from scratch.

**Heads-up — the demo incentives are date-relative, not fixed:** `seed_data` generates "this month + the 2 months before it" as of the moment you run it, and the dashboard only shows an incentive whose date range covers *today*. That means a database seeded in August will show empty "No active incentive" states once the calendar rolls into September — nothing is broken, the demo data has just aged out. If that happens, run `python manage.py seed_data` again (no need for `--flush`) to generate a fresh incentive centered on today; it won't touch your existing agents, sales, or history. Worth doing right before a demo to your manager, and worth remembering if you deploy this and it sits untouched for a few weeks.

---

## Getting a shareable link for your manager

A Django app needs a real backend host — it can't be a static link. **Render** has a free tier and is the fastest path to a public URL. Rough steps:

1. **Push this project to a GitHub repo** (private is fine — you can invite your manager as a collaborator, or just share the deployed URL).
2. **Create a free account at [render.com](https://render.com)** and choose "New → Web Service", connecting your GitHub repo.
3. Render auto-detects Python. Set:
   - **Build command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start command:** `gunicorn spectrum.wsgi`
4. Under **Environment**, add these variables:
   - `DJANGO_SECRET_KEY` → any long random string (Render can generate one)
   - `DJANGO_DEBUG` → `False`
   - `DJANGO_ALLOWED_HOSTS` → `yourapp.onrender.com` (Render shows you the exact hostname it assigns)
   - `PYTHON_VERSION` → `3.11.15`
5. Deploy. Render will run the build command, then start the app.
6. Once it's live, SSH in via Render's shell (or add a one-time build-command step) to run:
   ```bash
   python manage.py migrate
   python manage.py seed_data
   python manage.py createsuperuser
   ```
7. Share the `https://yourapp.onrender.com` link with your manager.

**Heads-up:** this ships with SQLite for simplicity. Render's free web services use an ephemeral filesystem, so the database resets on redeploys/restarts — perfectly fine for a demo, but if you want data to persist you'd add Render's free PostgreSQL instance and point `DATABASES` at it (ask and I'll wire that up). **PythonAnywhere** is a solid alternative if you'd rather not use GitHub — it lets you upload the folder directly and gives you a persistent `yourname.pythonanywhere.com` URL, but its free tier requires more manual WSGI configuration.

---

## Suggested next steps (phase 2 and beyond)

Role-based logins and routing for all three account types now exist (see "Three login types" above) — what's left is replacing their admin-linked placeholders with purpose-built screens:

1. Analyst: a bespoke screen to create/edit `Incentive`, `IncentiveTierRule`, and `IncentiveProductGoal` rows in place of the Django admin, plus a comparison view charting revenue/points across different past incentives.
2. Director: a real in-app approval queue (approve/reject sales without leaving the portal) in place of the Sale admin's bulk actions, plus an `Incentive.status` field (`draft` / `pending_approval` / `approved`) so a Director can review and approve incentives an Analyst has set up.

Happy to build any of these next — just say the word.
