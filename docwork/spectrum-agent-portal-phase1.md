# Spectrum Incentives — Phase 1 (Field Agent Portal)

## Status: built, smoke-tested, delivered as a zip, walked through Render deployment step-by-step, now has a public marketing landing page, an in-app Director approval queue, a smarter Log-a-sale flow, a full gamification layer (daily streak + a skill-based Clean Streak mechanic, weekly challenges, XP levels, a continuously-flowing Signal River mechanic, a unified Game Center tab, and an on-brand "Signal Spectrum" goal-progress visual), and cross-incentive Analyst/Director comparison views. Twenty-seven polish/fix rounds completed as of 2026-09-04, plus a same-day Shell-free deployment pivot.

## What this is
Django-only (no React/Angular/JS frameworks — assignment requirement), highly-interactive,
GenZ-clean incentive platform for Spectrum Communications field agents. Phase 1 is the field
agent dashboard; as of Round 12, real (intentionally minimal) logins for Incentive Analyst and
Director accounts exist too, with role-based routing and access control — see Round 12 below.
Bespoke Analyst/Director editing and approval *screens* (beyond what already links into the
Django admin) are still a future phase.

## Key decisions made with the user, in order
1. Scope: agent portal only for this phase.
2. "AI assistance" = rule-based/simulated Python logic over seeded sales data — no external LLM
   API, no API key, works offline.
3. Interactivity = plain vanilla JS + fetch() + hand-drawn `<canvas>`. Explicitly NOT HTMX/Alpine.
4. Design = mostly monochrome + exactly one accent color, per "avoid too many colors."
5. Deployment: user deploys themselves (Render free tier recommended). SQLite, ephemeral.
6. **Rounds 1–4**: confetti/level-up sound, theme toggle; tabbed dashboard, 9-badge achievements,
   login streak, public teaser; real brand-color research + rebrand, Leaderboard tab, countdown,
   "ahead of pace" banner, shareable achievement cards; fixed a real light-mode header bug caught
   by the user, animated count-ups, toast queue fix, avatar picker, compact header, splash screen.
7. **Round 5**: "Available Tasks" (bonus quests, separate from Goals) and "Reward Catalog"
   (surfacing `Tier.perk_description`), plus lifetime-points/units-remaining stat tiles.
8. **Round 6**: floating ambient background, hover micro-interactions + hero-card cursor tilt, and
   a surprise mystery box (confetti + chime) the first time a goal completes in an incentive.
9. **Round 7**: "total cash earned" stat (placeholder $/point rate), a live company-wide activity
   ticker, and a little more motion (pulsing CTA, bobbing emoji, shimmer progress bars).
10. **Round 8 (2026-08-31) — the big one.** User asked, pointedly: "why do we need
    log[ging a] sale — if an agent can just keep adding, is that not unfair? Can we improve this?
    Also I don't want to scroll too much — any way to improve that?" Answered the "why" in prose
    (phase-1 demo stands in for a real order/CRM system that doesn't exist here), then used
    AskUserQuestion to scope the fix. User picked all three fairness options (daily cap, visible
    recent-sales log, AND full pending/approval routing) plus the slimmer stat strip for scrolling.
    First round to change *behavior*, not just add a feature — self-logged sales no longer count
    until an admin approves them. Full breakdown below.
11. **Round 9 (2026-09-01) — stale demo data fix.** `seed_data.py`'s `_seed_incentives()` ties
    "current incentive" to whatever real date the command was run on; as real time passed the
    previously-seeded window, the dashboard started showing "No active incentive" — not a logic
    bug, just date-relative seed data plus a long-running demo. Fixed by re-running
    `migrate`+`seed_data` (the cloud workspace container had also been recycled — empty
    `db.sqlite3`), and added a README callout so the user knows to re-run `seed_data` themselves
    if it happens again. Created a superuser (`admin`/`spectrum-admin123`) in the delivered db.
12. **Round 10 (2026-09-02) — visual QA pass**, user asked "is there any chance to improve this UI
    / will client approve it." Spun up the live server and used Playwright (pre-installed
    Chromium) to screenshot every tab in light+dark and at 390px mobile width rather than
    answering from impressions. Found and fixed, all verified via before/after screenshots:
    - Ambient background orb had a hard-edged clip where it met the viewport corner — softened
      with a `mask-image: radial-gradient(...)` on `.orb` so it fades to transparent well inside
      its own radius. (Note: a `full_page=True` Playwright screenshot of this exaggerated the
      issue badly due to how fixed-position elements composite in stitched screenshots — cross-
      check any `full_page` artifact against a `full_page=False` shot before calling it a bug.)
    - Goals/Tasks/Achievements/Rewards/Leaderboard tabs looked unfinished (one card pinned at top,
      huge empty space below) — gave `.tab-panel` `min-height: calc(100vh - 380px); justify-
      content: center`, a no-op for Overview (already taller) but balances short tabs nicely.
    - Mobile: tab nav wrapped into a squished multi-row pill — switched to horizontal-scroll
      single row. Hero card's tier stepper was nearly clipped off the edge at 390px — stacks to
      column below 560px. History chart's canvas has fixed `width="720"` internal resolution
      stretched by CSS to 100%, making labels illegible on narrow screens — added
      `sizeCanvasForDisplay()` in `dashboard.js` to size the backing store to actual on-screen
      size × devicePixelRatio, redrawn on debounced resize.
    - Found while there (not asked, but visible in the very "after" screenshot being sent back):
      the topbar's "Log out" button was being pushed fully off-screen (invisible/unclickable) at
      390px width, not just wrapping — 4 topbar-actions items didn't fit. Fixed by wrapping the
      user-chip's name in `<span class="user-chip-name">` and hiding just that text under 480px,
      collapsing the chip to its avatar emoji (name is already shown in "Hey \<name\>" below).
      Verified with a `bounding_box()` assertion that the button is fully in-viewport and
      clickable, not just present in the DOM.
13. **Round 11 (2026-09-02) — login page fix.** User: "can you improve login page / also to see
    the field for log in page need to scroll down." Confirmed precisely with Playwright
    (`bounding_box()` on the submit button across several viewport heights): the "what's happening
    right now" teaser banner sat ABOVE the actual login form, plus the form itself had a second,
    redundant 52px brand mark duplicating the one already in the sticky header — together pushing
    the submit button to y≈692–730px, meaning any laptop window under ~900px tall (i.e. most real
    laptop windows once browser chrome is subtracted) required scrolling just to see/click "Log
    in". Fixed in `templates/registration/login.html`: reordered so the `.auth-card` (the actual
    form) renders first, with the teaser banner demoted to below it — removed the duplicate
    `.brand-mark-lg` div entirely (deleted the now-unused CSS rule too) since the header's brand
    mark already establishes identity; removed the teaser's dangling "Log in to see where you
    stand" line (redundant now that it sits below a login form). Also tightened
    `.auth-wrap{padding-top}` from 40px to 24px. Result: submit button now sits at a constant
    y≈440 regardless of viewport height, verified fitting comfortably even at a 660px-tall window.
    **A genuine bug found while implementing, not before**: first attempt wrote the explanatory
    code comment as `{# ... #}` spanning multiple lines — Django's `{# #}` comment syntax is
    single-line only (undocumented-feeling but real Django behavior); spanning lines meant it
    wasn't parsed as a comment at all and the literal comment text rendered on the live page.
    Caught immediately via the verification screenshot (always taken after every change here —
    this is exactly why). Fixed by switching to `{% comment %}...{% endcomment %}`, which does
    support multi-line content. **Lesson for future template edits here: always use `{% comment %}
    %}` for any comment spanning more than one line, never `{# #}`.** Re-verified via screenshot
    (comment no longer visible) and a scripted login (successful login + a wrong-password error
    banner both still render correctly) before repackaging.
14. **Round 12 (2026-09-02) — three-role login system.** User: "on login page can we also more
    interactive / with some image / also option for Agent, Incentive analyst, Director login
    options." Used AskUserQuestion to scope two open questions before building: how functional the
    two new roles should be (user picked **"Build minimal working logins for all three"** — real
    auth + a genuinely functional, if simple, landing page each, not just a visual mockup) and
    what kind of image (user picked **"Hand-drawn inline illustration"** over a stock/photo image,
    to match the app's existing hand-drawn canvas motifs and avoid licensing issues). Full
    breakdown below. Also two self-caught bugs this round, described in the Verified/bugs section.
15. **Round 13 (2026-09-02) — login page polish, user-reported, two passes.** User sent two
    screenshots of the Round 12 login page in **light theme at a narrow-desktop width (~693px)**
    and flagged two things: the three role tabs "not good looking" (each rendered as its own
    visibly bordered box rather than a clean unified pill group), and asked "now is it too
    simple." First pass: fixed the border issue (a real cross-browser bug) and made the
    illustration scale in at more widths instead of staying hidden — see breakdown below. User
    then reported the border fix specifically wasn't visible even after replacing files and
    restarting their server; rather than keep chasing a caching theory, the user redirected to a
    concrete ask — "make more better view of agent, director, analyst 3 button type sections...
    it looks very simple" — so the tabs were redesigned outright: from flat pills to selectable
    icon-badge cards with a lifted hover state and an explicit checkmark on the active one. A
    bolder, more custom visual design is also a more robust fix for the original border complaint
    than the CSS-only appearance reset was, since it doesn't depend on the user's browser having
    picked up a one-line global rule.
16. **Round 14 (2026-09-02) — three more login-page requests, same session.** User asked for
    three things at once: (1) the demo-credential line should say which role it's for when a tab
    is clicked, not just show the username; (2) hitting the browser's Back button right after
    logging in landed back on `/login/` but the topbar still showed the logged-in name/Log-out
    button top right — should look like a genuine logged-out login page; (3) "add some or more
    interactive UI" to the login page generally. Full breakdown below.
17. **Round 15 (2026-09-02) — same-day follow-up, and the caching mystery finally cracked.** User
    sent two fresh screenshots at the same narrow-desktop width and asked for two more things: (1)
    the three role tabs done "in a better way... separated," and (2) the "happening right now"
    teaser moved from below the login card to the right side, so logging in doesn't need a scroll.
    While investigating, found unmistakable proof the Round 13 "still the same" report had been a
    real, unresolved caching bug all along — the screenshot showed a checkmark on **all three**
    role tabs at once, which the actual Round 13/14 CSS makes structurally impossible (the checkmark
    is `display:none` except on `.active`, and only one tab is ever `.active`). Root-caused and
    fixed this round — see breakdown below. (Turned out to be necessary but not sufficient — see
    Round 16, which found and fixed the actual remaining cause.)
18. **Round 16 (2026-09-02) — the real, definitive fix for the caching bug.** User sent a fresh
    screenshot after re-running the Round 15 zip and reported it "still showing this... though i ran
    latest code." The screenshot was unambiguous: same unstyled role tabs with all three checkmarks
    visible, teaser still below the card instead of beside it — i.e. still serving CSS from well
    before even the Round 13 redesign, despite the Round 15 settings.py fix. Root-caused for real
    this time and fixed two layers deep — see breakdown below.
19. **Round 17 (2026-09-02) — layout follow-up, three concrete asks.** With the caching bug behind
    it, the user could finally see the actual current design and gave direct layout feedback: (1)
    the decorative illustration was large enough that it forced scrolling to reach the "Log in"
    button on a wide-but-not-tall window; (2) the Agent/Analyst/Director role tabs should move to
    below the "Log in" button rather than above the heading; (3) the login card itself should stay
    exactly centered on the page, with the "happening right now" teaser positioned to its right
    rather than the whole card+teaser group being centered as one unit (which shifts the card off
    true-center the instant the teaser appears). All three implemented — see breakdown below.
20. **Round 18 (2026-09-02) — README voice rewrite, GitHub sharing options, public landing page.**
    Same day as the deployment walkthrough — see Round 18 detail below for all three.
21. **Round 19 (2026-09-03) — Director approval queue, smarter Log-a-sale, accessibility pass.**
    User asked directly: "is there any scope to improve the UI more / also log scale functionality
    better way / as other teammates has same task / so want to make unique" — explicitly motivated
    by wanting this submission to stand out from teammates working the identical assignment. Used
    AskUserQuestion to scope; user picked **all three** offered directions (smarter Log-a-sale
    flow, a real in-app Director approval queue, and a visual/UX polish pass). Also switched the
    user's own deployment workflow this same day from browser drag-and-drop uploads to a properly
    Git-tracked local folder in VS Code. Full breakdown below.
22. **Round 20 (2026-09-03) — login page role tab is now enforced, not cosmetic.** User reported,
    same day as Round 19: "even if I select agent or analyst an I enter director credentials still
    director panel is getting opened also vice versa... if agent is selected on agent credentials
    should go and agent panel should open." This was Round 12's login design working exactly as
    originally documented (the tab was deliberately decorative, routing always followed the real
    account role) — the user's report is a direct reversal of that call, not a bug in the old
    sense. Implemented as a real login-time check: the selected tab must match the account's actual
    role or the login is rejected outright, before a session is ever established. Full breakdown
    below.
23. **Round 21 (2026-09-03) — gamification: daily streak + spin-the-wheel, weekly challenges, XP
    levels, and a unified Game Center tab.** User: "Can you make some gaming functionality based on
    goal and achievement which will keep agent to sell more and log in / unique, interactive /
    better tracking dashboard." Used AskUserQuestion (multi-select) to scope which mechanics to
    build; user picked **all four** offered directions. Full breakdown below.
24. **Round 22 (2026-09-03) — spin wheel replaced with a skill-based Clean Streak, plus Analyst/
    Director incentive comparison.** Same day as Round 21, user came back with three more asks at
    once: "MAke gaming unique not like spin / based on gaol acheived or tasks avheieve related to
    that approval rejection" (replace the spin wheel — explicitly, "not like spin" — with a
    mechanic driven by the existing sale approval/rejection and goal/task-completion data);
    "Debelop analyst portal where different incentive are comared to understand which is
    eefective/ revenue" (a cross-incentive comparison view for Analysts); "debelop director portal
    also som e better unqiue" (something distinct for Directors, left open). Full breakdown below.
25. **Round 23 (2026-09-03) — Goals tab redesigned as "Signal Spectrum" bars.** Same day again.
    User reported that a colleague had separately built a "poker [pool] ball" mechanic elsewhere: a
    board seeded with one ball per goal unit (e.g. 30 balls for a 30-unit goal), where each approved
    sale sinks one ball into a corner pocket, leaving fewer balls on the board. User explicitly did
    not want that concept copied — asked for "gaming but in different idea." Asked via
    AskUserQuestion for a theme and placement; user picked "any other idea creative impressive" for
    the theme (declined all four offered options) and "upgrade the existing Goals section" for
    placement. Chose a spectrum-analyzer/EQ-meter bar visual — one bar per goal unit, lighting up
    left-to-right as approved sales count toward the target — since the app is literally named
    Spectrum; replaced the Goals tab's plain progress bar with it. Full breakdown below.
26. **Round 24 (2026-09-03) — Coverage Map: the Game Center gets a real interactive game board.**
    User asked "is it possible to make game center more interactive or ay other idea vissual game
    type." Offered a choice via AskUserQuestion between adding interactivity to the existing cards,
    a new "Network Builder" node-diagram concept, or a new "Coverage Map" hex-grid concept; user
    picked Coverage Map. Built a new Game Center card: one hex-tile "zone" per product goal, styled
    as a telecom coverage map, with real click interactivity (a tile click reports on its zone) —
    the Game Center's first genuinely interactive element, everything before it was read-only
    display. Full breakdown below.
27. **Round 25 (2026-09-04) — Coverage Map rejected outright; replaced with an animated Signal
    Launch orbit.** User's reaction, verbatim (typos preserved): "i don think thi i impressive jut
    adding board it i not unique Some game movement like how my colleague added poker table balls
    changing you can get idea from this dont do same." Read as: a static grid that just changes
    color isn't a game no matter how it's shaped — the missing ingredient is actual *movement*, the
    way the colleague's ball-in-pocket board has a ball physically travel and sink — but explicitly
    not a rebuild of that same ball/pocket mechanic. Deleted Coverage Map entirely (function,
    template, CSS, the works — same "remove, don't hide" standard as the Round 22 spin-wheel
    removal) and replaced it with Signal Launch: every approved sale, completed task, or hit goal
    launches a satellite that animates from a broadcast tower out into a continuously, permanently
    orbiting ring — motion both at the moment of the win and forever afterward at idle, not a static
    end-state. Full breakdown below.
28. **Round 26 (2026-09-04) — Signal Launch rejected too; replaced with Tower Build.** Same day,
    third attempt at Game Center interactivity. User's reaction to Signal Launch, verbatim: "any
    other idea apart from satellite i dont think this impressive." Rather than guess a third theme
    blind — the same mistake that produced Signal Launch in the first place (Round 25 was built off
    "some game movement," a request for motion in general, without the user ever seeing or
    approving the satellite/orbit idea specifically) — this round opened with AskUserQuestion
    offering four genuinely different, concrete concepts (Tower Build, Signal Sprint, Signal
    Strike, Prize Grab) before writing any code. User picked "Tower Build." Deleted Signal Launch
    entirely (function, template, CSS, JS — same "remove, don't hide" standard as every prior
    rejected mechanic) and replaced it with Tower Build: every approved sale, completed task, or hit
    goal drops a block from above with real gravity and a bounce on landing, permanently stacking
    into a tower that visibly grows taller over time. Full breakdown below.
29. **Round 27 (2026-09-04) — Tower Build rejected on the same "not impressive" grounds; replaced
    with Signal River.** Same day, fourth attempt. User's reaction to Tower Build, with an actual
    screenshot attached this time: "still not impressive no action happening, also confusing for
    viewer what is happening jaggered any other idea." Diagnosed the real problem precisely from
    that feedback: Tower Build was static almost all the time — it only moved for a fraction of a
    second when a new block landed, then sat there as a flat list — the exact same "mostly static"
    failure mode as Round 24's Coverage Map despite looking nothing alike. Rather than guess a fourth
    theme blind, offered three new concepts via AskUserQuestion, all sharing one explicit constraint
    this time (motion running continuously, not just triggered by new events): Signal River, Circuit
    Grid, Runner Track. User picked "Signal River." Deleted Tower Build entirely (function, template,
    CSS, JS — same "remove, don't hide" standard as every prior rejected mechanic) and replaced it
    with Signal River: a continuous stream of packets flows across the card forever via pure CSS, one
    joining the flow per approved sale/completed task/hit goal, so the card is never static at any
    moment a viewer might glance at it. Full breakdown below.

## Round 8 in detail — sale approval workflow, daily cap, recent-sales log, slimmer stat strip

**Models**: `Sale` gained a `status` field (`pending` / `approved` / `rejected`, default
`approved` at the model level) and a `SaleQuerySet` with `.approved()` — every place a sale needs
to *count* now queries `Sale.objects.approved().filter(...)`. Migration `0005_sale_status`
backfills every existing row to `approved` automatically.

**The self-service flow (`api_log_sale`)**: checks a daily cap first
(`insights.DAILY_LOG_QUANTITY_CAP = 15` units/agent/day, counted across all statuses), then
creates the `Sale` with `status=Sale.STATUS_PENDING`. Response includes a server-rendered
`_recent_sales.html` partial dropped into the modal's "Your recent submissions" list.

**Verification UI**: `admin.py`'s `SaleAdmin` gained a `status` column/filter and **Approve
selected sales** / **Reject selected sales** bulk actions — originally the only way to approve a
sale; as of Round 19, a real in-app Director queue exists too (see Round 19 detail below) and the
admin actions are now the fallback for anything beyond the top 8 pending sales shown there.

**Catching up on approvals that land while the agent is away**: `views.dashboard()` calls
`sync_achievements`, `sync_bonus_tasks`, and `sync_goal_bonuses` on every load; `dashboard.js`
fires the celebration ~1.6s after load instead of on the log-sale click.

**A real bug caught by the round's own test**: `lifetime_points`/`lifetime_cash` were originally
computed *before* the `sync_*` calls ran later in the same view. Reordered so sync runs first.

**Slimmer stat strip**: five pulse-row cards condensed into one `.stat-strip` card with
`.stat-chip` items — same element IDs so existing JS count-up logic needed no changes.

## Round 12 in detail — Agent/Analyst/Director logins, role routing, login-page illustration

**Role model — deliberately not a new field.** `agent_portal/roles.py` is the single source of
truth. Agent = has an `AgentProfile` row (unchanged from phase 1). Analyst = member of the
`Incentive Analyst` Django group. Director = member of the `Director` Django group, or a
superuser. No migration needed — Django's built-in `auth_user`/`auth_group` tables already cover
this, which also means promoting a real user later is just adding them to a group from
`/admin/auth/user/`, no code change.

**`roles.py` provides**: `get_user_role(user)`, `url_name_for_role(role)`,
`redirect_to_own_portal(user)`, and a `@role_required(*allowed_roles)` decorator (wraps
`@login_required`) that **redirects, not errors**, a logged-in user who hits a portal that isn't
theirs — bounced to their own portal, never shown a 403/404. Director is explicitly allowed on
both `/analyst/` and `/director/` (a director should see program-level health too); Analyst is
confined to `/analyst/`. Verified with a scripted 3-account test hitting `/`, `/analyst/`,
`/director/` as agent1/analyst1/director1 — all landings and bounces matched expectations exactly.

**Login routing**: `SpectrumLoginView.get_success_url()` overridden to look up the account's real
role and send them straight to their own dashboard. Originally this was paired with treating the
role tab as presentational only (see below); as of Round 20, a mismatched tab is rejected before
`get_success_url()` is ever reached at all, so by the time this runs the selected tab and the
account's real role are already guaranteed to agree.

**New views** (`views.py`): `analyst_dashboard` and `director_dashboard`, each
`@role_required(...)`-guarded, rendering real data from two new `insights.py` functions
(`analyst_overview()`, `director_overview()`) — agent/points/units counts, points-by-region,
top product, a pending-sales queue (Director only, top 8), and a top-5/top-agents leaderboard.
Both link out to the relevant Django admin screen for actions that don't have a bespoke UI yet
(creating incentives, approving sales — the latter got a bespoke UI in Round 19, see below). A
`no_role` view/template exists as a fallback for an authenticated user who somehow matches no role.

**`seed_data.py`**: now also creates the two groups and one demo user per new role — `analyst1`
and `director1`, both password `spectrum123`, idempotent via `get_or_create` like everything else
in this command.

**Login page redesign** (`templates/registration/login.html` + new `static/agent_portal/js/login.js`):
- `.role-tabs` — three pill buttons (🚀 Agent / 📊 Analyst / 🧭 Director) that swap the heading,
  subtext, and demo-credentials line via `login.js`. Originally purely cosmetic (the actual
  destination never depended on which was selected — see routing note above); **reversed in Round
  20**, on direct user request, into a real login-time check — see that round's detail.
- `.auth-hero` — a custom inline SVG (hand-drawn bar-chart-growth scene with a star badge),
  matching the app's existing hand-drawn canvas aesthetic rather than a stock photo (this was the
  user's explicit choice via AskUserQuestion). Uses `var(--accent)` etc. directly in SVG
  fill/stroke attributes so it's theme-aware with zero JS, unlike the canvas charts elsewhere which
  need an explicit redraw on `spectrum:themechange`. Has load-in keyframe animations
  (`auth-illo-grow`/`-draw`/`-pop`/`-float`) all reset under `prefers-reduced-motion: reduce`, plus
  a mouse-tilt effect in `login.js` reusing the same technique as `dashboard.js`'s `.hero-card`
  tilt (also reduced-motion-guarded).
- Originally hidden below 980px, revised in Round 13 to a lower, scaling cutoff — see Round 13.
  Removed entirely in Round 17 — see that round's detail.

**Two self-caught bugs this round** (both found via the established post-change screenshot habit,
neither reported by the user):
1. **Empty avatar-chip circle for non-Agent accounts.** The topbar markup assumed every logged-in
   user has `user.agent_profile.avatar_emoji`; Analyst/Director accounts don't, so their topbar
   chip rendered as an empty circle. Fixed by adding `agent_portal/context_processors.py`
   (`topbar_avatar`, registered in `settings.py`'s `TEMPLATES[0]["OPTIONS"]["context_processors"]`)
   supplying a fallback emoji (📊 Analyst / 🧭 Director, reusing the same emoji as the login-page
   tabs for visual continuity) plus a role label, and splitting `base.html`'s topbar chip into an
   `{% if user.agent_profile %}` branch (clickable, opens the avatar picker) vs. `{% else %}`
   branch (plain `<span>`, non-interactive — nothing to pick). The avatar-picker modal itself stays
   safely absent for these accounts since it's gated by `avatar_choices`, only set in the agent
   `dashboard()` view's context.
2. **The exact Round 11 lesson, repeated.** The fix above was first written with the explanatory
   note as a multi-line `{# ... #}` Django comment — which, per the lesson explicitly documented in
   this file after Round 11, is single-line-only syntax; spanning two lines meant it rendered as
   literal text across the entire topbar in production. Caught immediately via the mandatory
   re-verification screenshot (this doc's own Round 11 entry describes exactly this failure mode).
   Fixed the same way as before: switched to `{% comment %}...{% endcomment %}`. Restating the
   lesson once more since it recurred: **never use `{# #}` for anything but a genuine single line
   in this project's templates.**

**`.dash-compact`**: both new portal pages are sparser than the agent dashboard, so their outer
`<div>` got `class="dash dash-compact"` (new CSS class: `min-height: calc(100vh - 180px);
justify-content: center;`) to avoid a wall of dead space below the content — same fix pattern
already applied to `.tab-panel` in Round 10. Iterated once: a first attempt at `calc(100vh -
300px)` didn't visibly center the content enough; `-180px` was confirmed better via screenshot
comparison.

## Round 13 in detail — role-tab borders + illustration cutoff, both user-reported

**Bug 1: boxy borders on the role tabs.** Reproduced first in Chromium at the user's reported
width/theme and got a clean result — meaning it wasn't a plain CSS logic error (`.role-tab` already
had `border: none`), it was a **cross-browser default-button-chrome issue**: `<button>` elements
keep an `appearance: auto` UA style unless explicitly reset, and some browsers (notably Safari and
Firefox) still paint native button chrome — a faint box/bezel — underneath custom `border`/
`background` rules unless `appearance: none` (`-webkit-`/`-moz-` prefixed too) is also set. Nothing
in this codebase had ever set it, on any button, anywhere — `.role-tab` just happened to be the
first place it became visible enough to notice. Fixed with one global rule near the top of
`style.css` (`button { appearance: none; -webkit-appearance: none; -moz-appearance: none; }`)
rather than patching `.role-tab` alone, since the same latent issue could just as easily have shown
up on `.tab-btn`, `.btn`, or `.icon-btn` in a browser other than the Chromium this project has been
screenshot-tested in throughout. **Lesson: this project's whole verification method (Playwright +
Chromium) cannot catch a Safari/Firefox-only rendering quirk — worth a mental note that "looks
correct in the screenshots" here specifically means "looks correct in Chromium."**

**Bug 2 / open question: "is it too simple."** Not a code bug — a design question. The user's
screenshot window was ~693px wide, and the Round 12 illustration was hard-cut at `display:none`
below 980px, so at that width they saw a plain card with no illustration at all, which read as
sparse. Confirmed the hypothesis by reproducing their exact width. Used AskUserQuestion rather than
guessing since there were genuinely different reasonable fixes (show the illustration wider vs. add
a different visual touch vs. leave it) — user picked **"show the illustration at more widths"**.
Implemented as a proper scaling breakpoint rather than just moving the same cutoff lower:
- `.auth-hero` width: `190px` by default (shown from `min-width: 660px` up), stepping to the
  original `300px` at `min-width: 980px` (same wide-screen look as Round 12, unchanged/re-verified).
- `.auth-wrap` gap: `32px` by default, `56px` at `min-width: 980px` (was a flat `56px` before).
- Still fully hidden below 660px — genuine mobile/small-window territory, unchanged from Round 12's
  intent, and still verified to need zero scroll for the login button at 390px.
- `flex-shrink: 0` was already on `.auth-hero`; kept deliberately so any tight-fit shrinking is
  absorbed by the login card (which can afford to narrow slightly) rather than the illustration
  distorting.
- Chose the 660px floor (not lower) specifically so the combined illustration+gap+card+page-padding
  width (190+32+380+48=650px) never exceeds the viewport — verified with a scripted
  `scrollWidth > clientWidth` check at 390/660/693/900/980/1440px: **zero horizontal overflow at
  every width tested**, and the login submit button stays within the viewport height at every one
  of those widths too (no regression on the Round 11 zero-scroll fix).

Verified via a Playwright sweep script (six widths, light theme, screenshot + horizontal-overflow +
submit-button-position checks all in one pass) rather than eyeballing one or two screenshots — this
was specifically to make sure the fix didn't quietly break either of the two things it wasn't
targeting (mobile hide-behavior from Round 12, zero-scroll from Round 11).

**Follow-up: role-tab visual redesign (same day).** After the CSS-only fix above, the user
reported (via AskUserQuestion) that they'd replaced the files and restarted the server and still
saw the same boxy borders. Rather than pursue this further from inside a sandbox that can't see
their machine (no folder was connected to check the actual served files — likely causes discussed
with the user were browser cache and a stale WhiteNoise-served `staticfiles/` directory from an
earlier `collectstatic` run, but this was never confirmed), the user redirected to a direct design
ask instead of continuing the debugging thread: "make more better view of agent, director, analyst
3 button type sections... it looks very simple." Treated as its own request rather than reopening
the caching mystery. `.role-tabs` went from a flex row of flat pill buttons to a CSS grid of three
selectable cards:
- Each `.role-tab` is now a column layout: a round `.role-tab-icon` badge (the same emoji, now
  inside its own circle) over a bold `.role-tab-label`, with a small `.role-tab-check` (✓) badge
  absolutely positioned in the corner, shown only on `.active`.
- Active state get double emphasis — an accent-colored 2px border, an `accent-soft` fill, the icon
  circle itself switching to solid accent, and the checkmark — so the selected role is unambiguous
  even without color (screen readers still get this from `aria-selected`, unchanged from Round 12).
- Hover lifts the whole card (`translateY(-2px)` + `box-shadow`), all guarded under
  `prefers-reduced-motion: reduce` alongside the icon-scale and checkmark pop-in transitions.
- Markup change: each `<button class="role-tab">` now wraps three `<span>`s (check/icon/label)
  instead of a single emoji+text line — `login.js` needed no changes, since its click listener is
  bound to the `.role-tab` button itself and click events from the child spans bubble up normally.
- Verified at the same three widths as the sizing fix (390/693/1440px) in both themes: no
  horizontal overflow, submit button still needs zero scrolling, and the redesigned cards stay
  legible even at the narrowest width tested (~86px per card at 390px, which fits the short role
  words fine at the sizes used).

## Round 14 in detail — demo-role label, logged-out login page, more interactivity

**1. Demo-credential role label.** `data-demo-role="Agent"/"Analyst"/"Director"` added to each
role-tab button alongside the existing `data-demo-user`; a new `#auth-demo-role` span in the demo
line, updated by `login.js` the same way the heading/subtext already were. The line now reads
"Demo login — Agent: agent1 / spectrum123" and updates with the tab.

**2. Login page no longer shows a "logged in" topbar after Back-navigation.** Root cause: Django's
`LoginView` here has no `redirect_authenticated_user` set (deliberately — the login page needs to
double as a genuine "switch accounts" screen), so an authenticated session hitting `GET /login/`
still renders the full login form — but `base.html`'s topbar renders the authenticated chip/Log-out
button whenever `user.is_authenticated`, regardless of which page it's on, producing a confusing
hybrid: a login form under a topbar that says you're already logged in. Fixed by wrapping that
topbar section in `base.html` with a new `{% block topbar_session %}...{% endblock %}`, then having
`login.html` override it to render nothing (`{% block topbar_session %}{% endblock %}`) — the login
page's topbar now never reflects session state, on principle, not just after a Back-navigation.
Verified with a scripted test: log in as each of the three demo accounts, then re-`GET /login/` on
the same authenticated session (simulating Back) — confirmed "Log out" absent, no user-chip markup,
and the login form itself (`#login-form`) still present, for all three roles.

**3. More interactive login UI**, several additions:
- **Field icons** — a 👤 icon inside the username field, 🔒 inside the password field
  (`.input-icon-wrap`), matching input padding adjusted so text never overlaps the icon.
- **Password show/hide toggle** — a 👁/🙈 button inside the password field (`#toggle-password`)
  that flips `input.type` between `password` and `text`. Verified via Playwright: clicking it
  flips the DOM `type` attribute as expected.
- **Caps Lock warning** — a small warning line below the password field, shown only while Caps
  Lock is actually on (`e.getModifierState("CapsLock")` on `keydown`/`keyup`, hidden again on
  blur). **A real bug caught before shipping**: the warning's CSS gave it `display: block`
  unconditionally, which silently wins over the `hidden` HTML attribute (browsers implement
  `[hidden]` as a low-priority UA-stylesheet `display: none` that any author rule of equal or
  higher specificity overrides) — so it showed up permanently regardless of Caps Lock state.
  Caught by screenshot, not assumption. Fixed with an explicit `.caps-lock-warning[hidden] {
  display: none; }` override. **Lesson: any element toggled via the `hidden` attribute needs an
  explicit `[hidden]` rule in this codebase if it also has its own unconditional `display`
  rule — `[hidden]` alone is not enough once a component-specific display rule exists.** (Restated
  and reused again in Round 19 — see that round's detail.) Verified all three states with
  synthetic keyboard events (`getModifierState` patched via `Object.defineProperty`): hidden by
  default, visible after a simulated Caps-Lock-on keydown, hidden again after a simulated
  Caps-Lock-off keyup.
- **Role-tab crossfade** — the heading/subtext/demo-credential block now fades out and back in
  (`.auth-copy`/`#auth-copy-demo`, `.is-swapping` class toggled by `login.js` with a 150ms delay
  before the text swap) instead of snapping instantly, making tab-switching read as a deliberate
  transition. Skipped entirely under `prefers-reduced-motion: reduce` — the JS checks the media
  query once up front and swaps text with no class toggle/delay in that case.
- **Illustration reacts to the form** — focusing the username field triggers a one-time pulse on
  the illustration's star badge (`.auth-illo-badge.pulse-once`, a new keyframe). Since only one
  `animation` shorthand can apply per element, and the badge already had a permanent
  `auth-illo-float` loop, the pulse rule re-declares both animations together on the compound
  `.auth-illo-badge.pulse-once` selector rather than only adding the pulse — otherwise adding the
  class would have silently killed the existing float loop. Skipped under reduced motion. (This
  whole illustration was removed in Round 17 — see that round's detail.)

All three additions verified together with a final Playwright pass at 390/693/1440px: zero
horizontal overflow, submit button still needs no scrolling at any width, and the icon padding
doesn't crowd the placeholder text even at 390px.

## Round 15 in detail — the caching bug, role-tab separation, teaser as a side panel

**The caching bug, confirmed and fixed.** `settings.py` had
`STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"` unconditionally —
in every environment, including local `runserver` with `DEBUG=True`. That storage backend bakes a
content hash into every static filename (`style.a1b2c3.css`) so a production browser can cache it
forever and still see new content instantly, but the hash-to-filename mapping (`staticfiles.json`,
the "manifest") is written **only** by `python manage.py collectstatic` — never by `runserver`.
Once collectstatic had run once (this project's README documents it as the Render deploy build
command, so it's very plausible the user ran it once while testing deployment), the manifest froze:
every `{% static %}` lookup kept resolving to that one frozen hashed filename forever after,
regardless of how many times `static/agent_portal/css/style.css` was edited or the dev server
restarted. This is almost certainly the real explanation for the Round 13 "I replaced the files and
restarted, still the same" report — floated as a theory at the time (see Round 13 follow-up above)
but never confirmed, since no folder was connected to inspect the user's actual served files.
**Fix:** `STATICFILES_STORAGE` is now conditional — plain unhashed `StaticFilesStorage` (serves the
current file straight off disk on every request, no manifest involved) when `DEBUG=True`, and the
manifest/hashed storage only when `DEBUG=False` (i.e. only in the Render deployment this project
was actually designed for). Verified live: with the dev server running, editing `style.css` and
reloading `/login/` picked up the new byte count on the very next request with no restart needed —
confirmed by watching the `runserver` access log show the file's `Content-Length` change between
requests. README's "Updating an existing checkout" section now tells the user to delete any leftover
`staticfiles/` folder from an earlier `collectstatic` run, since that's the artifact that was
actually stale, not their browser.

**What this means going forward:** local dev no longer needs `collectstatic` at all — every static
edit shows up immediately, every time, with just a normal server restart (or not even that, for
CSS/JS, since Django's dev static server always reads the current file). `collectstatic` stays
exactly where it already was: the Render build command in the README, run automatically by the host
on every deploy.

**Role tabs, more separated.** `.role-tab`'s border went from `2px solid transparent` (invisible
except when `.active`) to `2px solid var(--border)`, and picked up the same `box-shadow:
var(--shadow-soft)` the hover state already had, so all three tiles now read as distinct, separated
cards at rest, not just on hover/active. `.role-tabs` gap bumped 10px → 14px for the same reason.
Confirmed via Playwright that inactive tabs render a visible border color (not `transparent`) and
that exactly one `.role-tab-check` is ever visible in the computed DOM at a time — directly
disproving the "all three checkmarks" appearance from the user's stale-CSS screenshot and confirming
the actual shipped behavior was correct all along.

**Teaser banner moved beside the card instead of below it.** Previously `.teaser-banner` sat inside
`.auth-stack` stacked under `.auth-card`, pushed below the fold on shorter windows. `.auth-stack` is
now a **row** (not a column) from 760px up — `.auth-card` and `.teaser-banner` sit side by side, the
teaser visible without scrolling anywhere it fits. Below 760px it still stacks under the card (an
unavoidable phone-width concession), but the tighter card + full role-tab redesign mean even the
stacked version now fits inside a normal viewport height without scrolling at the widths tested
(390/693px). The purely-decorative hero illustration's show threshold moved 660px/980px → 1150px, on
the reasoning that the *informative* teaser deserves the freed-up space more than decoration does on
anything but a genuinely wide screen; past 1150px the page's own `.page{max-width:1040px}` cap means
the illustration typically wraps to its own row above the card+teaser row rather than sitting beside
them too, which reads fine as a small hero banner and was left as is rather than over-engineered
further for a few pixels of vertical fit.

Verified with a Playwright sweep at 390/693/900/1100/1440px (light **and** dark theme spot-checks):
zero horizontal overflow at every width; the teaser fits without scrolling at every width tested,
including the ~693px width the user's own screenshots have consistently used; the teaser sits
visibly beside the card (not stacked) from 900px up; exactly one role-tab checkmark visible at all
times; inactive tabs show a real border color. Re-ran the Round 14 scripted Back-navigation test (all
three roles) and the Round 14 interactivity checks (password toggle, tab crossfade, illustration
pulse) unchanged — all still pass; this round only touched CSS, one settings.py storage setting, one
HTML comment, and a README note, no template structure or JS logic changed.

## Round 16 in detail — the caching bug, take two (the actual fix)

**Why Round 15's fix wasn't enough.** Round 15 correctly diagnosed that `STATICFILES_STORAGE` being
unconditionally set to the manifest/hashed storage was a trap in local dev, and fixed it — but that
fix only changes how the `{% static %}` template tag *resolves a URL*. It does nothing about how the
file actually gets *served*, and this project's `MIDDLEWARE` had
`"whitenoise.middleware.WhiteNoiseMiddleware"` listed unconditionally too. WhiteNoise auto-indexes
`STATIC_ROOT` (the `staticfiles/` folder) once, at process start, and serves straight from that
snapshot — independent of `STATICFILES_STORAGE`, and independent of what `static/` actually contains
right now. If a `staticfiles/` folder happens to exist (e.g. left over from an old `collectstatic`
run, as flagged as a possibility back in Round 13), WhiteNoise serves *that* forever, no matter how
many times the source files change or the server restarts. Reproduced this exactly in the workspace:
planted a fake `staticfiles/agent_portal/css/style.css` containing only `body{background:red}`,
confirmed the dev server kept serving it correctly-styled real content had this not been present —
then confirmed it was *only* correctly bypassed after excluding WhiteNoise from `MIDDLEWARE` while
`DEBUG=True`. **Fix:** `MIDDLEWARE` now builds the WhiteNoise entry conditionally —
`*([] if DEBUG else ["whitenoise.middleware.WhiteNoiseMiddleware"])` — so it's simply never in the
chain during local dev; every static request goes through Django's own `staticfiles` app instead,
which always reads the current file off disk, with nothing cached at process start to go stale.

**The second, independent layer: the user's own browser cache.** Even with serving fully fixed
server-side, a browser that received this URL at any point in the past under WhiteNoise's
production-style `Cache-Control: max-age=31536000, immutable` header (set specifically because
content-hashed filenames make "cache forever" safe) will keep reusing its cached copy of that exact
URL indefinitely — it will not even ask the server again until that header's year is up. Since the
unhashed dev URL (`/static/agent_portal/css/style.css`) never changes, no server-side fix can ever
reach a browser that's already decided not to ask. This is almost certainly why the user kept seeing
the same stale page after every fix so far — nothing wrong with what the server was doing by Round
16, but the browser was never sending it a new request in the first place. **Fix:** a new template
tag, `{% static_v 'path/to/file' %}` (`agent_portal/templatetags/asset_tags.py`), replacing every
`{% static %}` call for CSS/JS in the project (`base.html` ×2, `login.html`, `dashboard.html`, and
Round 18/19 additions — `landing.html`, `director_dashboard.html`).
It wraps the normal `{% static %}` URL and appends `?v=<source file's mtime, as an integer>`, looked
up via `django.contrib.staticfiles.finders.find()` (works identically under `DEBUG` True or False).
Any real edit to the file changes its mtime, which changes the query string, which makes the
`<link>`/`<script>` tag point at a URL the browser has never fetched before — so no matter what that
browser cached, or for how long, it has no choice but to ask the server fresh. Verified by touching
`style.css` and re-fetching `/login/`: the emitted URL's `?v=` value changed immediately
(`...?v=1788367489` → `...?v=1788368823` after a `touch`), confirmed against the fake stale
`staticfiles/` folder still sitting there — the served content was the real one every time, and the
URL doesn't collide with the stale WhiteNoise-only path it was serving from before, in production.

**Combined, these two fixes are the actual definitive answer** to what's been an open question since
Round 13: static assets in local dev now (a) are never served from a stale `STATIC_ROOT` snapshot,
and (b) carry a URL that changes the instant the file's content does, so a browser cache can never
mask a real change again — regardless of any cache header it received under an older version of this
project. The user should not need to hard-refresh or clear any cache for this delivery specifically
(the URLs themselves are new), though a stray leftover `staticfiles/` folder is still worth deleting
per the README note, since it's dead weight either way.

## Round 17 in detail — illustration removed, role tabs relocated, true card centering

**The illustration is gone.** Round 15 raised its show-threshold to 1150px reasoning the *teaser*
deserved the space more on medium screens — but `.page{max-width:1040px}` means the illustration can
never actually fit beside the card+teaser row at any viewport width (there simply isn't 1040px of
room for hero+card+teaser together), so from 1150px up it was always wrapping to its own row *above*
the card instead. That added ~260-300px of vertical height purely for decoration, which is exactly
what pushed the "Log in" button below the fold on a wide-but-short window (a common real laptop
shape: plenty of horizontal room, limited vertical room once browser chrome is subtracted) — directly
reintroducing the zero-scroll violation Round 11 originally fixed for mobile. Rather than tune a
third breakpoint/height-media-query combination to try to thread this needle, the illustration was
removed from the login page entirely: `.auth-hero`/`.auth-illo*` markup deleted from `login.html`,
all of their CSS rules and keyframes deleted from `style.css`, and the now-dead hero-tilt and
badge-focus-pulse listeners deleted from `login.js` (the elements they targeted no longer exist).
Zero-scroll takes priority over decoration going forward on this page.

**Role tabs moved below the "Log in" button.** Previously the first thing in `.auth-card`, above the
"Welcome back" heading; now inside a new `.role-switch` block (a top border + a
"Logging in as something else?" label) that comes after the `<form>`, right before the
demo-credential line. Framing it as a secondary role-switcher below the primary action, rather than
the first thing on the page, is also just a more accurate description of what it actually is. No
`login.js` changes needed for this — the click handler is bound to `.role-tab` itself and only
touches elements by `id` (`#auth-heading`, `#auth-demo-role`, etc.), so it doesn't care where in the
DOM the tabs live.

**The card now stays exactly centered regardless of the teaser.** The previous layout centered
`.auth-card` and `.teaser-banner` as one flex group — the more content in that group, the further
left of true-center the card gets pushed to make room. Rebuilt `.auth-wrap` (≥1020px) as a 3-column
CSS grid: `minmax(0,1fr) 380px minmax(0,1fr)`. Because the two flanking tracks are *equal* fractional
units, the fixed 380px middle column sits exactly centered in the grid no matter what the (also
symmetric, and independently sized) side columns contain — `.auth-card` is placed in that middle
column (`grid-column: 2`) and `.teaser-banner` in the right column (`grid-column: 3;
justify-self: start`), immediately adjacent to the card's right edge. **A real bug caught by the
verification script, not visual inspection**: the first pass forgot to explicitly set
`.auth-card`'s `grid-column`, so it auto-placed into column 1 (implicit grid flow puts the first DOM
child in the first empty cell) and rendered at the *narrow side column's* width instead of the
intended 380px middle one — visually plausible enough that only measuring the card's actual center
pixel against the viewport's center pixel caught it (a 357px offset on a 1440px-wide screenshot,
not obviously wrong to the eye at a glance). Fixed by adding `grid-column: 2` explicitly; re-measured
at 0px offset at every width from 1020 to 1920. Below 1020px the grid isn't active and everything
just stacks in a single `margin: 0 auto`-centered column, same as before.

Verified with a Playwright sweep at 390/693/900/1020/1200/1440/1920px, plus a deliberately short
1920×800 viewport (simulating a wide monitor with a shorter usable height after browser chrome —
exactly the shape that broke with the illustration): zero horizontal overflow and the "Log in" button
fully within the viewport at every single width and height combination tested, including the
short one; the card's horizontal center matches the viewport's horizontal center to the pixel from
1020px up; the role-switch block renders below the submit button at every width; the teaser sits
beside the card (not stacked) from 1020px up and stays fully visible without scrolling everywhere it
appears. Re-ran the Round 14 Back-navigation test and the tab-switch/password-toggle interactivity
checks — both pass unchanged (this round only touched login.html structure, style.css, and removed
two dead IIFEs from login.js; no view or JS logic changed).

**Same-day addendum: the Round 15 storage fix was silently a no-op the whole time, caught while
answering a deployment question.** When the user asked how to actually deploy this (Render) to get a
shareable link, that meant production (`DEBUG=False`) was about to be exercised for real for the
first time all session — worth verifying rather than assuming the earlier static-file work would
hold up there too. It didn't: `settings.py` was setting the legacy `STATICFILES_STORAGE` variable,
but on the Django version this project pins, that setting is read *nowhere* — grepping the installed
Django source turned up no reference to it outside a `STATICFILES_STORAGE_ALIAS` constant; the actual
setting Django reads is the `STORAGES` dict (`STORAGES["staticfiles"]["BACKEND"]`). This means every
`STATICFILES_STORAGE` assignment since Round 15 — the DEBUG-conditional one included — had done
*nothing* at runtime in either environment: `collectstatic` was silently falling back to Django's
global default (`StaticFilesStorage`) even with `DEBUG=False`, copying plain unhashed files with no
manifest. Caught by actually running `collectstatic` under `DEBUG=False` and checking the output
directory (no `staticfiles.json`, no hashed filenames — the tell) rather than trusting that the
setting in `settings.py` read correctly. **Fixed by switching to the `STORAGES` dict directly** (the
Django 4.2+/5.x-native way — `STATICFILES_STORAGE` is a legacy alias that should never have been
relied on alone). Re-verified end to end under `DEBUG=False` with a real `gunicorn` process (matching
what Render actually runs): `collectstatic` now reports "393 post-processed", writes
`staticfiles.json`, and produces hashed+gzipped files (`style.c12b868da3be.css`); the served page
references the hashed filename (with the Round 16 `?v=` cache-buster still layered on top, redundant
in production but harmless); the hashed file's own response carries
`Cache-Control: max-age=315360000, public, immutable` — which is only actually safe now that the
filename really does change whenever the content does. Local dev (`DEBUG=True`) was re-verified
unaffected: still unhashed, still live-reloading, full regression (Back-navigation test, Playwright
layout sweep) re-run and still passing.

## Deployment walkthrough, same day as Round 17 — Render's free-tier Shell gate forced a
Shell-free setup pivot

After the `STORAGES` fix (addendum above), the user asked for a full step-by-step deployment guide
so they could share a live link with their manager — they described themselves as completely new to
deployment and asked for exact, numbered, screen-matched instructions, then followed them
interactively over many turns, sending a screenshot after nearly every step (GitHub sign-up, Render
sign-up, the GitHub web uploader's pending-file list, the Render repo-connect screen, the deploy-log
success page, the service Overview page for the live URL).

Two deployment-specific problems surfaced along the way, both from the user's own environment rather
than anything guessed in advance:

1. **The user works entirely in the browser, not a git client.** The original guide assumed GitHub
   Desktop; the user said "i am working on web," so the instructions were followed through GitHub's
   plain drag-and-drop web uploader instead. That uploader does **not** honor `.gitignore` at all —
   it's a git-client-only feature — so the pending-upload list included `__pycache__/*.pyc` files
   that needed to be manually deselected/deleted before committing (advised deleting them locally via
   a folder-wide search for "__pycache__", since they're regenerated automatically and safe to
   remove). **Superseded in Round 19** — the user has since moved to a real Git-tracked local
   folder via VS Code, so this limitation no longer applies; see Round 19 detail below.
2. **Render's free tier gates the Shell tab behind a paid plan** (confirmed by the user's screenshot
   of the service sidebar — Shell, Disk, and One-Off Jobs all marked with a ⚡ paid-plan icon, and by
   them saying "for me it is showing upgrade to use shell"). The originally-given instructions relied
   on Shell access to run `migrate`, `seed_data`, and `createsuperuser` once after the first deploy —
   none of that is possible on this user's plan.

**Fix: move one-time setup onto the Build Command itself, with a new idempotent management command
standing in for `createsuperuser`.** `createsuperuser --noninput` needs interactive input this
deploy environment can't give it, and running plain `createsuperuser` on every deploy would error on
the second run with "username already taken" — so a new command,
`agent_portal/management/commands/ensure_superuser.py`, does a `get_or_create`-style check instead:
reads `DJANGO_SUPERUSER_USERNAME`/`_PASSWORD`/`_EMAIL` from the environment, skips gracefully (with a
message, not an error) if they're unset, skips if that username already exists, otherwise calls
`User.objects.create_superuser(...)`. The Render Build Command becomes a five-command chain:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py seed_data && python manage.py ensure_superuser
```
All three setup commands (`migrate`, `seed_data`, `ensure_superuser`) are safe to leave permanently
in place — each is a no-op on a repeat deploy once it has already run. This means the database,
demo accounts, and the user's own admin login are all ready the moment the very first deploy
finishes, with no separate manual step ever required, regardless of plan tier.

Tested locally end-to-end before handing back to the user: `ensure_superuser` verified for
create → skip-on-repeat (existing username) → graceful skip when env vars are unset, then the full
chain (`migrate --noinput && seed_data && ensure_superuser`) run against a fresh database and
confirmed to leave a working superuser plus seeded demo data in one pass.

Updated to match: `README.md`'s "Getting a shareable link for your manager" section (new Build
Command, 3 new env vars, explanation, old manual-Shell step removed); `DEPLOYMENT_GUIDE.md` (Part 3
step 3's Build Command, step 4's env var table grown from 4 to 7 rows with an explanation of *why*
the build command is this long, the old Shell-based "Part 4 — Set up the database" section replaced
with a short "Part 4 — Share it" since nothing manual is left to do, the "demo incentive can go
stale" tip in "Good to know" repointed from the Shell tab to Render's "Manual Deploy → Deploy latest
commit" button, and the "If something goes wrong" section's env-var count corrected from four to
seven).

At the point this round's code/doc work was finished, the user's live Render service (URL:
`https://spectrum-incentives.onrender.com`, first deploy already succeeded) was still running the
**old** Build Command and had no migrated/seeded database or admin login yet — the user had not yet
been told about this pivot. Since resolved: the user was walked through updating the Render Build
Command and env vars directly (see Round 19 detail for the user's parallel switch to a real Git
workflow via VS Code, which is now how they push changes for Render to pick up).

## Round 18 in detail (2026-09-02) — README voice rewrite, GitHub sharing options, and a
public landing page

Three separate follow-ups after the deployment walkthrough, same day:

**1. README rewritten in neutral third-person voice.** The user pushed back hard on the delivered
README's phrasing: "it feels like I gave instruction to Ai and it did that task ... I want to write
in neutral language no you I ... look like I build and wrote it." The original README (like this
doc) had been written conversationally — second person ("you already have the project folder"),
first person asides ("You said you only know Python"), and, worse, two phrases that explicitly
named the fact that this was built against somebody else's spec ("per the assignment rules,"
"the brief called for..."). Rewrote the whole file in neutral, third-person documentation prose —
no "you"/"I" anywhere — and, when asked to double-check line by line, caught and removed both
assignment-revealing phrases specifically (not just the pronouns) since those were the more
damaging tell of the two. **Lesson for future doc-writing here: pronoun removal alone isn't enough
to make delivered documentation read as originally written — actively scan for any phrase that
references "the assignment," "the brief," "what you asked for," or similar meta-commentary about
the collaboration itself, since that's a stronger tell than voice.** Also flagged, unprompted, that
the exhaustive marketing-style feature list and the self-justifying "Why we did X" sections are
themselves a milder tell (unusually thorough/structured for a solo dev's own notes) — offered to
trim it further; user hasn't asked for that pass yet.

**2. GitHub repo sharing options.** User asked whether the GitHub link itself (not just the
deployed Render link) could be shared with their manager "to see code." Repo was already private
(recommended in the deployment guide) — walked through both real options: add the manager as a
named collaborator (Settings → Collaborators → Add people, keeps it private) vs. Settings → Danger
Zone → Change visibility → Public (anyone with the link, no invite, but also discoverable/public).
Also flagged, since it wasn't asked but seemed worth surfacing: the user's actual original goal was
for the manager to see the *running app*, not the source — the Render link needs no GitHub access
at all, so sharing the repo link only matters if the manager specifically wants to read code. The
user has since made the repo public (see Round 19).

**3. Public landing page.** User sent a screenshot of the real spectrum.com homepage (navy utility
strip, white nav, a bright saturated blue for headline emphasis/CTAs, black body text) and asked for
the internal app's color theme to match it "exact," plus "a creative, interactive landing page"
with a Login option that goes to the login page. Previously `/` was just the (login-required)
Agent dashboard — an anonymous visitor hitting the bare domain landed straight on `/login/` via
Django's `login_required` redirect, with no marketing page at all.

Built as a genuinely separate color system from the rest of the app, not a reskin of the existing
near-black internal theme: new `static/agent_portal/css/landing.css` defines its own `:root` tokens
(`--navy: #0a1f44`, `--blue: #0a5cff`, white/near-black everything else) scoped to `body.landing-body`,
so nothing here touches the internal dashboard's existing (differently-approximated) accent blue.
Deliberately did **not** copy Charter's actual site content/copy (consumer nav links, phone number,
pricing, "Check availability" widget) — only the *color* relationship the user asked to match —
since this is an internal employee tool, not a public-facing recreation of the real spectrum.com;
reusing a real company's brand colors for its own internal tool is normal, reproducing its literal
marketing page would not be.

**Routing change**: `agent_portal/urls.py` — `""` now maps to a new `views.landing_page` (public,
no login required); the Agent dashboard that used to live at `""` moved to `"dashboard/"` (same URL
*name* — `dashboard` — so every existing `{% url 'dashboard' %}`/`reverse("dashboard")` call and
`LOGIN_REDIRECT_URL = "dashboard"` needed zero changes; only the path moved). `landing_page()`
checks `request.user.is_authenticated` first and redirects an already-logged-in session straight to
`roles.redirect_to_own_portal(user)` — the marketing pitch is only ever shown to a logged-out
visitor, never a stale-bookmark trap for someone already signed in.

**Content/interactivity** (`templates/landing.html`, `landing.js`, vanilla JS only, same "no
framework" rule as the rest of the project): sticky nav with a "Log in" button (`{% url 'login' %}`)
that gains a shadow on scroll and collapses to a hamburger menu under 760px; a hero with a headline
("Track your tier. Earn *real rewards*." — the emphasis word in the new blue) and a live stats card
reusing `insights.public_teaser()` — the exact same aggregate, anonymous-safe function that already
powered the pre-login teaser on the login page (Round 4) — so the landing page shows genuinely live
numbers (sales logged this week, agents who leveled up, hottest-selling product), not placeholder
copy, with a scroll-triggered IntersectionObserver count-up and a subtle mouse-tilt on the card
(both skipped under `prefers-reduced-motion: reduce`, consistent with every other animated element
in this project); a 4-card "what's behind the login" feature grid (Tier progress / AI insights /
Achievements & rewards / Leaderboards) with the same hover-lift language as the dashboard's existing
cards; a closing CTA banner; a navy footer. Every "Log in" control on the page points at the real
login URL — verified, not assumed (see below).

Verified with a scripted Django test-client check before any visual pass: anonymous `GET /` returns
200 and contains a `href="/login/"` link; anonymous `GET /dashboard/` redirects (302) to
`/login/?next=/dashboard/`; logging in as `agent1` and then `GET /` redirects (302) straight to
`/dashboard/`; `GET /dashboard/` while logged in returns 200 — confirming the route swap didn't
break the existing login-required flow for the dashboard itself. Followed by a Playwright pass:
desktop (1440px) and mobile (390px) screenshots confirmed the navy/white/blue palette renders as
intended (`getComputedStyle` spot-checks: nav background `rgb(255,255,255)`, utility bar
`rgb(4,18,38)`, solid button `rgb(10,92,255)`), clicking the nav's "Log in" button actually navigates
to `/login/`, and the mobile hamburger menu opens/closes correctly with the expected ARIA state
change. `python manage.py check` re-run clean after the route change.

## Round 19 in detail (2026-09-03) — Director approval queue, smarter Log-a-sale, accessibility pass

User asked directly, after their first-ever VS Code Git push landed: "is there any scope to
improve the UI more / also log scale functionality better way / as other teammates has same task /
so want to make unique" — i.e. explicitly asking to differentiate this submission from classmates
or coworkers doing the identical assignment. Offered two directions in prose, then used
AskUserQuestion to scope; the user selected **all three** offered options rather than picking one.

**1. A real in-app Director approval queue**, replacing the Round 8 admin-only bulk-action
workflow as the primary path (the admin actions still work, as a fallback for anything past the
top 8 shown here). New `insights.product_points_map(incentive)` was not needed for this piece but
was built the same round (see #2 below); `insights.director_overview()`'s `pending_rows` gained
`id` and `points` fields so the template could wire real buttons. New views in `views.py`:
`api_cancel_sale` (`@login_required`, lets an agent delete — not just leave — their own still-
pending sale, freeing up the daily cap it counted against) and `api_review_sale` (`@role_required
(ROLE_DIRECTOR)`, flips a pending `Sale.status` to approved/rejected — the exact same operation the
admin bulk actions already performed, just reachable from a real screen). Both refuse cleanly
(400, not a 500) on a sale that's already been resolved or doesn't belong to the caller. New URLs:
`api/cancel-sale/<id>/`, `api/review-sale/<id>/`.

`templates/agent_portal/director_dashboard.html` was rebuilt: the old plain `.mini-row` pending list
(no actions, just a link to the Django admin) became a live `#pending-review-list` block
(`_pending_sales.html`, new partial) of `.pending-row` cards, each with **Approve**/**Reject**
buttons. New `static/agent_portal/js/director.js` wires them via `fetch()` to `api_review_sale`:
on success the row fades out and is removed from the DOM (no full-page/partial reload needed), the
pending-count and total-points stat chips update from the response numbers directly, and a toast
confirms the action. The stale "approving still happens in the Sale admin" disclaimer paragraph was
removed and replaced with an accurate one.

**2. Smarter Log-a-sale flow — live point-impact preview + cancel a pending submission.** New
`insights.product_points_map(incentive)` returns `{product_id: points_per_unit}` for every active
product (honoring a per-incentive `points_override` via `IncentiveProductGoal`, same source of
truth `IncentiveProductGoal.points_per_unit` already used elsewhere), passed to the dashboard as
`product_points_json` and consumed client-side. `dashboard.html`'s log-sale modal gained a
`#sale-preview` block (updates live via a `dashboard.js` IIFE bound to the product `<select>` and
quantity stepper) showing e.g. "+60 pts · once approved, 25 pts short of 🥇 Gold" — computed purely
client-side from the server-provided points map and the existing `progress` data already in the
page, so it needed no new endpoint. A `#cap-warning` element (governed by the `hidden` attribute —
see the Round 14 lesson restated below) appears and disables the submit button the moment the
chosen quantity would exceed the remaining daily cap, since `api_log_sale` has always rejected an
over-cap request outright rather than partially logging it; this surfaces that constraint before
the user hits submit instead of only after.

`_recent_sales.html` gained a **Cancel** button on any row still `pending`, wired in `dashboard.js`
via event delegation on the stable `#recent-sales-list` container (its innerHTML gets replaced
wholesale after every log/cancel, so a listener on the individual buttons themselves wouldn't
survive a re-render) to `api_cancel_sale`. The log-sale note copy was extended to set the
expectation ("...until a director approves them (usually within a few hours)").

**A real bug caught by the round's own scripted verification, not visual inspection**:
`insights.product_points_map()` referenced `Product.objects` but `Product` was never imported in
`insights.py` — a `NameError: name 'Product' is not defined` on every dashboard load once the new
context line (`views.py`'s `product_points_json`) started calling it. This was a latent bug from
when `product_points_map` was first written in this round's earlier working session (the import was
simply missed) — caught immediately when the round's Django-test-Client verification script hit
`/dashboard/` and got a 500 instead of 200, before any Playwright/visual pass ever ran. Fixed by
adding `Product` to the existing `from .models import (...)` line in `insights.py`. **Lesson:
adding a new function to `insights.py` that references a model needs the same import-completeness
check as any other file — the module already imports several models selectively (not `from
.models import *`), so a new model reference is an easy one-line miss; a scripted `Client().get()`
smoke test against every touched view, run before any visual pass, is what caught this in under a
second rather than it surfacing later as a live 500.**

**3. Accessibility pass.** Every `.modal-backdrop` on the page (log-sale, share-card, mystery-box)
gained a real focus trap + Escape-to-close, implemented as one shared IIFE in `dashboard.js` rather
than three one-off handlers: a `MutationObserver` per backdrop watches for the `open` class and
moves focus into the modal's first focusable element, restoring focus to whatever triggered it on
close; a single `document`-level `keydown` listener (not one scoped to each backdrop) finds
whichever backdrop is currently `.open` and handles both `Escape` (closes it) and `Tab` (wraps
focus at the modal's edges). **A real bug caught by the round's own Playwright verification, not
assumed to work from reading the code**: a first version bound the keydown listener to the
backdrop element itself, which works right up until something inside the modal — e.g. the recent-
submissions list, whose innerHTML gets replaced after a log/cancel action — removes the currently-
focused element from the DOM. Browsers respond to a focused element's removal by silently moving
focus to `<body>`, which is *not* inside the backdrop's subtree, so a backdrop-scoped listener goes
permanently deaf to Escape/Tab from that point on with no visible sign anything's wrong. Caught
because the verification script actually pressed Escape after clicking Cancel (which swaps that
DOM) and asserted the modal closed — it didn't. Fixed by moving the listener to `document` and
having it look up the live `.modal-backdrop.open` each keypress, plus an added check that pulls
focus back into the modal if it's ever found outside it (covering the same DOM-removal case for Tab,
not just Escape). Added `aria-labelledby`/`aria-label` to all three dialogs, `aria-label`s on the
quantity stepper's +/− buttons and the quantity input itself, and `role="status" aria-live="polite"`
on the log-sale form's message line so a screen reader announces the result of a submission.
Also restates and reuses the Round 14 `[hidden]`-attribute lesson: the new `#cap-warning` element
is deliberately given **no unconditional `display` CSS property at all** (only color/border/padding/
font rules), so the browser's own `[hidden] { display: none }` UA-stylesheet default is never
overridden and no explicit `.cap-warning[hidden] { display: none; }` rule is even needed this time —
simpler than the Round 14 fix, and worth remembering as the preferred approach going forward:
avoiding an unconditional `display` rule on a `hidden`-toggled element in the first place is easier
than remembering to add the override after the fact.

**Verification, in order**: `python manage.py check` (clean); a scripted Django-test-Client script
covering both new endpoints end to end — `api_log_sale` → `api_cancel_sale` (delete confirmed,
double-cancel refused with a clean 400), a non-director blocked from `api_review_sale` (302
redirect, not a 500/403 crash), a director approving and rejecting sales (status flips confirmed,
double-review refused with a clean 400), the pre-existing daily-cap rejection re-confirmed
unchanged, and both touched pages (`/dashboard/`, `/director/`) confirmed to render the new markup —
this is what caught the missing-import bug above; then a Playwright pass covering the live
point-preview updating as quantity/product change, the cap-warning appearing and disabling submit
past the daily limit, a real log→cancel round trip, Escape actually closing the modal (this is what
caught the focus-trap bug above), the Director queue's Approve button removing a row and updating
both stat chips live, and a 390×844 mobile screenshot of the log-sale modal. One incidental
discovery during the Playwright pass, not a bug: a freshly re-seeded demo account can have queued
"on-load celebration" mystery boxes/achievements (existing Round 6/8 behavior, unrelated to this
round's changes) that visually block modal interaction until dismissed — the verification script
was adjusted to close any of those first rather than treating it as a regression.

**Separately, same day: the user's own deployment workflow changed.** Previously the user pushed to
GitHub entirely through the browser's drag-and-drop web uploader (see the Round 17-adjacent
deployment section above), which doesn't honor `.gitignore`. The user has since cloned the real repo
fresh via VS Code's `Git: Clone`, copied the working project files across (including `.gitignore`,
excluding `venv/`/`db.sqlite3`/`__pycache__/`/`staticfiles/`), set up a fresh local `venv`, and is
now committing/pushing through VS Code's Source Control panel — confirmed working end to end (a
53-changed-file commit/push landed cleanly). Render auto-redeploys on every push to `main`; no
manual Render-side action is needed for a normal update. This is now the user's standing workflow
for every future round: edit locally in VS Code → Source Control → stage → commit message → Commit
→ Sync Changes/Push, and Render picks it up automatically within its usual build time.

## Round 20 in detail (2026-09-03) — login page: the role tab is now a real permission check

Since Round 12, the three login-page role tabs (Agent / Analyst / Director) were an explicit,
documented design choice: purely cosmetic, swapping only the headline/demo-credentials copy, while
the actual post-login destination was always decided from the account itself
(`roles.get_user_role`), specifically so a mismatched tab click *couldn't* fake its way into a
portal it didn't belong to — see the Round 12 detail section and the old `roles.py` module
docstring, both of which spelled this out as a deliberate anti-spoofing decision. In practice this
reads as a bug from the outside: picking "Agent" and typing Director credentials in still opens the
Director portal, with no indication anything was mismatched. The user reported exactly this,
explicitly asking for the tab to gate which credentials are accepted. This round reverses that
design decision on the user's direct instruction — the tab is no longer just a preview, it's an
assertion that gets enforced.

**The enforcement itself.** `views.SpectrumLoginView` gained a `form_valid(self, form)` override
that runs *between* Django's own credential check (`AuthenticationForm.clean()`, unchanged) and the
point where a session actually gets established (`super().form_valid(form)`, which is what calls
`django.contrib.auth.login()`). `form.get_user()` returns the authenticated user object at this
point without having logged them in yet, so the role check happens before any session exists:
```python
def form_valid(self, form):
    user = form.get_user()
    selected_role = self.request.POST.get("selected_role") or roles.ROLE_AGENT
    actual_role = roles.get_user_role(user)
    if selected_role != actual_role:
        ...
        form.add_error(None, "...")
        return self.form_invalid(form)
    return super().form_valid(form)
```
A mismatch never logs the account in at all, not even briefly — `form_invalid(form)` just
re-renders the login page with an error, the same page the user would see for a wrong password.
Missing/unrecognized `selected_role` defaults to `"agent"` (never treated as a wildcard that skips
the check), so a login POST that omits the field entirely — a stripped-down client, a replayed
request — still gets the enforcement rather than an accidental bypass.

**Wiring the tab's value into the request.** The three role-tab buttons already carried
`data-heading`/`data-subtext`/`data-demo-user`/`data-demo-role` attributes for the existing cosmetic
copy-swap; each also gained a `data-role="agent"/"analyst"/"director"` attribute (the actual role
slug, distinct from the human-readable `data-demo-role` label already there). A new hidden
`<input type="hidden" name="selected_role" id="selected-role">` sits in the login form; `login.js`'s
existing tab-click handler (`applyTabCopy`) now also sets `selectedRoleField.value = tab.dataset.role`
alongside the copy swap it already did — no new event listener needed, just one more line in the
function that already ran on every tab click.

**Keeping the page consistent after a rejected login.** A naive version of this fix would reload the
login page after a mismatch with the tabs reset back to their hardcoded default (Agent active,
"Welcome back" heading) — technically correct (the error message names the real account type) but
visually confusing, since the tab the user actually had selected would silently vanish. Fixed by
having `SpectrumLoginView.get_context_data` pass `selected_role` (from `POST` on a failed submit,
defaulting to `"agent"` on a plain `GET`) into the template, and making the tab's `active` class,
`aria-selected`, the heading/subtext block, and the demo-credentials line all render from that
context variable server-side (via `{% if selected_role == '...' %}` blocks) rather than only from
the hardcoded Agent-flavored markup `login.js` used to patch after the fact. This means the page is
correct on first paint even before `login.js` runs, and a role-mismatch reload keeps showing
whichever tab the user actually had selected, with the matching heading/demo line, not a reset to
Agent.

**The error message names the tab exactly as printed on screen.** `roles.py` already had
`ROLE_LABELS` (fuller labels — "Field Agent", "Incentive Analyst" — used elsewhere, e.g. the
topbar's role badge). Using those directly in "switch to the ___ tab" would have said "switch to
the Field Agent tab," which doesn't match what the tab actually says ("Agent"). Added a second,
narrower `ROLE_TAB_LABELS` dict (`{"agent": "Agent", "analyst": "Analyst", "director": "Director"}`)
used only for naming the tab in this one message, so the instruction matches the UI verbatim —
caught and fixed during this round's own Playwright pass, not assumed correct from reading the
code (see verification below).

**Both stale design-rationale comments were updated, not just the behavior.** `roles.py`'s module
docstring and `views.SpectrumLoginView`'s class docstring both explicitly documented the old
"tabs are cosmetic, routing always follows the real account" reasoning as intentional — leaving
those in place after reversing the behavior would have misled whoever reads this code next into
"fixing" it back. Both rewritten to describe the current (enforced) behavior and explicitly note
that it supersedes the earlier decision, rather than silently going stale the way a couple of other
comments in this project have before (see lessons list).

**Verification, in order**: `python manage.py check` (clean); a scripted Django-test-Client script
covering all nine login combinations that matter — each of the three demo accounts logging in with
its own correct tab (all three succeed and land on the right portal); director/agent/analyst
credentials each attempted under a *wrong* tab (all three rejected, and — checked explicitly, not
assumed — the session was never established: a follow-up request to that role's own portal still
redirects to `/login/`, not through); a genuinely wrong password still rejected as before
(regression check); and a POST that omits `selected_role` entirely still rejects director
credentials rather than defaulting past the check. Then a Playwright pass: confirmed the error
banner's exact wording for both mismatch directions (this is what caught the `ROLE_LABELS` vs.
`ROLE_TAB_LABELS` wording mismatch above — the first version said "switch to the Field Agent tab"
next to a tab literally labeled "Agent"), confirmed the previously-selected tab (and its
heading/demo-line) stays active after a rejected login instead of resetting to Agent,
and confirmed a correct tab+credentials login still lands on the right portal end to end
(Director tab + Director creds → `/director/`; Agent tab + Agent creds → `/dashboard/`).

## Round 21 in detail (2026-09-03) — gamification: streaks, spin wheel, weekly challenges, XP levels

User asked directly: "Can you make some gaming functionality based on goal and achievement which
will keep agent to sell more and log in / unique, interactive / better tracking dashboard." Used
AskUserQuestion (multi-select) to scope which mechanics to build rather than guessing at "unique,
interactive" — offered four concrete directions; the user picked **all four**: daily streak +
spin-the-wheel, a weekly challenge board, XP levels layered on tiers, and a unified "Game Center"
tracking hub. Built as a fifth new dashboard tab that consolidates all of it (plus a live view of
the existing login streak) rather than scattering the new mechanics across the existing tabs.

**Design decisions made before writing code, and why.** The existing points system already has
several layers (tier progress — incentive-scoped — plus achievements, bonus tasks, and mystery-box
bonuses, all folding into `lifetime_points()`), so the main risk with "add gamification" was
creating a second, inconsistent point total or duplicating an existing mechanic under a new name.
Three decisions kept the new mechanics additive rather than redundant:
- **Level is lifetime-points-scoped, Tier stays incentive-scoped.** `tier_progress()`/
  `agent_points()` deliberately only count the *current* incentive's approved `Sale.points_earned`
  and reset every period; the new XP Level reads `lifetime_points()` (never resets) so it answers a
  genuinely different question — "how far have you come, overall" vs. "how are you doing this
  incentive" — rather than being a reskinned copy of the tier ring.
- **Every new point source feeds the existing `lifetime_points()` aggregate**, not a separate
  total. Spin-wheel points (`AgentSpinResult`) and weekly-challenge points
  (`AgentWeeklyChallengeCompletion`) were added into the same `Sum(...)` chain that already combines
  approved sales, bonus-task points, and mystery-box points — so the stat-strip's existing
  "lifetime pts"/"cash earned" tiles, and the new Level card, automatically reflect a spin or a
  challenge the instant it's earned, with no second code path to keep in sync.
- **The weekly challenge board reuses the exact `ACHIEVEMENTS`/`BONUS_TASKS` pattern** — a fixed
  catalog of plain Python dicts in `insights.py`, each with a `check(...)` callable, a `sync_*`
  function that persists newly-qualified entries and returns only what's new *this call* (for
  celebration), and a `*_context` function that returns the full shelf for rendering — rather than
  inventing a new architecture. The only structural difference: challenges reset weekly on the ISO
  calendar (`_iso_week_bounds()`) instead of per-incentive, so completions are keyed on
  `(agent, iso_year, iso_week, key)` instead of `(agent, incentive, key)`, and each `check` takes a
  week's date range instead of an incentive.

**New models** (`agent_portal/models.py`, migration `0006_agentprofile_last_seen_level_and_more`):
- `AgentProfile` gained three fields: `streak_freezes` (banked "skip a missed day" tokens, capped
  at `MAX_STREAK_FREEZES = 3`), `last_spin_date` (today's-spin-already-used check without a query),
  and `last_seen_level` (drives the level-up celebration's "newly earned this call" pattern, same
  idea as achievements/tasks).
- `AgentLoginDay` — one row per `(agent, date)` actually logged in, plus a `used_streak_freeze`
  flag. This is what draws the streak calendar heatmap; the running counters on `AgentProfile`
  can't answer "which specific days," only "how many in a row."
- `AgentSpinResult` — one row per `(agent, date)`, unique together (enforces "one spin a day" at
  the database level, not just in the view), storing which prize key was won and its points.
- `AgentWeeklyChallengeCompletion` — one row per `(agent, iso_year, iso_week, key)`, mirroring
  `AgentTaskCompletion`'s shape.

**Daily streak + streak freeze** (`signals.py`, extending the existing `update_login_streak`
receiver on `user_logged_in`): a missed single day no longer resets the streak to 1 if a freeze is
banked — the freeze is spent automatically, the skipped day is backfilled into `AgentLoginDay` with
`used_streak_freeze=True` (so the calendar shows *why* the streak survived, not just that it did),
and a freeze is earned automatically every `STREAK_FREEZE_MILESTONE = 7` days of unbroken streak, up
to the cap. **A real bug caught by this round's own backend test, not visual inspection**: the first
version computed the day to backfill as `gap_day = today - timedelta(days=2)` (reusing the variable
that correctly identifies *when `last_login_date` must be* for a one-day gap) instead of `yesterday
= today - timedelta(days=1)` (the day that was actually *skipped*) — so a freeze-covered gap was
being recorded on the wrong calendar day. Caught immediately by a scripted test that drove the
signal across a real 9-day sequence (7-day streak → skip a day → freeze-covered login → confirmed
`current_login_streak` continued to 8 → asserted the *specific* `AgentLoginDay` row for the skipped
day existed with `used_streak_freeze=True`) rather than only checking the streak counter, which
would have passed even with the date bug in place. Fixed by renaming/reusing the already-correct
`yesterday` variable for the backfill instead of the `gap_day` threshold variable, and re-verified
the same 9-day sequence end to end.

**Spin the wheel** (`insights.py` — `SPIN_PRIZES`, `spin_the_wheel()`, `spin_wheel_context()`; new
`api_spin_wheel` view/URL): a fixed, weighted prize catalog (mostly small point prizes, a rare
streak-freeze prize, a very rare jackpot), `random.choices(..., weights=...)` picking one per spin.
`AgentSpinResult`'s unique `(agent, date)` is the actual "once a day" enforcement — `spin_the_wheel()`
re-checks it itself (not just relying on the view's pre-check) so a race can never award two spins
in one day. The wheel is drawn client-side (`dashboard.js`) as a canvas pie chart from the *exact
same* `SPIN_PRIZES` list the server picks against (passed down as `spinPrizesJson`), so the visual
wheel and the server's random pick can never drift out of sync; landing on the correct segment is
pure CSS-transform rotation math (compute the target segment's mid-angle, rotate to put it under a
fixed top pointer, plus a few extra full turns for effect — skipped under
`prefers-reduced-motion: reduce`, which jumps straight to the result instead), not a second
"guessed" animation. **Superseded in Round 22, same day — removed entirely and replaced with the
Clean Streak mechanic below, on direct user request ("not like spin").**

**Weekly challenge board** (`insights.py` — `WEEKLY_CHALLENGE_TEMPLATES`, `_select_weekly_challenges()`,
`sync_weekly_challenges()`, `weekly_challenges_context()`; new `templates/agent_portal/
_weekly_challenges.html` partial, styled by reusing the existing `.task-card` family of classes
verbatim rather than inventing new CSS): 3 of 6 fixed challenge templates are live each ISO week,
chosen by `random.Random(f"{iso_year}-W{iso_week}").sample(...)` — seeded only by the week number,
not per-agent, so every agent sees the identical 3 challenges (a shared "event" feel) with zero
extra "which challenges are live" table to maintain.

**XP levels** (`insights.py` — `LEVEL_XP_STEP`, `LEVEL_TITLES`, `level_progress()`,
`sync_level_up()`): a triangular-number curve (level *N* needs `100 * (N-1) * N / 2` cumulative
lifetime points, so early levels come fast and later ones take real sustained selling), with five
title bands (Rookie → Rising Star → Pro Closer → Ace → Legend). `sync_level_up()` follows the exact
same "persist + return only what's new this call" pattern as achievements, so the level-up
celebration fires exactly once per level crossed, the moment it's crossed, whether that's from a
sale, a spin, or a weekly challenge.

**Wiring into `views.dashboard()`**: `sync_weekly_challenges()` and `sync_level_up()` were added to
the existing chain of `sync_*` calls that **must run before** `insights.build_dashboard_context()` —
the same ordering rule this project has enforced since the Round 8 bug (`lifetime_points`/
`lifetime_cash`, and now `level_progress`, all read off state these sync calls just wrote) — verified
directly by a scripted test that reloads `/dashboard/` twice in a row and confirms no duplicate
awards or crashes (the sync calls are idempotent once nothing new qualifies).

**The "Game Center" tab** (`dashboard.html`, reusing the existing `.tab-btn`/`.tab-panel` mechanism
verbatim — no JS tab-switching changes needed): a Level card (progress bar reusing
`.progress-track`/`.progress-fill` from the Goals tab, not a new bar style); a Streak card (a 35-day
calendar heatmap of small dots — green/blue/gray for logged-in/freeze-covered/missed — plus the spin
wheel and its Spin button); and a Weekly Challenges card. All three fit on one scroll on desktop and
stack cleanly on mobile (verified at 390px), reusing the existing `.grid-2` responsive breakpoint
rather than a new one. New CSS (`style.css`) — `.level-card`, `.streak-calendar`/`.streak-dot`,
`.spin-wheel-*` — deliberately reuses the existing `--gold`/`--silver` tokens for two of the wheel's
segment colors (already used for confetti) rather than adding new palette entries, and every new
transition/animation is guarded under `prefers-reduced-motion: reduce`, consistent with the rest of
the app. **The Streak card's spin-wheel block, and the 2-card grid it sat in, were both replaced in
Round 22 — see that round's detail.**

**Wiring into `dashboard.js`**: a new `unlockWeeklyChallenges()` function mirrors the existing
`unlockTasks()` exactly (same `.task-card`/`data-key`/pill-swap DOM update, since the weekly
challenge markup is the identical `.task-card` template); a new `celebrateLevelUp()` finally wires
up `playLevelUpSound()`, which had been dead code (defined, zero call sites) since an earlier round.
Both are added into the existing "on-load celebration" block alongside achievements/tasks/mystery
boxes, so a level-up, a newly-completed weekly challenge, a badge, and a bonus quest earned in the
same request all queue through the same toast system rather than stepping on each other. Spinning
the wheel live-updates the stat-strip's lifetime-points/cash tiles, the Level card, and the streak-
freeze count directly from the `api_spin_wheel` response, with no full page reload.

**Verification, in order**: a scripted backend test (`insights.level_progress`/`_level_for_points`
curve math; `sync_level_up` fires exactly once per level crossed; `spin_the_wheel` enforces one
spin/day and `spin_wheel_context` reflects the day's result; weekly-challenge selection is
deterministic for a given week; the streak-freeze bug above, caught and re-verified across a full
9-day sequence) — run before any template/view work was touched, catching the streak-freeze date
bug immediately; `python manage.py check` (clean); a scripted Django-test-Client pass covering
`/dashboard/` loading with all the new context wired in, reloading idempotently, `api_spin_wheel`
awarding a prize then refusing a second same-day spin, the spin limit being per-agent (not global),
and a non-agent account (Director) being refused cleanly rather than crashing; a Playwright pass
confirming the Game Center tab renders, the streak calendar draws exactly 35 dots, the wheel canvas
actually paints non-transparent pixels, all 3 weekly challenge cards render, a live spin animates
and reveals a result matching the server's response, and that result persists correctly across a
page reload (server-rendered "already spun today" state matches what the live spin just showed);
a 390×844 mobile screenshot confirmed the three new cards stack cleanly with no overflow. Also
re-ran the Round 20 login-role regression test unchanged (still all passing) since this round didn't
touch login/role code, to confirm no cross-round regression.

## Round 22 in detail (2026-09-03) — Clean Streak replaces the spin wheel; Analyst/Director incentive comparison

Same day as Round 21, the user came back with three more asks in one message (typos corrected
here, quoted below in the Key-decisions entry above): (1) replace the spin wheel with something
"unique, not like spin" — a mechanic based on goals/tasks achieved and tied to the existing sale
approval/rejection workflow; (2) an Analyst view comparing incentives against each other to see
which is more effective/revenue-generating; (3) something for the Director portal too, left open
("som e better unqiue").

**1. Clean Streak — a fully deterministic replacement for the spin wheel.** The core design
choice was to make the new mechanic answer exactly what the user asked for — "based on goal
acheived or tasks achieve related to that approval rejection" — by counting consecutive *reviewed-
positive* events rather than anything random. `Sale` gained a `reviewed_at` field (nullable
`DateTimeField`, set by both `views.api_review_sale` and `SaleAdmin`'s bulk actions — the latter
needed `reviewed_at=timezone.now()` added directly to its `queryset.update(...)` calls, since bulk
`update()` bypasses `save()` and any override on it). `insights._agent_positive_timeline(agent)`
merges three event streams into one list sorted most-recent-first: approved/rejected sales
(ordered by `reviewed_at`, not `sold_at` — the streak is about *when a Director acted*, not when
the agent submitted it), completed `AgentTaskCompletion` rows, and awarded `AgentGoalBonus` rows.
`clean_streak_progress(agent)` walks that list from the top, counting consecutive positive events
until a rejected sale (or the end of history) stops it — no `random` call anywhere in this
mechanic, directly satisfying "not like spin."

**Milestones are a ledger, not a one-time unlock — a deliberate divergence from this project's
usual "earn once" pattern.** Every other award model here (`AgentAchievement`, `AgentTaskCompletion`,
`AgentGoalBonus`) is effectively earn-once, enforced via `unique_together` or a `get_or_create`.
`AgentCleanStreakAward` is intentionally **not** unique — a streak can legitimately be earned,
broken, and re-earned, and each crossing is meant to be its own celebratable event that adds again
to lifetime points (a "combo meter" feel). `CLEAN_STREAK_MILESTONES = [3, 5, 10, 15, 25, 40]` with
points `{3:10, 5:20, 10:40, 15:60, 25:100, 40:200}`. Bookkeeping for "which milestones have already
been paid out on the current run-up" lives on two new `AgentProfile` fields —
`highest_clean_streak_awarded` and `last_clean_streak_seen` — rather than re-scanning the ledger on
every check; `insights.sync_clean_streak(agent)` resets `highest_clean_streak_awarded` to 0 the
moment it detects the live streak has *dropped* since the last check (i.e. a break happened), so
the same milestones become earnable again on the next run-up. A third field,
`longest_clean_streak_ever`, was added alongside the other two (before the migration was generated,
so it's one clean migration rather than two) specifically so the Game Center card can show an
all-time best that survives a break, since the other two bookkeeping fields deliberately don't.

**Wiring**: `sync_clean_streak(agent)` was added into `views.dashboard()`'s existing pre-
`build_dashboard_context()` sync chain (same ordering rule this project has enforced since Round 8 —
`lifetime_points()` now also sums `AgentCleanStreakAward.points_awarded`, so a milestone crossed
this exact request has to be persisted before the context that reports lifetime points is built).
`build_dashboard_context()` swapped its old `"spin": spin_wheel_context(agent)` entry for
`"clean_streak": clean_streak_progress(agent)` and a new `"clean_streak_feed"` entry
(`clean_streak_feed()`, the ledger's most recent payouts — mirrors `recent_sales_for_agent`'s
shape). `api_spin_wheel` and its URL were deleted outright, not just deprecated — the user
explicitly asked for the mechanic gone, not hidden. `api_review_sale` now sets `sale.reviewed_at =
timezone.now()` alongside the status flip.

**Game Center card layout**: the old 2-card `.game-center-grid` (Streak+Spin combined into one
card, Weekly Challenges in the other) became a 3-card `.grid-3` (`repeat(auto-fit, minmax(280px,
1fr))`, new CSS rule): Daily Streak (unchanged, just the spin block removed from inside it), a new
Clean Streak card (current count, a `.progress-track`/`.progress-fill` bar toward the next
milestone, a short "no luck involved" explainer, and a `.mini-row`-based recent-awards feed reusing
the same partial-row styling the Analyst/Director portals already use), and Weekly Challenges
(unchanged). `dashboard.js`'s entire spin-wheel section (canvas drawing, rotation math, the click
handler, `revealSpinResult`) was deleted — including `prefersReducedMotion()`, which existed only
for the wheel's animation and had no other callers — and replaced with a much smaller
`celebrateCleanStreaks(awards)` function that fires from the same on-load celebration block as
achievements/tasks/level-ups (toast per milestone + a new row prepended to the feed + confetti),
since milestones are detected server-side at page load rather than through a user-initiated click
the way a spin was.

**2 & 3. Incentive comparison, shared by Analyst and Director.** New
`insights.incentive_comparison_rows()` ranks every incentive that has at least one approved sale by
**effectiveness = total points ÷ participating agents ÷ period days elapsed** — deliberately not
raw total points, which would just reward whichever incentive ran longest or had the most agents on
it and wouldn't actually answer "which one worked." `estimated_value` reuses the existing
`CASH_PER_POINT` placeholder conversion (already used by `total_cash_earned()`) rather than
inventing a second rate, since there is still no real per-sale dollar/price field anywhere in this
data model (`Product` only has `base_points`) — labeled "est. value" in the UI, with a tooltip
spelling out the estimate and the rate, not "revenue," consistent with this project's standing
practice of flagging placeholder numbers rather than presenting them as real. A shared partial,
`templates/agent_portal/_incentive_comparison.html`, renders the ranked rows (reusing
`.goal-item`/`.progress-track`/`.progress-fill` rather than a new table component) and is included
from both `analyst_dashboard.html` and `director_dashboard.html` so the two portals can never drift
out of sync on how this is computed or displayed.

**A fairness caveat added after noticing the metric could mislead on its own seed data**: a few
days into a brand-new incentive, a small `period_days` denominator can make `effectiveness` look
inflated relative to incentives with a full period already behind them (confirmed directly in this
round's own seeded data — the just-started September incentive showed ~40+ pts/agent/day against
~4-5 for the two completed prior months, purely because it had only 3 elapsed days to divide by).
Rather than hide this or silently exclude fresh incentives from the ranking, `incentive_comparison_
rows()` flags any current incentive with `period_days < 7` as `early_data`, and the shared partial
renders an "early data" pill with a tooltip explaining why the number may look inflated — the
ranking stays honest about a comparison that isn't fully fair yet, instead of presenting a
misleading #1 with no caveat.

**Director-specific additions, on top of the shared comparison table** (`director_overview()`
already covers the Round 12/19 baseline — approval queue, top performers — unchanged): `insights.
review_turnaround_stats(incentive)` — average hours between `Sale.sold_at` (submission) and
`reviewed_at` (review) across the period's reviewed sales, plus an approval-rate percentage;
returns `None` when nothing's been reviewed yet, rather than a misleading 0. `insights.
top_clean_streaks(limit=5)` — a live-computed mini-leaderboard of agents with the longest current
Clean Streaks, giving Directors direct visibility into who has approval momentum right now, tying
this round's #1 and #3 asks together (approvals feed streaks; streak visibility belongs to the
people doing the approving). Both surfaced as two new stat chips (avg. turnaround, approval rate)
in the existing `.stat-strip`, plus a new "Top Clean Streaks right now" card sitting beside the
incentive comparison table in a new `.grid-2` section, all fed through `views.director_dashboard()`.

**Verification, in order**: `python manage.py check` after the model changes, then
`makemigrations`/`migrate` (migration `0007_remove_agentprofile_last_spin_date_and_more` —
removes `last_spin_date`, adds the three new `AgentProfile` fields and `Sale.reviewed_at`, creates
`AgentCleanStreakAward`, deletes `AgentSpinResult`); a scripted backend test covering the Clean
Streak mechanic specifically — 3 approved sales in a row correctly compute a streak of 3 and award
exactly the 3-streak milestone (+10 pts, confirmed via `sync_clean_streak`'s return value, not just
inferred from the profile field), a rejected sale immediately after drops the live streak back to 0
and resets `highest_clean_streak_awarded` to 0 while `longest_clean_streak_ever` stays at 3
(confirming the "record persists through a break, current-run bookkeeping does not" design),
`lifetime_points()` reflects the milestone award, and `api_review_sale` sets `reviewed_at` on
approval; a scripted Django-test-Client pass confirming `api_spin_wheel` now 404s (route actually
removed, not just unused), `/dashboard/` renders with no `spin-wheel` markup anywhere in the page
and the new `clean-streak` markup present, and both `/analyst/` and `/director/` render their new
comparison sections without error; then a full re-seed (`seed_data --flush`, extended this round —
see below) and a Playwright pass at desktop and 390px mobile confirming the 3-card Game Center
layout, the Clean Streak card's progress bar and milestone feed, the Analyst comparison table
(including the "early data" pill rendering correctly), and the Director page's four new pieces
(turnaround/approval-rate stat chips, comparison table, top-streaks card) all render cleanly with
no overflow at either width.

**`seed_data.py`'s `_seed_sales()` was extended, not just left alone, since the new features need
real data to demo.** Previously every seeded sale was created `STATUS_APPROVED` with no
`reviewed_at` and a 0% rejection rate anywhere in demo data — meaning a fresh `seed_data` run would
have shown a perpetual 100% approval rate, an unbroken Clean Streak with nothing to reset it, and no
review-turnaround numbers at all (the field would be null on every row). Now: each agent's planned
sales are sorted newest-first and, for the *current* incentive only, the top 1-2 have a 60% chance
each of staying `STATUS_PENDING` (unchanged behavior — keeps the Director's queue non-empty in a
fresh demo); every other sale gets a `reviewed_at` timestamp `sold_at` plus a random 15
minutes–48 hours (capped at "now"), and an 8% chance of `STATUS_REJECTED` instead of approved
(`SEED_REJECTION_RATE`) — enough to give the Clean Streak mechanic actual breaks to show and the
approval-rate/turnaround stats non-trivial numbers, without dominating the demo.

## Round 23 in detail (2026-09-03) — Goals tab redesigned as "Signal Spectrum" bars

The user described a teammate's separate build in detail: seed a board with one ball per goal
unit, sink a ball into a corner pocket on every approved sale, so the board visually empties as
the agent progresses. The instruction was explicit — "i want to build like gaming but in different
idea" — so the goal here wasn't a reskin of that same board/pocket shape, it was a genuinely
different mechanic answering the same underlying need (a satisfying, game-like way to see
per-product goal progress).

**Design choice, and why it's not just a repaint of the existing progress bar.** `product_goal_
progress(agent, incentive)` (unchanged data contract — still returns `target`/`sold`/`remaining`/
`pct`/`complete` per goal) gained one new field: `spectrum_bars`, a list of `{lit, height}` dicts,
one per unit of the goal (capped — see below). `lit` is real data (sold vs. target, identical math
to `pct`); `height` is cosmetic, drawn from a small fixed repeating cycle
(`GOAL_SPECTRUM_BAR_HEIGHT_CYCLE`) rather than a flat staircase, so the bars actually read as a
broadcast spectrum-analyzer/EQ meter — deliberately picked because this app is literally named
Spectrum, which the ball-and-pocket board had no equivalent tie-in to. Same discipline as Clean
Streak's "not like spin" requirement in Round 22: no `random` call anywhere in this function, so
the same goal state always renders identically — the *shape* just isn't a boring flat bar anymore.

**Capping, since a real target could exceed a sane number of DOM bars.** Seeded data uses small
targets (3-6 units per goal — see `seed_data.py`'s `IncentiveProductGoal.objects.get_or_create`),
so most goals render one bar per literal unit, same as the colleague's one-ball-per-unit board. For
robustness against a much larger target, `GOAL_SPECTRUM_MAX_BARS = 30` caps the bar count; beyond
that, each bar represents a proportional slice of the target rather than exactly one unit
(`_goal_spectrum_bars()`, scripted-tested directly: confirmed 2/5 → 5 bars/2 lit, 6/5 (over-target)
→ 5/5 lit i.e. clamped not overflowing, 0/4 → 4/0 lit, 40/100 → capped to 30 bars/12 lit, and a
defensive `target=0` → `[]` with no division error).

**Markup/CSS, not a new JS system.** `templates/agent_portal/_goals.html`'s old `.progress-track`/
`.progress-fill` bar (inside `.goal-item`) was replaced with a `.spectrum-meter` containing a row
of `.spectrum-bar` spans (height set inline from `--h`, lit state from a `.lit` class) plus a small
`.spectrum-antenna` beacon dot. `.progress-track`/`.progress-fill` themselves were left completely
untouched — they're still load-bearing for the Round 22 incentive-comparison table and the login
streak calendar, which explicitly reuse them (see those sections' own "reuses" comments), so this
round only stopped using them inside `_goals.html`, it didn't remove or restyle the shared classes.
New CSS (`style.css`): `.spectrum-meter`/`.spectrum-bars`/`.spectrum-bar` (lit = accent gradient, or
`--success` once `.goal-item` is `.complete`), a staggered `spectrum-bar-in` entrance animation
(`animation-delay: calc(var(--i) * 0.025s)`, replays every time the Goals tab is reopened since
`.tab-panel` toggles via `display: none` → `flex`, not just opacity — confirmed by reading
`.tab-panel`'s own CSS rather than assuming), and — only on a completed goal — a pulsing
`spectrum-pulse` animation on the lit bars plus `antenna-flash`/`antenna-ping` radar-style rings on
the beacon dot ("the meter goes live"), all added to the existing `@media
(prefers-reduced-motion: reduce)` guard. No JS changes were needed: the mystery-box popup
(`queueMysteryBox`, built in Round 6, unchanged) already celebrates the moment a goal newly
completes with its own toast/confetti, and the spectrum meter's `.live` state is just server-
rendered from `g.complete` on every load — so the two celebrations (mystery box = "you just did
it," meter = "here's the state now") complement each other without duplicating logic.

**Verification, in order**: a scripted check of `_goal_spectrum_bars()` (four cases above); `python
manage.py check` (no model/migration changes this round — `spectrum_bars` is computed, not stored);
a Django-test-Client render of `/dashboard/` for an agent with a mix of complete/in-progress goals,
asserting `spectrum-meter`/`spectrum-bar`/`spectrum-antenna` are present and no leftover `pool`
references exist anywhere in the page; a full re-seed; then a Playwright pass covering three cases
at desktop and a fourth at 390px mobile — an agent with a mix of 3 complete + 6 in-progress goals
(bars correctly blue/in-progress vs. green/glowing-antenna/complete, `6/4`-style over-target goals
correctly showing all bars lit rather than overflowing past the cap), an agent with zero complete
goals (all-dim antennas, no stray "on air" pills), and the same mixed case at mobile width — all
render with no horizontal overflow and no console errors traceable to this change (two unrelated
`ERR_TUNNEL_CONNECTION_FAILED`/404 console lines were also present before this round's changes and
are a sandbox network-proxy artifact, not an app regression — confirmed by grepping the page for
any external resource this round added, which is none).

## Round 24 in detail (2026-09-03) — Coverage Map: the Game Center's first real interactive element

**Superseded in Round 25, next day — removed entirely (function, template, CSS, all of it) and
replaced with the Signal Launch orbit below. The user's verdict was that a static grid that only
changes color isn't a game; see Round 25 detail for what replaced it and why.** Left here as a
historical record of what was tried and rejected, same as Round 21's spin wheel below.

The ask was open-ended — "is it possible to make game center more interactive or ay other idea
vissual game type" — so rather than guess, AskUserQuestion offered three concrete directions:
add interactivity to the existing three Game Center cards (click-to-expand history, flip-on-hover
badges), a "Network Builder" node/tower diagram, or a "Coverage Map" hex-grid territory concept.
User picked Coverage Map.

**Deliberately not a new data source — a new *shape* for data the app already computes.** Every
prior gamification round (Clean Streak in Round 22, Spectrum bars in Round 23) added its own new
aggregation logic. Coverage Map doesn't: `insights.coverage_map(goals)` takes
`product_goal_progress()`'s existing return value — the exact list `build_dashboard_context()`
already builds for the Goals tab — and groups it into "zones," one per product goal. Critically, a
zone's tiles *are* that goal's `spectrum_bars` list from Round 23, reused as-is rather than
recomputed; the only new numbers are the roll-ups (`total_target`/`total_sold` summed across every
goal, clamping each goal's contribution at its own target so an over-sold product can't inflate the
overall percentage past what it should be). This means the Goals tab's EQ meter and the Game
Center's Coverage Map can never silently disagree about whether a given product is covered — they
render from the identical `lit` booleans, just shaped differently (linear bars vs. hex zones).

**Interactive, not just decorative — the point of the round.** Every earlier gamification card
(streak calendar, Clean Streak count, weekly challenges, Spectrum bars) is read-only: state is
computed server-side and just displayed. Coverage Map's hex tiles are real `<button>` elements
(not `<span>`s), event-delegated on `#coverage-map-grid` in `dashboard.js` rather than one listener
per tile (same delegation pattern as the Round 19 cancel-submission handler on
`#recent-sales-list`). Clicking any tile in a zone updates a `#coverage-detail` line with that
zone's product/sold/target/points, and re-triggers a `zone-pulse` CSS flash on that zone (a forced
reflow — `void zone.offsetWidth` — before re-adding the class, so clicking the *same* zone twice in
a row still replays the animation instead of being a no-op). Being real buttons also means the map
is keyboard-reachable (Tab + Enter/Space activates a tile) without any extra work, not just
mouse/touch.

**Visual design**: hex tiles via `clip-path: polygon(...)` on a fixed-size button, unlit = 
`var(--border)`, lit = the same accent gradient as the Round 23 spectrum bars, lit-and-zone-complete
= `var(--success)` with a soft glow — same color language as everywhere else progress is shown in
this app, just a new shape. Zones stagger-fade in on tab open (`coverage-zone-in`, delayed by a
`--zi` custom property per zone, same staggering technique as Round 23's bar entrance). An overall
`{{ coverage_map.overall_pct }}%` figure animates via the existing `animateNumber()` helper (added
to the same on-load count-up list as `lifetime-points`/`units-remaining` — no new animation code).
When every zone is complete (`coverage_map.fully_covered`), the whole card gets a `.full-coverage`
class: every lit tile pulses continuously (`hex-pulse`, scale + glow) and a "📡 Full coverage —
every zone on air" pill appears — verified live (see below) to coincide with the existing mystery-
box popup and confetti (built Round 6), since the goal that completes the *last* zone is the same
goal event that already triggers that celebration. **Deliberately no new celebration was added
here** — duplicating it would just be two popups fighting for attention on the same event.

**Verification, in order**: a scripted check of `coverage_map()` against hand-built goal dicts
(2 zones, 1 complete/1 partial → correct `zones_complete`/`overall_pct`/`fully_covered`; an empty
goal list → zeroed-out result, no division error); `python manage.py check` (no model/migration
changes — `coverage_map` is computed, not stored); a Django-test-Client render of `/dashboard/`
confirming `coverage-map-grid`/`coverage-zone`/`hex-tile`/`coverage-pct`/`coverage-detail` markup is
present; a full re-seed; a Playwright pass covering three real states — a mixed agent (4 of 9 zones
complete, 57% covered), an agent with zero complete zones (all-blue, no green rings, no "full
coverage" pill), and a scripted **click** on an actual rendered hex tile confirming
`#coverage-detail` updates to the exact expected string ("Sports Add-On — 3/5 covered · 15 pts
each") — not just that the markup exists, that the interaction actually works; and, to see the
100%-covered state at least once, a one-off backend script that approved enough sales for one test
agent to complete every zone, confirming `fully_covered` renders all-green pulsing tiles and — as
predicted above — the existing mystery-box/confetti/level-up celebrations fired on their own,
without any Round-24 code triggering them. Both desktop and 390px-mobile screenshots (mixed-state
agent) showed no horizontal overflow, the map reflowing to a 2-column layout on mobile via the
existing `auto-fill, minmax(140px, 1fr)` grid — no mobile-specific CSS needed.

## Round 25 in detail (2026-09-04) — Signal Launch: Coverage Map rejected, replaced with real motion

**Superseded in Round 26, same day — removed entirely (function, template, CSS, JS, all of it) and
replaced with Tower Build.** The satellite/orbit mechanic below was fully built, tested, and
verified working exactly as designed — the rejection that followed was on the theme itself ("any
other idea apart from satellite i dont think this impressive"), not a bug in the implementation.
This section is kept for the record of what was tried and why (the reasoning about "movement" as
the actual missing ingredient still holds and directly informed Tower Build); see "Round 26 in
detail" below for what replaced it.

Round 24 shipped, got tested, and the user came back unimpressed — not with a bug, with the whole
premise: a hex grid that silently changes color when data changes isn't a "game," it's a chart with
a different shape. The reference point they gave was specific and worth taking literally: a
colleague's separate build has a pool-ball board where a ball visibly *travels* and sinks into a
pocket the moment a sale is approved — an actual kinetic event, not a redraw. The instruction was
equally specific: take the idea (movement tied to a real event), not the mechanic itself ("dont do
same").

**What "movement" means here, concretely — two distinct kinds, both real, neither literally the
ball-in-pocket mechanic.** (1) A one-time *launch* animation the moment a satellite is newly earned:
starts small and near the tower, arcs out to its resting orbit slot over ~0.85s with an overshoot
easing (`cubic-bezier(.34, 1.56, .64, 1)`) for a satisfying "pop," fires once per newly-earned event,
staggered 350ms apart so several new wins launch as a little cascade rather than all at once. (2) A
*permanent* idle motion that has nothing to do with any single event: the whole ring of
already-earned satellites continuously orbits the tower (`orbit-spin`, 50s per revolution, runs
forever, never stops). Round 24's mistake wasn't lacking (1) entirely — the mystery-box popup
already provides a "something happened" moment elsewhere — it was having *no* (2): once a tile lit
up, it just sat there. A pool table with balls that never move once they're on it isn't a game
either; the ball's whole appeal is that it's traveling. Signal Launch has both: earning something
plays a visible moment, and the accumulated state itself never goes fully static again.

**Reused the event source, not the event handling.** `_agent_positive_timeline()` — built for Clean
Streak in Round 22, already the single source of truth for "what counts as a win" across this app
— is exactly what feeds Signal Launch too, filtered to positive events only (a rejection still
breaks the Clean Streak elsewhere on the same page; it doesn't get its own negative satellite
animation here, since one visual consequence per event type was judged enough — a satellite falling
out of orbit on a rejection was considered and deliberately not built, to avoid two different
widgets independently dramatizing the same rejection). This is the third distinct visual language
built on that one timeline: Clean Streak = "how many in a row," Spectrum bars (Round 23, per-goal)
= "how full is this goal," Signal Launch = "watch each one happen." All three can never disagree
about what actually counts as a win, since none of them maintain their own copy of that logic.

**New "have they seen this launch yet" bookkeeping — the one genuinely new piece of state.**
`AgentProfile.last_seen_positive_event_at` (nullable `DateTimeField`, migration
`0008_agentprofile_last_seen_positive_event_at`) is the high-water mark. `insights.
sync_signal_launch(agent)` compares the timeline's newest timestamp against it, advances it, and
returns *how many* events are new — not which ones, deliberately: since the timeline is always
sorted most-recent-first, the newly-earned satellites are always exactly the first N entries of
that same list, so dashboard.js just animates the first N `<button class="satellite">` elements it
finds in the DOM rather than needing a per-item "is this new" flag to survive the trip through the
template. First-ever sync for any agent (field is `None`) deliberately returns 0 and just marks
everything as already-seen, rather than replaying years of history launching at once the first time
this code runs on an existing account — confirmed directly: a scripted test seeded 2 approved sales
+ 1 rejected sale for a freshly-reset agent, called `sync_signal_launch` for the *first* time, and
got back 0 (not 2) with the rejected sale correctly producing no satellite at all; a *second* sync
after one more approved sale correctly returned 1.

**Positioning satellites on the ring is pure CSS, no JS layout math.** Each `.satellite` gets two
inline custom properties from the template, `--oi` (its index) and `--ocount` (total count), and a
single rule handles every satellite regardless of count: `transform: rotate(calc(360deg /
var(--ocount) * var(--oi))) translateY(-90px)`. The classic clock-hand trick — rotate first, then
translate along the now-rotated axis — places every satellite at an even angle around a fixed
90px-radius circle without any per-element JS positioning. A conscious simplification: satellite
icons are *not* counter-rotated to stay visually "upright" at every angle (that would need a second,
opposite-direction animation matched exactly to the ring's own spin duration) — an emoji tilted to
match its orbital position reads as an intentional "space" aesthetic rather than a bug, and skipping
it removed a whole layer of animation-timing fragility for a cosmetic difference nobody was going to
notice mid-spin.

**A real interaction-testing finding, not just a demo caveat**: Playwright's simulated pointer click
refused to click a `.satellite` at all ("element is not stable" — its actionability check polls the
element's bounding box across frames and refuses to click anything still moving between polls),
even though the rotation is slow enough (50s/revolution, a few px/sec at this radius) that a real
human clicking it is in no practical danger of missing. Verification switched to a programmatic
`el.click()` for the automated test — a legitimate DOM click, exercising the exact same listener a
real user's click would — rather than treating the tooling's strictness as a product problem to
"fix" by slowing down or pausing the orbit. Worth remembering if a future round adds more interactive
elements to something that's also continuously animating: Playwright's default click will need the
same workaround again.

**Verification, in order**: `python manage.py check` after the model change, `makemigrations` +
`migrate` (migration 0008, additive only — one nullable field, no data migration needed); the
scripted `sync_signal_launch` test above (first-visit suppression, rejected-sale exclusion, correct
new-count on a subsequent visit, idempotent zero on a third call with nothing new); `python
manage.py check` clean; a Django-test-Client render confirming `signal-launch`/`orbit-ring`/
`satellite`/`launch-tower`/`signal-launch-detail` markup present and every trace of `coverage-map`/
`coverage-zone`/`hex-tile` gone from the page; a full re-seed; a Playwright pass confirming 24
satellites render for a real seeded agent with no horizontal overflow at desktop or 390px mobile, a
programmatic click on a satellite correctly updating `#signal-launch-detail` to that satellite's
exact label, and — by priming one agent's `last_seen_positive_event_at` via one real dashboard load
then adding one fresh approved sale before a second load — confirming `state.newSignalLaunches`
correctly read `2` (the new sale plus one more event that had also landed), that exactly 2 elements
carried the `.launching` class ~150ms into that second page load (caught genuinely mid-animation,
not inferred), and that the class was correctly removed again (via the `animationend` listener)
within 1.5 seconds.

## Round 26 in detail (2026-09-04) — Tower Build: Signal Launch rejected, replaced with a falling-block tower

**Superseded in Round 27, same day — removed entirely (function, template, CSS, JS, all of it) and
replaced with Signal River.** Tower Build was fully built, tested, and verified working exactly as
designed — the rejection that followed was, again, not a bug: "still not impressive no action
happening, also confusing for viewer what is happening jaggered." The actual flaw, only visible in
hindsight from that specific wording: Tower Build is static almost all the time. It plays a real
0.6s fall animation when a block lands, then just sits there as a flat list of colored bars for
however long until the next win — which, on a screenshot or a glance, reads as nothing happening at
all. This section is kept for the record of what was tried and why; see "Round 27 in detail" below
for what replaced it and the specific design change (motion that never stops, not motion that
occasionally triggers) made to avoid repeating this exact mistake a third time.

Signal Launch shipped, tested exactly as designed, and the user rejected it anyway: "any other idea
apart from satellite i dont think this impressive." No bug, no misfire — the satellite/orbit theme
itself just didn't land. This was the second theme-level rejection in two rounds (Coverage Map,
then Signal Launch), and both times the mechanic had been built off a *general* instruction
("Some game movement," "is it possible to make game center more interactive") rather than a
concept the user had actually seen and approved first. Round 26 broke that pattern: instead of
picking a third theme solo, four concretely different concepts were laid out via AskUserQuestion —
Tower Build (blocks falling and stacking), Signal Sprint, Signal Strike, and Prize Grab — and the
user chose before any code was written. Tower Build won.

**What changed and what didn't.** The event source, the "what counts as a win" logic, and the
new-since-last-visit bookkeeping are all identical to Signal Launch — only the visual vocabulary on
top changed. `_agent_positive_timeline()` (Round 22, Clean Streak) is still the one place that
decides what a "win" is; Tower Build reads it the same way Signal Launch did, filtered to positive
events only, for the same reason (a rejection breaks the Clean Streak elsewhere on the page rather
than getting its own negative animation here — one visual consequence per event type). This is now
the fourth distinct visual language built on that single timeline: Clean Streak = "how many in a
row," Spectrum bars (Round 23) = "how full is this goal," and now Tower Build = "watch it stack
up." `AgentProfile.last_seen_positive_event_at` (added in Round 25) is reused completely unchanged
— same nullable high-water-mark field, same first-sync-marks-everything-seen behavior, same
"newest N entries in the most-recent-first list are the new ones" trick that lets dashboard.js
animate the first N DOM elements with no per-item flag from the server. No new migration was needed
for this round at all — `sync_tower_build()`/`tower_build_context()` are direct renames of
`sync_signal_launch()`/`signal_launch_context()` (satellites → blocks, `SIGNAL_LAUNCH_MAX` (24) →
`TOWER_BUILD_MAX` (18, sized down for vertical space instead of a ring's circumference), the
`"satellites"` context key → `"blocks"`).

**What's genuinely new is the layout and the motion.** Signal Launch needed real trigonometry — a
clock-hand rotate-then-translate trick — just to place satellites evenly around a circle. Tower
Build needs none of that: blocks render in a plain `flex-direction: column` stack
(`.tower-stack`), and because the server already emits the timeline most-recent-first, the newest
block is simply the *first* DOM child — no reversal in template or JS. The container
(`.tower-build`) uses `justify-content: flex-end` so the whole stack anchors to the bottom and
visibly grows upward as more blocks accumulate, with a `.tower-base` foundation rendered beneath
it. Each block is colored by event kind (sale = blue accent gradient, task = `var(--success)`
green, goal = `var(--gold)`), with a small icon and a `.tower-legend` row (same dot+label pattern
as the existing Clean Streak calendar legend) explaining the color key. A newly-earned block gets a
`.falling` class and a `tower-block-fall` keyframe: starts `translateY(-60px)` and transparent,
drops with an overshoot easing (`cubic-bezier(.34, 1.56, .64, 1)`, the same curve Signal Launch used
for its launch "pop"), and picks up a brief `scaleY(.7)` squash at 75% of the way through before
settling — a landing-impact cue layered purely on top of the block's already-correct flex position,
since flex layout (not JS or rotate/translate math) is what actually places it. New blocks are
staggered 350ms apart on page load, same cascade feel as Signal Launch's staggered satellite
launches, and `playMysteryChime()` fires per block, reused as-is.

**Sizing the container took one real iteration.** `TOWER_BUILD_MAX` (18) blocks at 14px height + 2px
gap between them sums to 286px of actual stack height, plus the base — a first pass at `.tower-build
{ height: 280px }` clipped the top of a fully-stacked tower (confirmed via a Playwright bounding-box
check: the stack's top edge measured *above* the container's own top edge). Fixed by sizing the
container to 320px, with real headroom above the worst-case stack height rather than a tight fit,
and re-verified the same bounding-box check now passes (stack top sits inside the container).

**A click-to-inspect handler ported straight from Signal Launch's pattern**, retargeted:
`#tower-stack` gets one delegated click listener (same shape as the old `#orbit-ring` handler and
the Round 19 cancel-submission handler before it) that updates `#tower-build-detail` with the
clicked block's label and a kind-specific emoji. Verified directly with Playwright — click a block,
read `#tower-build-detail`, confirm it shows that exact block's label — no actionability workaround
needed here (unlike Signal Launch's `.satellite`, tower blocks aren't continuously animating at
rest, so Playwright's normal simulated click works fine without the `eval_on_selector(...
"el.click()")` trick Round 25 needed).

**Verification, in order**: `python manage.py check` clean; `makemigrations --check --dry-run`
confirmed no migration was generated (expected — no model change this round, `models.py` only got
its explanatory comment on `last_seen_positive_event_at` updated to describe the Round 25→26
handoff); a Django-shell sanity pass confirming `tower_build_context()`/`sync_tower_build()` return
correct shapes and that `build_dashboard_context()` no longer contains a `signal_launch` key; a
Django-test-Client render confirming `tower-build`/`tower-stack`/`tower-block`/`tower-base`/
`tower-legend` markup present and every trace of `signal-launch`/`orbit-ring`/`satellite`/
`launch-tower` gone from the rendered page; a full re-seed; a Playwright pass across desktop and
390px mobile confirming an 18-block tower renders with correct per-kind colors and no horizontal or
vertical overflow (the 280px→320px fix above), a real click correctly updating the detail line, and
— by priming one agent's `last_seen_positive_event_at` to just before its newest event — confirming
`state.newTowerBlocks` read `2`, that exactly 2 elements carried the `.falling` class ~150ms into
that page load (caught genuinely mid-animation), and that the class was correctly removed again
(via the `animationend` listener) within 1.2 seconds. grep across the whole project for
`signal_launch`/`signal-launch`/`SIGNAL_LAUNCH`/`satellite` after the round turned up nothing left
in application code — only this document's own history of the round that got replaced.

## Round 27 in detail (2026-09-04) — Signal River: Tower Build rejected on the same grounds, this time with a specific diagnosis

Tower Build shipped, tested exactly as designed, and was still rejected — but this time the
feedback (with a screenshot attached) was specific enough to diagnose precisely, not just react to:
"still not impressive no action happening, also confusing for viewer what is happening jaggered."
Read carefully, "no action happening" isn't a complaint about the theme (blocks vs. satellites vs.
hex tiles) — it's a complaint about *when* motion exists. Tower Build genuinely does animate, but
only for 0.6 seconds at the exact instant a block lands; the other 99.9% of the time — which is what
any screenshot, or any glance that doesn't happen to land in that half-second window, actually shows
— it's a completely static list of flat colored bars. That's the same underlying failure as Round
24's Coverage Map (a static grid that only silently changes color), wearing a different visual
costume. Two different themes, one repeated design mistake: treating "plays an animation on an
event" as equivalent to "has motion," when what actually reads as *alive* to a viewer is something
moving continuously, independent of whether anything just happened.

**Broke the "guess again" pattern differently this time — constrained the options, not just
multiplied them.** Rounds 25 and 26 both opened with AskUserQuestion offering several concepts, but
none of those options carried any explicit requirement about *when* the motion had to run, so it was
possible (and, with Tower Build, is exactly what happened) to pick a concept that still failed the
same way. Round 27's AskUserQuestion named the actual constraint up front — "all of these have
motion running continuously, all the time, not just on new events" — before listing Signal River,
Circuit Grid, and Runner Track as three ways to satisfy it. User picked Signal River.

**The core mechanism: motion that needs no JS to keep running.** Every `.river-packet` gets a single
infinite CSS `@keyframes river-flow` animating its `left` position from 108% (just past the right
edge) to -14% (just past the left edge), on a fixed-duration loop that never stops for the lifetime
of the page. Each packet's `animation-delay` is a negative offset computed purely in CSS —
`calc(-18s / var(--count) * var(--idx))` — so with N packets evenly spaced by that formula, the
stream looks continuous and fully populated from the very first rendered frame, with no JS "spawn
loop" or positioning code needed at all. This is a deliberate contrast with both prior attempts:
Signal Launch's orbit needed a clock-hand rotate/translate trick to place satellites on a circle,
and Tower Build needed flex-column layout plus a one-shot fall keyframe; Signal River's baseline
motion is *simpler* code than either, not more, because letting one CSS property (`left`) do 100% of
the positioning and motion work removes the need to reason about JS-driven layout at all. Verified
directly, not just asserted: a Playwright script read every packet's `getBoundingClientRect().left`
at two points one second apart and confirmed all 24 of 24 packets had genuinely moved — the same
verification rigor as Signal Launch's orbit-motion claim in Round 25, now applied to a completely
different mechanism.

**Reused the event source and the bookkeeping yet again — only the visual vocabulary changed, for
the third time running.** `_agent_positive_timeline()` (Round 22, Clean Streak) is still the one
place that decides what a "win" is; Signal River reads it the same way both prior mechanics did,
filtered to positive events only, for the same reason (a rejection breaks the Clean Streak elsewhere
on the page rather than getting a negative animation here). This is now the fifth distinct visual
language built on that single timeline: Clean Streak = "how many in a row," Spectrum bars = "how
full is this goal," Signal River = "watch it keep flowing." `AgentProfile.last_seen_positive_event_at`
(Round 25) is reused completely unchanged for the third round in a row — same nullable high-water-
mark field, same first-sync-marks-everything-seen behavior. No new migration was needed again.
`SIGNAL_RIVER_MAX` was set to 24 (back up from Tower Build's 18, and matching Signal Launch's
original cap) since a flowing stream can hold more items comfortably than a stack needs vertical
room for — items aren't all on-screen simultaneously the way stacked blocks were, so a higher count
doesn't create the same "does it fit" problem Tower Build hit.

**The "arriving" flourish for newly-earned packets layers cleanly on top of the base motion, by
construction.** Because the continuous flow animates only the `left` property, the `transform`
property on the same element is completely unused by the base motion — so a newly-earned packet's
one-time `.arriving` class can add a second, finite keyframe (`river-arrive`, a scale-up bounce
using the same overshoot easing as every prior round's entrance/landing animations) that animates
`transform` without ever fighting the `left` animation for control of the same property. This also
sidesteps a bookkeeping question the previous two rounds didn't have to answer: when *two*
animations run on one element (one infinite, one finite), does `animationend` fire correctly?
Confirmed by construction rather than needing a workaround: an infinite CSS animation never fires
`animationend` at all (there's no "end" to reach), so the listener attached in dashboard.js reliably
fires only for `river-arrive` — no `event.animationName` check needed, unlike a scenario where two
finite animations might complete separately.

**A real interaction-testing finding, repeated for a second time and now recognized as the pattern
it is.** Just like Round 25's orbiting `.satellite`, Playwright's simulated pointer click refused to
click a continuously-moving `.river-packet` ("element is not stable"). Verification used the same
programmatic `el.click()` workaround as Round 25. This is now documented as a standing pattern for
this project, not a one-off surprise: *any* element with a permanently-running CSS animation on a
positional property will need this same click workaround in Playwright, regardless of theme —
expected to recur again if a future round adds a clickable element to something else that's always
moving.

**Verification, in order**: `python manage.py check` clean and `makemigrations --check --dry-run`
confirmed no migration generated (no model change this round — `last_seen_positive_event_at` reused
as-is, only its explanatory comment updated for the Round 26→27 handoff); a Django-shell sanity pass
confirming `signal_river_context()`/`sync_signal_river()` return correct shapes and that
`build_dashboard_context()` no longer carries a `tower_build` key; a Django-test-Client render
confirming `signal-river`/`river-packet` markup present and every trace of `tower-build`/
`tower-stack`/`tower-block`/`signal-launch`/`orbit-ring`/`satellite` gone from the page; a full
re-seed; a Playwright pass across desktop and 390px mobile confirming a 24-packet river renders with
no horizontal overflow (`.signal-river`'s `overflow: hidden` correctly clips packets currently
positioned outside the 0–100% band, which is expected and intentional, not a layout bug), all 24
packets genuinely changing position over a 1-second window (the "is this really moving" check above),
a programmatic click correctly updating `#signal-river-detail` to that exact packet's label, and — by
priming one agent's `last_seen_positive_event_at` to just before its newest timeline event —
confirming `state.newRiverPackets` read `2`, that exactly 2 elements carried the `.arriving` class
~150ms into that page load (caught genuinely mid-animation), and that the class was correctly
removed again within 1.2 seconds via the `animationend` listener. A whole-project grep for
`tower_build`/`tower-build`/`tower-stack`/`tower-block`/`TOWER_BUILD`/`newTowerBlocks` after the
round turned up nothing left in application code — only prose in code comments and this document's
own history of the rounds that got replaced.

### Round 27 addendum, same day — self-labeled pills replace icon-only dots + a separate legend

The first cut of Signal River shipped exactly as designed above and drew a new complaint, distinct
from "not impressive": legibility. The packets were small round dots distinguished only by color and
a tiny icon, with a `.river-legend` color key underneath spelling out what blue/green/gold meant. The
user's objection, paraphrased: a viewer glancing at the card — or being shown a screenshot of it, with
no chance to read the legend or click anything — has no way to know what a moving blue dot represents.
"How should I explain / make understandable... not like this." Fair: needing to cross-reference a
legend, or click an element, just to identify *what kind of thing is even flowing* is a real
legibility gap, separate from the "is it moving" problem the round had already fixed.

The fix: each `.river-packet` became a self-labeled pill — the same icon as before, plus a short
always-visible text label baked directly onto the moving element (`💰 Sale`, `✅ Task done`,
`🎯 Goal hit`). Nothing needs interpreting or clicking to know what a given packet is; the color
still reinforces category at a glance for a returning viewer, but is no longer load-bearing for a
first-time one. The now-redundant `.river-legend` row was deleted from both `_signal_river.html` and
`style.css` — same "remove, don't hide" standard as every other retired piece of markup in this
project. `signal_river_context()`/`sync_signal_river()`/the JSON wiring were untouched; this was
purely a template + CSS legibility pass, not a data or mechanism change.

Widening each packet from a 30px circle to a ~104px pill meant the layout math needed rework too:
at the original size, roughly 20 of the 24 packets could be visible inside the card at once (the
container is wide enough, and the 18s/24-packet cadence dense enough, that most of the stream is
on-screen simultaneously) — fine for small dots, but 20 pills at 104px each would overlap constantly.
The existing 4-lane vertical `--jitter` system (originally added just for cosmetic variety) already
put every 4th packet in the same lane, so widening the vertical spread between lanes (from a ~46px
total spread to a ~100px spread, and growing `.signal-river`'s height from 130px to 160px to fit it)
turned those 4 lanes into real collision avoidance: same-lane neighbors now get 4x the time (and
therefore horizontal) spacing, comfortably wider than one pill. The travel range was also widened
(`left: 118%` → `-30%`, was `108%` → `-14%`) so a wider pill still fully exits the visible band
before the loop repeats, rather than a sliver of it lingering visible at the edge.

**Re-verified after the change**, not just eyeballed: the same Playwright script from the original
Round 27 pass — `getBoundingClientRect()` motion check, `overflow: hidden`/no-clip check, a
programmatic click confirming `#signal-river-detail` still updates correctly, and the
`.arriving`-class mid-animation catch for a freshly-primed agent — all re-run clean against the
labeled-pill version, plus a fresh desktop/mobile screenshot pair confirming the labels render
legibly (`"Sale"`/`"Task done"`/`"Goal hit"` all directly readable in the screenshot, no legend
needed) with no visible overlap at either width. A full re-seed followed before the delivery zip was
rebuilt.

## Project structure (delivered zip: spectrum_project.zip)
- `DEPLOYMENT_GUIDE.md` (new, same day as Round 17; revised same day per the Shell-free pivot
  above): a from-scratch, beginner-level walkthrough for the user specifically — GitHub Desktop or
  the plain browser uploader to publish the repo, then a Render Web Service with the exact five-part
  Build Command, Start Command, and all seven environment variables spelled out (setup now runs
  automatically on every deploy via `ensure_superuser`, no Shell/manual step needed), then sharing the
  link. Written after confirming (Round 17 addendum, above) that the `STORAGES` fix actually works
  end-to-end under `DEBUG=False` — this guide assumes that fix is in place. Included in the delivered
  zip alongside README.md; the two are complementary (README covers local dev + a condensed deploy
  summary aimed at a more technical reader, this guide is the click-by-click version). The user's
  actual publishing workflow has since moved to VS Code Git (Round 19) rather than the browser
  uploader this guide originally centered on; the Render-side instructions are unaffected.
- Django project `spectrum`, single app `agent_portal`.
- Models: Region, Tier, Category, Product, Incentive, IncentiveTierRule, IncentiveProductGoal,
  AgentProfile, Sale (with `status`, and now `reviewed_at` — Round 22), AgentAchievement,
  AgentTaskCompletion, AgentGoalBonus. Role (Round 12) is Django Groups, not a new model/field —
  see Round 12 detail above. Round 21 added `AgentLoginDay` and `AgentWeeklyChallengeCompletion`
  (both still present) plus `AgentSpinResult` and three `AgentProfile` fields
  (`streak_freezes`, `last_spin_date`, `last_seen_level`) — migration
  `0006_agentprofile_last_seen_level_and_more`. Round 22 removed `AgentSpinResult` and
  `last_spin_date`, and added `AgentCleanStreakAward` (an append-only ledger, deliberately not
  `unique_together` — see Round 22 detail) plus three more `AgentProfile` fields
  (`highest_clean_streak_awarded`, `last_clean_streak_seen`, `longest_clean_streak_ever`) —
  migration `0007_remove_agentprofile_last_spin_date_and_more`. Round 25 added one more
  `AgentProfile` field, `last_seen_positive_event_at` (nullable `DateTimeField`) — migration
  `0008_agentprofile_last_seen_positive_event_at`, purely additive, no removals this round.
- `roles.py` (Round 12): `get_user_role`, `url_name_for_role`, `redirect_to_own_portal`,
  `role_required(*roles)` decorator. Round 20 added `ROLE_TAB_LABELS` (short labels matching the
  login page's tab text exactly, distinct from the fuller `ROLE_LABELS`) and rewrote the module
  docstring to describe the login-time role check rather than the superseded "tabs are cosmetic"
  reasoning — see Round 20 detail.
- `context_processors.py` (Round 12): `topbar_avatar` — fallback emoji/role label for the topbar
  chip on non-Agent accounts. Registered in `settings.py`.
- `signals.py` (extended Round 21, unchanged in Round 22): `update_login_streak` (on
  `user_logged_in`) records each login day into `AgentLoginDay`, spends/backfills a streak freeze
  on a single missed day, and awards a new freeze every `STREAK_FREEZE_MILESTONE` days — see Round
  21 detail for the date-bug caught and fixed here. (The Clean Streak mechanic, despite the similar
  name, is unrelated to this login-streak signal — it lives entirely in `insights.py` and is
  computed from `Sale`/`AgentTaskCompletion`/`AgentGoalBonus`, not from login events.)
- `insights.py`: `DAILY_LOG_QUANTITY_CAP`, `daily_logged_quantity`, `recent_sales_for_agent`,
  `sync_goal_bonuses`, `analyst_overview()`/`director_overview()` (Round 12; `director_overview()`'s
  `pending_rows` gained `id`/`points` in Round 19), and `product_points_map(incentive)` (Round 19,
  new — product_id → points-per-unit, powers the log-sale live preview). Every aggregate function
  filters through `Sale.objects.approved()`. Now imports `Product` explicitly (Round 19 bugfix —
  see that round's detail). Round 21 added `level_progress()`/`sync_level_up()`/`LEVEL_XP_STEP`/
  `LEVEL_TITLES` (all unchanged in Round 22), `sync_weekly_challenges()`/`weekly_challenges_context()`/
  `WEEKLY_CHALLENGE_TEMPLATES`/`_iso_week_bounds()` (unchanged), and `login_streak_calendar()`
  (unchanged). Round 22 removed `SPIN_PRIZES`/`spin_the_wheel()`/`spin_wheel_context()`/
  `has_spun_today()` entirely and added `CLEAN_STREAK_MILESTONES`/`CLEAN_STREAK_MILESTONE_POINTS`/
  `_agent_positive_timeline()`/`clean_streak_progress()`/`sync_clean_streak()`/`clean_streak_feed()`;
  extended `lifetime_points()` to sum `AgentCleanStreakAward` instead of `AgentSpinResult`; and
  added `incentive_comparison_rows()`/`review_turnaround_stats()`/`top_clean_streaks()` near the
  existing `analyst_overview()`/`director_overview()` — see Round 22 detail. Round 23 added
  `GOAL_SPECTRUM_BAR_HEIGHT_CYCLE`/`GOAL_SPECTRUM_MAX_BARS`/`_goal_spectrum_bars()` and extended
  `product_goal_progress()`'s return dict with a new `spectrum_bars` field — see Round 23 detail.
  Round 24 added `coverage_map(goals)` — **removed again in Round 25** (rejected by the user; see
  Round 25 detail) — replaced by `SIGNAL_LAUNCH_MAX`, `sync_signal_launch()`, and
  `signal_launch_context()`, both reading `_agent_positive_timeline()` (built for Clean Streak,
  Round 22) filtered to positive events only. `build_dashboard_context()`'s `"coverage_map"` entry
  is gone; `"signal_launch": signal_launch_context(agent)` replaced it. **Round 26 renamed all of
  this again** (rejected in turn — see Round 26 detail) to `TOWER_BUILD_MAX` (18),
  `sync_tower_build()`, and `tower_build_context()` (same `_agent_positive_timeline()` source,
  `"blocks"` replacing the `"satellites"` key); `build_dashboard_context()`'s
  `"tower_build": tower_build_context(agent)` replaced `"signal_launch"`. **Round 27 renamed it all
  a third time** (rejected in turn again — see Round 27 detail) to `SIGNAL_RIVER_MAX` (24, back up
  from Tower Build's 18), `sync_signal_river()`, and `signal_river_context()` (`"packets"` replacing
  the `"blocks"` key); `build_dashboard_context()`'s `"signal_river": signal_river_context(agent)`
  replaced `"tower_build"`. No new migration in any round after Round 25 —
  `last_seen_positive_event_at` is reused as-is throughout.
- `views.py`: `dashboard()` syncs before building context, and (Round 12) redirects a non-Agent
  authenticated user to their own portal instead of showing `no_profile.html`. `api_log_sale()`
  built around the cap + pending flow. `analyst_dashboard`/`director_dashboard`/`no_role` (Round
  12), all through `roles.role_required`. Round 18 added `landing_page()` (public, redirects an
  authenticated session to its own portal). Round 19 added `api_cancel_sale` (agent deletes their
  own still-pending sale) and `api_review_sale` (`@role_required(ROLE_DIRECTOR)`, approve/reject),
  plus `product_points_json` in `dashboard()`'s context. Round 20:
  `SpectrumLoginView.form_valid()` (new) rejects a login whose `selected_role` doesn't match the
  account's real role, before a session is established; `get_context_data` now also passes
  `selected_role` so the template can echo back whichever tab was actually selected. See Round 20
  detail. Round 21 added `api_spin_wheel` and wired `sync_weekly_challenges()`/`sync_level_up()`
  into `dashboard()`'s sync-before-context-build chain. Round 22 **removed** `api_spin_wheel`
  entirely; added `sync_clean_streak()` to the same sync chain plus a `new_clean_streaks_json`
  context entry (replacing `spin_prizes_json`); `api_review_sale` now sets `sale.reviewed_at =
  timezone.now()` alongside the status flip; `analyst_dashboard()`/`director_dashboard()` now pass
  `comparison_rows`/`cash_per_point` (both) and `turnaround`/`top_streaks` (director only). Added a
  `from django.utils import timezone` import. Round 25 added `sync_signal_launch()` to the same
  sync-before-context-build chain and a `new_signal_launches_json` context entry (an int — how many
  satellites are new this load, not a list, since dashboard.js only needs the count — see Round 25
  detail). Round 26 renamed both to `sync_tower_build()` and `new_tower_blocks_json` (same int
  shape, now counting new blocks instead of new satellites) — see Round 26 detail. Round 27 renamed
  both again to `sync_signal_river()` and `new_river_packets_json` (same int shape, now counting new
  packets) — see Round 27 detail.
- `urls.py`: Round 19 added `api/cancel-sale/<id>/` and `api/review-sale/<id>/`. Round 21 added
  `api/spin-wheel/`, **removed in Round 22** (route deleted, not just unwired).
- `admin.py`: `SaleAdmin` gets `status` + approve/reject bulk actions (Round 8) — now a fallback
  behind the Round 19 in-app Director queue rather than the only approval path. Round 22: both
  bulk actions now also set `reviewed_at=timezone.now()` in their `.update(...)` calls (bulk
  `update()` bypasses `save()`, so this has to be explicit); added a `from django.utils import
  timezone` import and an `AgentCleanStreakAwardAdmin` registration for consistency with the
  other award models.
- `seed_data.py`: `_seed_incentives()` ties "current incentive" to the real run date (Round 9) —
  re-run whenever the demo has sat untouched long enough for the calendar to roll past it. Round
  12 added `_seed_analyst_and_director()` (groups + `analyst1`/`director1` demo users). Round 22
  extended `_seed_sales()` to set `reviewed_at` on every reviewed seeded sale (a random 15
  min–48h turnaround after `sold_at`), introduce an ~8% seeded rejection rate
  (`SEED_REJECTION_RATE`), and keep a ~60%-chance-each pending status on each agent's 1-2 most
  recent sales within the *current* incentive only — see Round 22 detail.
- `templates/base.html`: topbar user-chip's name is `<span class="user-chip-name">` (Round 10,
  mobile collapse-to-avatar-only fix). Round 12: chip markup split into agent/non-agent branches
  (see bug #1 above). Round 14: authenticated topbar section wrapped in an overridable
  `{% block topbar_session %}` so a child template (login.html) can suppress it entirely.
- `templates/registration/login.html`: Round 11 — auth-card (login form) now renders before the
  teaser banner, no duplicate brand mark, no dangling "log in to see where you stand" line. Round
  12 — `.role-tabs`, `.auth-hero` SVG illustration, `login.js` include. Round 14 — `data-demo-role`
  attrs, `topbar_session` block override. Round 15 — illustration comment updated for the new
  1150px show-threshold (see Round 15 detail). Round 16 — `login.js` include
  now goes through `{% static_v %}` (see Round 16 detail), same as every other CSS/JS include in
  the project (`base.html`, `dashboard.html`). Round 17 — hero
  illustration markup removed; role-tabs relocated into a new `.role-switch` block after the
  `<form>`. See Round 17 detail above. Round 20 — each `.role-tab` gained a `data-role` attribute
  (the role slug, distinct from the human-readable `data-demo-role`); a hidden
  `#selected-role`/`name="selected_role"` input added to the form; the active tab, heading/subtext,
  and demo-credentials line now all render server-side from a `selected_role` context variable
  instead of being hardcoded to Agent's copy; the error banner now shows `form.non_field_errors.0`
  (the actual message, including the new role-mismatch one) instead of a single hardcoded string.
  See Round 20 detail.
- `templates/landing.html` (Round 18, new): standalone public landing page, its own `<html>` doc
  (not extending `base.html` — deliberately a separate color system, see Round 18 detail above),
  styled by `static/agent_portal/css/landing.css` and `landing.js`.
- `templates/agent_portal/analyst_dashboard.html`, `director_dashboard.html`, `no_role.html`
  (Round 12, new). `director_dashboard.html` rebuilt in Round 19 with a live `#pending-review-list`
  (Approve/Reject cards) in place of the old plain admin-linked list — see Round 19 detail. Round
  22 added a Review Turnaround + Approval Rate pair of stat chips, an incentive-comparison section,
  and a Top Clean Streaks card to `director_dashboard.html`; `analyst_dashboard.html` gained the
  same incentive-comparison section — see Round 22 detail.
- `templates/agent_portal/_pending_sales.html` (Round 19, new): partial rendered inside
  `director_dashboard.html`'s pending-review block.
- `templates/agent_portal/_incentive_comparison.html` (Round 22, new): shared partial rendering
  `insights.incentive_comparison_rows()` — included from both `analyst_dashboard.html` and
  `director_dashboard.html` so the two portals can never disagree on the comparison logic/markup.
- `templates/agent_portal/_goals.html` (Round 23): each goal's `.progress-track`/`.progress-fill`
  bar replaced with a `.spectrum-meter` (one `.spectrum-bar` per `g.spectrum_bars` entry plus a
  `.spectrum-antenna` beacon) — see Round 23 detail. `.progress-track`/`.progress-fill` themselves
  are untouched and still used by `_incentive_comparison.html` and the login streak calendar.
- `templates/agent_portal/dashboard.html`: stat-strip; log-sale modal's recent-submissions list;
  `dashboard-data` JSON carries `newAchievements`/`newTasks`/`newMysteryBoxes`. Round 19: modal
  gained `#sale-preview`/`#cap-warning`; `dashboard-data` JSON gained `productPoints`/
  `progress.pointsToNext`/`progress.nextTierName`/`progress.nextTierEmoji`/`dailyCap`; added
  `aria-labelledby`/`aria-label` to all three modal dialogs and `aria-label`s on the stepper
  buttons/quantity input. Round 21: new "🎮 Game Center" tab (Level card, Streak+Spin card, Weekly
  Challenges card); `dashboard-data` JSON gained `newWeeklyChallenges`/`levelUp`/`spinPrizes`/
  `alreadySpunToday`. Round 22: Game Center tab rebuilt as a 3-card `.grid-3` layout — the spin
  block removed from the Daily Streak card, a new standalone Clean Streak card added (count,
  progress-to-next-milestone bar, recent-awards feed), Weekly Challenges unchanged;
  `dashboard-data` JSON's `spinPrizes`/`alreadySpunToday` replaced with `newCleanStreaks` — see
  Round 21/22 detail. Round 24: a new `.card.coverage-map-card` section added below the 3-card
  grid (not inside it — the map needed room to breathe as its own full-width block) — **rejected
  by the user and removed again in Round 25**, replaced by `.card.signal-launch-card` in the same
  slot, including `_signal_launch.html`; `dashboard-data` JSON's `newCleanStreaks` entry gained a
  sibling, `newSignalLaunches` (an int, not an array — see Round 25 detail) — see Round 24/25
  detail. **Round 26: `.card.signal-launch-card` rejected in turn**, replaced by
  `.card.tower-build-card` in the same slot, including `_tower_build.html`; `dashboard-data` JSON's
  `newSignalLaunches` entry renamed to `newTowerBlocks` (same int shape) — see Round 26 detail.
  **Round 27: `.card.tower-build-card` rejected in turn**, replaced by `.card.signal-river-card` in
  the same slot, including `_signal_river.html`; `dashboard-data` JSON's `newTowerBlocks` entry
  renamed to `newRiverPackets` (same int shape) — see Round 27 detail.
- `templates/agent_portal/_coverage_map.html` (Round 24, new) — **deleted outright in Round 25**,
  not just unwired; replaced by `_signal_launch.html` (Round 25, new) — **deleted outright in
  Round 26 in turn**, not just unwired; replaced by `_tower_build.html` (Round 26, new) —
  **deleted outright in Round 27 in turn**, not just unwired; replaced by:
- `templates/agent_portal/_signal_river.html` (Round 27, new): the Signal River partial — a
  `#signal-river` band containing a `.river-source` broadcast-tower icon and one
  `<button class="river-packet river-packet-{kind}">` per positive-timeline event from
  `signal_river_context()`, each positioned entirely by CSS (no per-packet coordinate computed
  here — see the `style.css` bullet below) and each carrying its own always-visible
  `.river-packet-icon` + `.river-packet-label` text (e.g. "💰 Sale," "🎯 Goal hit") baked directly
  onto the moving element, plus a `#signal-river-detail` line updated client-side on packet click —
  see Round 27 detail and its same-day addendum (the labels, and the now-redundant separate
  `.river-legend` color key they replaced, were a same-day follow-up after the first cut of this
  round shipped with icon-only dots that the user couldn't identify without clicking or reading a
  legend). (Tower Build's `.tower-stack`/`.tower-block`/`.tower-base` flex-stack markup is gone
  entirely.)
- `templates/agent_portal/_recent_sales.html`: Round 19 — `data-sale-id` on each row, a Cancel
  button on any row still `pending`.
- `templates/agent_portal/_weekly_challenges.html` (Round 21, new): partial rendered inside the
  Game Center tab's Weekly Challenges card — reuses the exact `.task-card` markup from
  `_tasks.html` rather than inventing new markup/CSS.
- `spectrum/settings.py` (Round 15, superseded same-day): originally set the legacy
  `STATICFILES_STORAGE` conditional on `DEBUG`; discovered to be a silent no-op on this Django
  version (see same-day addendum above) and replaced with the `STORAGES` dict — plain
  `StaticFilesStorage` in local dev (no manifest, always serves the current file), manifest/hashed
  WhiteNoise storage only when `DEBUG=False` (production/Render). See Round 15 detail and the
  same-day addendum above.
- `spectrum/settings.py` (Round 16): `WhiteNoiseMiddleware` also now conditional on `DEBUG` —
  excluded from `MIDDLEWARE` entirely in local dev, so it can never serve a stale `STATIC_ROOT`
  snapshot. See Round 16 detail above.
- `agent_portal/templatetags/asset_tags.py` (Round 16, new): `{% static_v %}` tag — `{% static %}`
  plus a `?v=<source file mtime>` cache-buster, used for every CSS/JS include project-wide so a
  browser can never keep serving a cached copy past a real edit. See Round 16 detail above.
- `agent_portal/management/commands/ensure_superuser.py` (new, same day as Round 17's deployment
  walkthrough): idempotent superuser creation from `DJANGO_SUPERUSER_*` env vars, meant to be chained
  onto the end of the Render Build Command so a deploy host without Shell access still gets an admin
  login automatically. See the deployment-walkthrough section above.
- `agent_portal/urls.py` (Round 18): `""` → `landing_page` (new, public); the Agent dashboard moved
  from `""` to `"dashboard/"` (same URL name, path only). See Round 18 detail above.
- `static/agent_portal/css/landing.css`, `static/agent_portal/js/landing.js` (Round 18, new): the
  public landing page's own color system and vanilla-JS interactivity, separate from `style.css`.
  See Round 18 detail above.
- `static/agent_portal/js/director.js` (Round 19, new): Approve/Reject fetch handlers for the
  in-app Director queue, plus its own small toast queue (`#director-toast`).
- `style.css`: Round 10 — `.orb` mask-image, `.tab-panel` min-height+justify-content:center,
  mobile tabs horizontal-scroll (`max-width:700px`), hero-card column-stack (`max-width:560px`),
  `.btn{white-space:nowrap}`, user-chip-name hide (`max-width:480px`). Round 11 —
  `.auth-wrap{padding-top}` 40px→24px, removed unused `.brand-mark-lg` rule. Round 12 —
  `.auth-wrap` flex row + gap, `.role-tabs`/`.role-tab`, `.auth-hero`/`.auth-illo`, illustration
  keyframes (all reduced-motion-guarded), `.mini-row`, `.dash-compact`. Round 13 — global
  `button { appearance: none; ... }` reset near the top of the file; `.auth-hero`/`.auth-wrap`
  changed from a single 980px hide/show cutoff to a scaling two-tier breakpoint (660px / 980px).
  Round 19 — `.sale-preview`, `.cap-warning`, `.recent-sale-cancel`, `.pending-row`/`.review-btn`
  (Approve/Reject, matching the existing `.pill-danger` fixed-hex red rather than introducing a new
  CSS custom property, per this project's "one extra semantic color used sparingly" pattern).
  Round 21 — `.level-card`/`.level-badge-emoji`/`.level-progress-track`, `.game-center-grid`,
  `.streak-calendar`/`.streak-dot*`/`.streak-legend*`, `.spin-wheel-*` (reuses `--gold`/`--silver`
  for two wheel-segment colors, same tokens already used for confetti). Round 22 — all
  `.spin-wheel-*` rules and their reduced-motion guard deleted; added `.grid-3` (the new 3-card
  Game Center layout), `.clean-streak-*` rules, and `.comparison-row-current`/
  `.comparison-row-stats` (Analyst/Director incentive comparison, reusing `.goal-item`/
  `.progress-track`/`.progress-fill` rather than new table CSS) — see Round 22 detail. Round 23 —
  new `.spectrum-meter`/`.spectrum-bars`/`.spectrum-bar`/`.spectrum-antenna`/`.antenna-wave` rules
  (Goals tab only; `.progress-track`/`.progress-fill` themselves untouched, still used elsewhere)
  plus their own reduced-motion guard — see Round 23 detail. Round 24 — new `.coverage-*`/
  `.hex-tile` rules — **all deleted again in Round 25**, none of it survived. Round 25 — new
  `.signal-launch`/`.launch-tower`/`.orbit-ring`/`.satellite`/`.satellite-icon` rules: satellites
  positioned via the classic `rotate() translate()` clock-hand technique keyed off `--oi`/
  `--ocount` custom properties, a permanent `orbit-spin` animation on `.orbit-ring` (50s/revolution,
  runs forever — the "idle" motion), a one-time `satellite-launch` animation (overshoot easing,
  `.satellite.launching`) for newly-earned satellites, a subtle `tower-glow` breathing animation on
  the tower emoji, and their own reduced-motion guard (disables the two continuous animations and
  the launch animation, but the satellite's own static positioning rule — not itself animated —
  still renders every satellite in its correct resting spot) — see Round 25 detail. Round 26 — **all
  of the above deleted again**, replaced with `.tower-build`/`.tower-stack`/`.tower-block`/
  `.tower-block-{sale,task,goal}`/`.tower-base`/`.tower-legend` rules: blocks positioned by plain
  `flex-direction: column` flow (no rotate/translate math needed, unlike the orbit), a
  `tower-block-fall` keyframe (overshoot easing + a mid-fall `scaleY(.7)` squash for landing impact)
  for newly-earned blocks, and their own reduced-motion guard. One real sizing iteration: the
  container's first height (280px) clipped an 18-block tower at the top (a Playwright bounding-box
  check caught it — the stack's top edge measured above the container's own), fixed by sizing to
  320px with real headroom over the 286px worst-case stack height — see Round 26 detail. Round 27 —
  **all of the above deleted again**, replaced with `.signal-river`/`.river-source`/`.river-packet`/
  `.river-packet-{sale,task,goal}` rules: an ambient `river-current` background animation (a
  repeating diagonal-stripe gradient scrolling via `background-position`) runs permanently
  regardless of packet count, so the card never looks fully static even empty; each packet's
  continuous horizontal travel is one infinite `@keyframes river-flow` animating `left`, with
  `animation-delay: calc(-18s / var(--count) * var(--idx))` distributing every packet evenly along
  the stream from the first rendered frame — no JS positioning at all for the base motion, unlike
  every prior version of this mechanic. A `river-arrive` keyframe (same overshoot easing as prior
  rounds' entrance animations) plays once on newly-earned packets via `transform`, a property the
  flow animation never touches, so the two coexist without conflict. Deterministic vertical variety
  via `:nth-of-type(4n+…)` `--jitter` rules (same "fixed repeating cycle, not random.random()"
  approach as `GOAL_SPECTRUM_BAR_HEIGHT_CYCLE`). Reduced-motion guard disables all three animations
  and repositions packets into a static evenly-spaced row via a `calc()` on `left` keyed off the
  same `--idx`/`--count` — without this override, disabling the flow keyframe would leave every
  packet stuck at its `left` fallback, permanently invisible just off the right edge — see Round 27
  detail. **Same-day addendum**: packets widened from 30px icon-only circles to ~104px pills
  carrying an always-visible `.river-packet-label` (plain white text, `text-shadow`-outlined for
  contrast over any of the three fill colors) alongside the icon, and the separate `.river-legend`
  rules were deleted as redundant once the label made the legend unnecessary. Widening the packets
  meant reworking two things that were sized for tiny dots: the `--jitter` vertical lane spread grew
  from ~46px to ~100px (and `.signal-river`'s height from 130px to 160px to fit it) so the existing
  4-lane system — originally just cosmetic variety — actually prevents same-lane pills from
  overlapping at the new width; and the travel range widened from `108%↔-14%` to `118%↔-30%` so a
  wider pill still fully clears the visible band before its loop repeats. See the addendum under
  Round 27 detail.
- `dashboard.js`: Round 10 — `sizeCanvasForDisplay()` + debounced `resize` listener so
  `drawHistory` always renders at true on-screen resolution. Round 19 — live sale-preview IIFE,
  cancel-submission handler (event-delegated on `#recent-sales-list`), and the shared modal
  focus-trap/Escape-to-close IIFE (document-level keydown listener — see Round 19 detail for why).
  Round 21 — `drawSpinWheel()`/`spinToPrize()`/`revealSpinResult()` (canvas wheel + spin animation),
  `unlockWeeklyChallenges()` (mirrors `unlockTasks()`), `celebrateLevelUp()` (finally wires up the
  previously-dead `playLevelUpSound()`), all hooked into the existing on-load celebration block.
  Round 22 — the entire spin-wheel block (including `prefersReducedMotion()`, which had no other
  callers) deleted; replaced with a much smaller `celebrateCleanStreaks(awards)` hooked into the
  same on-load celebration block — see Round 22 detail. Round 23 — no JS changes: the spectrum
  meter's entrance/live animations are pure CSS (see the `style.css` bullet above), and goal
  completion already had its own celebration via the existing `queueMysteryBox()`/
  `openMysteryBox()` (built Round 6) — see Round 23 detail for why that was judged sufficient
  rather than adding a second celebration path. Round 24 — added an event-delegated click handler
  on `#coverage-map-grid` and a `coverage-pct` count-up entry — **both removed again in Round 25**
  along with everything else Coverage-Map-shaped. Round 25 — added an event-delegated click handler
  on `#orbit-ring` (reports the clicked satellite's label into `#signal-launch-detail`); and, unlike
  every prior round's "no JS needed, it's pure CSS" pattern, this round's core ask specifically
  *required* JS — reads `state.newSignalLaunches` (a plain int) and, since the server-rendered
  timeline is always most-recent-first, animates exactly the first N `<button class="satellite">`
  elements it finds in the DOM (no per-item "is this new" flag needed from the server), staggered
  350ms apart via `setTimeout`, each one playing a mystery-box-style chime
  (`playMysteryChime()`, reused rather than building a second sound) and removing its own
  `.launching` class on `animationend` — see Round 25 detail, including a real Playwright finding
  (simulated pointer clicks refuse to click a continuously-moving element; verification switched to
  a programmatic `el.click()`). Round 26 — the orbit click handler and launch-stagger logic
  **removed entirely**, replaced with an event-delegated click handler on `#tower-stack` (reports
  the clicked block's label into `#tower-build-detail`) and a `state.newTowerBlocks`-driven
  fall-stagger block (same shape as Round 25's — first N `<button class="tower-block">` elements,
  350ms apart, `playMysteryChime()` reused, `.falling` class removed on `animationend`); since tower
  blocks aren't continuously animating at rest the way orbiting satellites were, ordinary Playwright
  clicks work here with no `el.click()` workaround needed — see Round 26 detail. Round 27 — the
  tower click handler and fall-stagger logic **removed entirely**, replaced with an event-delegated
  click handler on `#signal-river` (reports the clicked packet's label into `#signal-river-detail`)
  and a `state.newRiverPackets`-driven arrival-stagger block (same shape as Rounds 25/26's — first N
  `<button class="river-packet">` elements, 350ms apart, `playMysteryChime()` reused, `.arriving`
  class removed on `animationend`); since river packets flow continuously and permanently (unlike
  Tower Build's resting blocks), the Round 25 `el.click()` workaround was needed again for
  verification — see Round 27 detail, including why the `animationend` listener needs no
  `event.animationName` check despite two animations running on the same packet at once (the base
  flow animation is infinite and therefore never itself fires `animationend`).
- `login.js` (Round 12, new): role-tab click handler + `.auth-hero` mouse-tilt, both
  reduced-motion-guarded. Hero-tilt/badge-pulse listeners removed in Round 17 (illustration gone).
  Round 20 — the tab-click handler's existing `applyTabCopy()` also sets the hidden
  `#selected-role` field's value now, so the role actually submitted with the form always matches
  whichever tab is visually active.

## Verified working (all rounds)
Round 8: scripted tests confirmed pending sales don't move stat-strip numbers, approval correctly
triggers same-reload sync, daily cap rejects correctly, goal-scoping still correct. Round 9: fresh
migrate+seed confirmed clean; scripted login confirmed populated dashboard. Round 10: before/after
Playwright screenshots for all four fixes at desktop+mobile; `bounding_box()` confirmed mobile
Log-out button fully clickable; all 6 seeded agents load 200 OK after the changes. Round 11:
`bounding_box()` on the submit button confirmed a constant ~y440 position across four viewport
heights (900/760/660px desktop, 844px mobile) before and after, proving the fix; screenshot
confirmed the `{# #}` comment leak was fully gone after switching to `{% comment %}`; scripted
login (correct password) and a wrong-password attempt both verified working end-to-end post-fix.
Round 12: scripted 3-account access-control test (agent1/analyst1/director1 × `/`, `/analyst/`,
`/director/`) confirmed every landing and bounce matches the intended matrix; `node --check` on
both JS files and a CSS brace-balance check both passed; `python manage.py check` clean;
screenshots at desktop (1440×900) and mobile (390×844) confirmed the avatar-chip fallback renders
correctly (📊/🧭, not an empty circle) and confirmed the second `{# #}`-comment leak (bug #2 above)
was fully gone after the fix — both bugs were caught by screenshot, not guessed from code; login
page re-confirmed still needs zero scrolling at a 660px-tall viewport with the new hero image in
place, and the hero image itself is confirmed absent (not just visually hidden) at mobile width.
Round 13: Playwright sweep across 390/660/693/900/980/1440px widths (light theme, matching the
user's report) confirmed zero horizontal overflow and a within-viewport submit button at every
width; screenshots at each confirmed the illustration scales smoothly from hidden → 190px → 300px
rather than popping in abruptly; `node --check` and the CSS brace-balance check both re-passed
(CSS-only change this round, no JS/Python touched); the full 3-account access-control regression
from Round 12 was re-run and still passes unchanged. Round 14: scripted Back-navigation test across all three
roles confirmed the login page's topbar never shows authenticated state; Playwright confirmed all
five interactivity additions and caught the `[hidden]`-override bug before delivery. Round 15: a
live edit-and-reload check proved the static-file fix actually works (no more restart needed to
see a CSS change); a 5-width Playwright sweep in both themes confirmed the teaser sits beside the
card with zero scrolling from 900px up and stays scroll-free even stacked at 390/693px; DOM checks
confirmed exactly one role-tab checkmark is ever visible; the Round 14 Back-navigation and
interactivity tests were both re-run unchanged and still pass. Round 17: a
Playwright sweep across 7 widths (390 to 1920px) plus a deliberately short 1920x800 viewport
confirmed zero overflow and a fully in-viewport submit button everywhere, including the exact
wide-but-short shape that broke with the illustration; a pixel-level check of the card's
horizontal center against the viewport's center caught a real grid auto-placement bug (see Round
17 detail) that a visual screenshot alone had not made obvious, and confirmed 0px offset at every
width from 1020 to 1920 after the fix; Round 14's Back-navigation test and the tab-switch/
password-toggle interactivity checks were both re-run and still pass. Round 16: reproduced the actual
WhiteNoise/STATIC_ROOT staleness bug directly in the workspace (planted a fake stale `staticfiles/`
folder with visibly wrong CSS, confirmed the dev server serves it before the fix and correctly
bypasses it after); confirmed the `{% static_v %}` tag's `?v=` value changes immediately after
touching a static file, proving new edits always produce a URL the browser has never cached; the
Round 14 Back-navigation test and Round 15's full Playwright sweep (5 widths, both themes) were
both re-run against the final code and still pass with zero regressions. Round 18: a scripted
Django test-client check (anonymous `/` shows the landing page and links to `/login/`; anonymous
`/dashboard/` redirects to `/login/?next=/dashboard/`; a logged-in agent hitting `/` redirects to
`/dashboard/`, which then loads 200) confirmed the route swap didn't break the existing
login-required flow; a Playwright pass confirmed the navy/white/blue palette via
`getComputedStyle`, confirmed clicking "Log in" actually navigates to `/login/`, and confirmed the
mobile hamburger menu opens/closes with correct ARIA state; `python manage.py check` re-run clean.
Round 19: `python manage.py check` clean; a scripted Django-test-Client script covering
`api_log_sale`→`api_cancel_sale` (create/cancel/double-cancel-refused), non-director blocked from
`api_review_sale`, director approve/reject (including double-review-refused), the pre-existing
daily-cap rejection re-confirmed, and both `/dashboard/` and `/director/` rendering the new markup —
this caught the missing-`Product`-import bug (see Round 19 detail) before any visual pass ran; a
Playwright pass confirmed the live point-preview updates on product/quantity change, the cap-warning
appears and disables submit past the daily limit, a full log→cancel round trip works, Escape closes
the log-sale modal (this caught the focus-trap DOM-removal bug — see Round 19 detail), the Director
queue's Approve button removes the row and updates both stat chips live, and the log-sale modal
renders correctly at 390×844 mobile width. Round 20: `python manage.py check` clean; a scripted
Django-test-Client script covering all nine relevant login combinations — each demo account
succeeding under its own correct tab and landing on the right portal, each of the three accounts
rejected under each of the two wrong tabs (six mismatch cases) with the session confirmed never
established (a follow-up request to that role's portal still redirects to `/login/`, not through),
a genuinely wrong password still rejected as before, and a POST omitting `selected_role` entirely
still rejecting director credentials rather than defaulting past the check; a Playwright pass
confirmed the exact error-banner wording for both mismatch directions (catching the
`ROLE_LABELS`-vs-`ROLE_TAB_LABELS` wording mismatch — see Round 20 detail), confirmed the
previously-selected tab and its heading/demo-line stay active after a rejected login instead of
resetting to Agent, and confirmed correct tab+credentials logins still land on the right portal.
Round 21: a scripted backend test caught and confirmed the streak-freeze backfill-date bug fix
(see Round 21 detail) across a full 9-day simulated sequence, plus confirmed level-curve math,
one-spin-per-day enforcement, and deterministic weekly-challenge selection, all before any
template/view code was touched; `python manage.py check` clean; a scripted Django-test-Client pass
confirmed `/dashboard/` loads with all new context, reloads idempotently, `api_spin_wheel` awards
once and refuses a same-day second spin (per-agent, not global), and a non-agent account is refused
cleanly; a Playwright pass confirmed the Game Center tab (35-dot streak calendar, a non-blank
canvas-drawn wheel, all 3 weekly challenge cards), a live spin animating to and revealing the
server-reported prize, that result persisting correctly across a reload, and a clean 390×844 mobile
stack with no overflow; the Round 20 login-role regression suite was re-run unchanged and still
passes, confirming no cross-round regression. Round 22: a scripted backend test confirmed the
Clean Streak mechanic end to end — 3 approved sales in a row produce a streak of 3 and award
exactly the 3-streak milestone (+10 pts), a subsequent rejection drops the live streak to 0 and
resets the current-run bookkeeping while `longest_clean_streak_ever` correctly stays at 3,
`lifetime_points()` reflects the award, and `api_review_sale` sets `reviewed_at`; `python manage.py
check` clean after the model/migration changes; a scripted Django-test-Client pass confirmed
`api_spin_wheel` now 404s (route genuinely removed), `/dashboard/` contains no `spin-wheel` markup
and does contain `clean-streak` markup, and both `/analyst/` and `/director/` render their new
comparison sections without error; a full re-seed with the extended `_seed_sales()` (real
`reviewed_at` spread, ~8% rejection rate) followed by a Playwright pass at desktop and 390×844
mobile confirmed the 3-card Game Center layout with the Clean Streak card's progress bar and
milestone feed rendering correctly, the Analyst comparison table (including a correctly-rendered
"early data" pill on the just-started incentive), and the Director page's four new pieces
(turnaround/approval-rate stat chips, comparison table, Top Clean Streaks card) — all with no
horizontal overflow at either width tested. Round 23: a scripted check of `_goal_spectrum_bars()`
confirmed correct bar/lit counts for an in-progress goal (2/5 → 5 bars, 2 lit), an over-target goal
(6/5 → 5/5 lit, clamped not overflowing), a zero-progress goal (0/4 → 0 lit), a target past the
30-bar cap (40/100 → 30 bars, 12 lit), and a defensive `target=0` (returns `[]`, no
`ZeroDivisionError`); `python manage.py check` clean (no model changes this round); a
Django-test-Client render of `/dashboard/` confirmed `spectrum-meter`/`spectrum-bar`/
`spectrum-antenna` markup present for an agent with real goals and no leftover `pool` references
anywhere on the page; a full re-seed; then a Playwright pass at desktop and 390×844 mobile across
three agents — a mix of 3 complete + 6 in-progress goals (bars correctly blue vs. green-with-
glowing-antenna, over-target goals showing all bars lit), an agent with zero complete goals
(all-dim antennas, no stray "on air" pills), and the mixed case again at mobile width — all
rendered cleanly with no horizontal overflow. Round 24: a scripted check of `coverage_map()`
against hand-built goal dicts confirmed correct `zones_complete`/`overall_pct`/`fully_covered` for
a 2-zone mix (1 complete, 1 partial) and a safe zeroed-out result for an empty goal list; `python
manage.py check` clean (no model changes); a Django-test-Client render confirmed `coverage-map-
grid`/`coverage-zone`/`hex-tile`/`coverage-pct`/`coverage-detail` markup present; a full re-seed;
a Playwright pass confirmed three real states (57%-covered mixed agent with 4/9 zones complete,
a 43%-covered agent with 0/9 complete, and — via a one-off backend script that approved every
remaining sale for a fourth test agent — the 100%-covered/`fully_covered` state, which correctly
triggered the existing mystery-box/confetti/level-up celebrations on its own with no Round-24 code
involved) plus an actual **scripted click** on a rendered hex tile confirming `#coverage-detail`
updated to the exact expected zone text, not just that the click handler was wired up; desktop and
390px-mobile screenshots of the mixed-state agent showed the map reflowing to two columns on
mobile with no horizontal overflow, using the grid's existing `auto-fill` behavior with no new
mobile-specific CSS needed. (Coverage Map itself was removed one round later — see Round 25.)

Round 25: `python manage.py check` after the model change, `makemigrations` + `migrate` (migration
0008, additive-only); a scripted `sync_signal_launch()` test confirmed first-visit suppression (2
approved + 1 rejected sale on a never-synced agent → 0 returned, not 2, and the rejected sale
produced no satellite at all — `signal_launch_context()` correctly showed `count: 2`), correct
new-count detection on a subsequent visit after one more approved sale landed (→ 1), and a correctly
idempotent 0 on a third call with nothing new; a Django-test-Client render confirmed `signal-launch`/
`orbit-ring`/`satellite`/`launch-tower`/`signal-launch-detail` markup present (24 satellites for a
real seeded agent, hitting the cap) and confirmed every trace of `coverage-map`/`coverage-zone`/
`hex-tile` gone from the page; a full re-seed; a Playwright pass confirmed the resting orbit renders
correctly at desktop and 390px mobile with no horizontal overflow, a **programmatic click**
(`el.click()`, not Playwright's simulated pointer click — see Round 25 detail for why the simulated
click didn't work on a continuously-moving element) on a satellite correctly updated
`#signal-launch-detail` to that exact satellite's label; and, by priming one agent's
`last_seen_positive_event_at` via a real first dashboard load then adding one fresh approved sale
before a second load, confirmed `state.newSignalLaunches` read `2`, exactly 2 `.satellite` elements
carried the `.launching` class ~150ms into that second page load (caught genuinely mid-animation),
and the class was correctly removed again within 1.5 seconds via the `animationend` listener.

Round 26: `python manage.py check` clean and `makemigrations --check --dry-run` confirmed no
migration generated (no model change this round — `last_seen_positive_event_at` reused as-is); a
Django-shell sanity pass confirmed `tower_build_context()`/`sync_tower_build()` return the expected
shapes and `build_dashboard_context()` no longer carries a `signal_launch` key; a Django-test-Client
render confirmed `tower-build`/`tower-stack`/`tower-block`/`tower-base`/`tower-legend` markup
present and every trace of `signal-launch`/`orbit-ring`/`satellite`/`launch-tower` gone from the
page; a full re-seed; a Playwright pass confirmed an 18-block tower renders correctly at desktop and
390px mobile with no horizontal overflow — and, after one real iteration, no vertical overflow
either (a `getBoundingClientRect()` check on the stack vs. its container caught the initial 280px
container clipping a full 18-block stack, fixed by sizing to 320px and re-verified passing); an
ordinary Playwright click (no workaround needed, unlike Round 25's satellite) on a tower block
correctly updated `#tower-build-detail` to that exact block's label; and, by priming one agent's
`last_seen_positive_event_at` to just before its newest timeline event, confirmed
`state.newTowerBlocks` read `2`, exactly 2 `.tower-block` elements carried the `.falling` class
~150ms into that page load (caught genuinely mid-animation), and the class was correctly removed
again within 1.2 seconds via the `animationend` listener. A whole-project grep for
`signal_launch`/`signal-launch`/`SIGNAL_LAUNCH`/`satellite` after the round turned up nothing left
in application code.

Round 27: `python manage.py check` clean and `makemigrations --check --dry-run` confirmed no
migration generated (no model change this round — `last_seen_positive_event_at` reused as-is,
comment updated only); a Django-shell sanity pass confirmed `signal_river_context()`/
`sync_signal_river()` return the expected shapes and `build_dashboard_context()` no longer carries a
`tower_build` key; a Django-test-Client render confirmed `signal-river`/`river-packet` markup
present and every trace of `tower-build`/`tower-stack`/`tower-block`/`signal-launch`/`orbit-ring`/
`satellite` gone from the page; a full re-seed; a Playwright pass confirmed a 24-packet river renders
correctly at desktop and 390px mobile with no horizontal overflow (`.signal-river`'s
`overflow: hidden` intentionally clips packets currently positioned outside the visible band); a
direct motion check — reading every packet's `getBoundingClientRect().left` at two points one second
apart — confirmed all 24 of 24 packets had genuinely changed position, not just present in the DOM;
a **programmatic click** (`el.click()`, the Round 25 workaround needed again since packets are
continuously moving, unlike Round 26's resting tower blocks) on a river packet correctly updated
`#signal-river-detail` to that exact packet's label; and, by priming one agent's
`last_seen_positive_event_at` to just before its newest timeline event, confirmed
`state.newRiverPackets` read `2`, exactly 2 `.river-packet` elements carried the `.arriving` class
~150ms into that page load (caught genuinely mid-animation), and the class was correctly removed
again within 1.2 seconds via the `animationend` listener (confirmed reliable with no
`event.animationName` check needed, since the packet's other, infinite animation never itself fires
`animationend`). A whole-project grep for `tower_build`/`tower-build`/`tower-stack`/`tower-block`/
`TOWER_BUILD`/`newTowerBlocks` after the round turned up nothing left in application code.

## User's environment / support notes
Windows. As of Round 19, working in VS Code with a real Git-tracked local clone of the GitHub repo
(`renuka3094/spectrum-incentives`), pushing changes via VS Code's Source Control panel — Render
auto-redeploys on every push to `main`. Previously used the GitHub web uploader directly (does not
respect `.gitignore` — see the deployment-walkthrough section above); that limitation no longer
applies now that a real git client is in use. Self-described as knowing "only Python."

**Demo data goes stale with real time** (Round 9): if the dashboard ever shows "No active
incentive," run `python manage.py seed_data` (no `--flush` needed). Documented in the README too.

Reminder for future sessions: this cloud workspace is genuinely ephemeral — containers get
recycled between sessions. `venv/bin/python`/`venv/bin/pip` must be invoked directly since `source
venv/bin/activate` doesn't persist across separate Bash tool calls here. Leaves stale `manage.py
runserver` processes across tool calls — check `ps aux | grep runserver` and kill by PID directly.
The Django settings module for this project is `spectrum.settings` (not `spectrum_project.settings`
— the project package is `spectrum`, the checkout folder is `spectrum_project`; worth remembering
when running a standalone script with `django.setup()` outside `manage.py`, which already gets this
right via its own hardcoded default). Playwright + Chromium are pre-installed
(`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`, launch with
`executable_path="/opt/pw-browsers/chromium"`) — genuinely useful for visually verifying any UI
change here rather than guessing from reading CSS alone. This project's login page also enforces
(since Round 20) that the selected role tab matches the account's real role — a Playwright script
driving a non-Agent login must click the matching `.role-tab[data-role="..."]` before submitting,
or the login is rejected with a role-mismatch error rather than succeeding. Sharp edges learned the hard way:
(1) a `full_page=True` screenshot of a `position:fixed` element can produce a misleading artifact
— cross-check against `full_page=False` before reporting a bug found that way; (2) Django's
`{# comment #}` tag is single-line only — a comment spanning multiple lines silently stops being a
comment and renders as literal page text. Always use `{% comment %}...{% endcomment %}` for
anything longer than one line, and always re-screenshot after a template edit here to catch this
class of mistake immediately rather than downstream — this one recurred in Round 12 despite being
documented after Round 11, so treat it as a standing checklist item on every template edit, not
just a one-time fix; (3) role/permission logic (Round 12) is worth a scripted multi-account test
every time, not just a visual screenshot — a screenshot won't show you that the wrong account can
reach a page, only that the page it did reach looks fine; (4) **all of this project's visual
verification happens in Chromium** (the only browser available here) — a bug that's purely a
Chromium-vs-Safari/Firefox rendering difference (Round 13's button-appearance issue) will screenshot
as fine here and still be visibly broken for a real user. When a user reports something looking
wrong that a Chromium screenshot doesn't show, consider a cross-browser CSS default (appearance,
font rendering, flex/grid quirks) before assuming it's not reproducible. (5) **`ManifestStaticFilesStorage`
(or any hashed/manifest static storage) must never be the storage class used while `DEBUG=True`**
— it depends on a `staticfiles.json` manifest that only `collectstatic` writes, so once that's run
once (e.g. while testing a deploy config), local static edits silently stop taking effect, forever,
with no error and no obvious symptom beyond "my change isn't showing up." This was floated as a
theory in Round 13 and confirmed as the actual root cause in Round 15 — gate this storage setting
on `DEBUG` from the start in any future Django project that uses WhiteNoise or similar. (6) that fix
alone was necessary but not sufficient: **WhiteNoise's middleware serves from a `STATIC_ROOT`
snapshot taken at process start, independent of `STATICFILES_STORAGE`** — if a stale `staticfiles/`
folder exists on disk, WhiteNoise will keep serving it forever regardless of any storage-class fix,
so the middleware itself needs to be excluded from `MIDDLEWARE` when `DEBUG=True`, not just the
storage backend swapped. Caught only by deliberately planting a fake stale file and testing the
actual served bytes end-to-end, not by reasoning about the settings alone — worth doing that kind
of adversarial repro for any "is this actually fixed" question that's already had one failed fix.
(7) **a browser that has ever cached a static URL under a long-lived `Cache-Control` header will
not ask the server again for that exact URL, ever, no matter what changes server-side** — the only
reliable fix is to change the URL itself when the content changes (a cache-busting query string
tied to the file's own mtime, applied uniformly to every static include), rather than trying to
reason about or ask the user to clear whatever their specific browser decided to cache. (8) **a
layout that's supposed to keep one element exactly centered needs to be verified by measuring that
element's actual center pixel against the viewport's, not just by eyeballing a screenshot** — a
CSS Grid item that auto-places into the wrong (unnamed) column can still look roughly plausible at
a glance (right general position, right rough proportions) while being measurably off-center; this
project's Round 17 grid-column bug was caught only because the verification script computed and
printed the actual offset in pixels rather than relying on a human glance at a screenshot. (9) **a setting that
reads correctly in a code review can still do nothing at runtime** — `STATICFILES_STORAGE` looked
like exactly the right fix (it's the documented, commonly-referenced setting name) but this Django
version only ever reads the newer `STORAGES` dict, silently ignoring the legacy name with no
warning or error. The only way this was ever going to surface was by actually exercising the
`DEBUG=False` path end to end (run `collectstatic`, check for a manifest file and hashed
filenames, serve it with `gunicorn`) rather than trusting that a plausible-looking settings.py
change had taken effect — worth doing that concretely before telling a user "this is fixed" for
any setting whose effect can't be seen in the environment already being tested. (10) **delivered
prose (READMEs, docs) needs the same "does this reveal it was AI-assisted" scrutiny as code** —
removing "you"/"I" pronouns is necessary but not sufficient; phrases that name the collaboration
itself ("per the assignment," "the brief called for") are a stronger tell and need to be hunted
down explicitly, ideally by rereading the specific line the user points at rather than assuming a
voice pass caught everything. (11) **a new function added to a module that imports models
selectively (not `from .models import *`) needs its own import-completeness check** —
`insights.py`'s new `product_points_map()` referenced `Product` without it being imported, a
one-line miss that would have shipped as a live 500 on every dashboard load had a scripted
`Client().get()` smoke test not been run against every touched view before any visual/Playwright
pass (Round 19). Run that cheap check first, every round, before spending time on screenshots.
(12) **an accessibility fix (focus trap, keyboard handler) needs to be verified against the app's
own dynamic-DOM behavior, not just tested in isolation** — binding a modal's Escape-key listener to
the modal/backdrop element itself is the natural first instinct and works fine until something
inside the modal removes the currently-focused element from the DOM (this app does that routinely —
any AJAX-refreshed list, like the recent-submissions list, swaps its own innerHTML), at which point
the browser silently moves focus to `<body>` and a backdrop-scoped listener goes deaf with no
visible symptom. A `document`-level listener that looks up whichever modal is currently open is the
robust pattern for any future modal/dialog work in this codebase. Caught only because the
verification script exercised Escape *after* triggering a DOM-swapping action (Cancel), not before
— worth remembering to sequence interaction tests that way whenever a page has both a modal and
AJAX-refreshed content inside it. (13) **the `[hidden]` HTML attribute needs no CSS override at all
if the element toggled by it is simply never given an unconditional `display` property in the first
place** — Round 14 fixed a `[hidden]`-attribute bug reactively with an explicit `[hidden]{display:
none}` override; Round 19's `#cap-warning` element sidestepped the same class of bug proactively by
only ever setting color/border/padding/font rules on it, letting the browser's own UA-stylesheet
`[hidden]` default do the work unopposed. Prefer this proactive approach for any new
`hidden`-toggled element in this codebase going forward, and reserve the reactive override only for
an existing element that already has a conflicting unconditional `display` rule and can't easily
lose it. (14) **a deliberate, documented design decision can still be the wrong call once real usage
shows what it actually feels like** — Round 12's "the role tab is cosmetic, routing always follows
the real account" was a considered anti-spoofing choice, explained in two separate docstrings, not
an oversight; the user's Round 20 report ("even if I select agent... director credentials still
director panel is getting opened") is a direct, reasonable objection to that documented behavior,
not evidence it was ever buggy. Worth remembering for this project specifically: a `roles.py`/
`views.py` comment that says "this is intentional, here's why" is not immune to a later, equally
valid user request to do the opposite — and when that happens, update the rationale comments to
match the new behavior (Round 20 did this for both `roles.py`'s module docstring and
`SpectrumLoginView`'s class docstring), not just the code, so the next person reading them isn't
misled into "fixing" it back. (15) **two variables that are both "derived from a 1-day gap" can
still mean different calendar days, and reusing the wrong one compiles fine and often even passes a
shallow test** — Round 21's streak-freeze bug backfilled `today - 2 days` (the threshold
`last_login_date` must equal for a one-day gap to be detected at all) instead of `today - 1 day`
(the day that was actually skipped) into `AgentLoginDay`. Both variables are legitimately "about"
the same 1-day-gap scenario, which is exactly what made the mistake easy to write and easy to skim
past in review — the fix was to give the correct variable (`yesterday`) an unambiguous name and
reuse *it* specifically for the backfill, and to catch it with a test that asserts the *specific
date* of the backfilled row, not just that the streak counter came out right (a test that only
checks the counter would have passed with the bug still in place). Any future logic that
back-dates or back-fills a record from a "day N ago" calculation deserves this same
specific-value assertion, not just an aggregate/counter check. (16) **a ratio metric with a small
or shrinking denominator needs an explicit "not enough data yet" flag, not just a correct
formula** — Round 22's `effectiveness = points ÷ agents ÷ elapsed days` is the right metric for
comparing incentives fairly overall, but a brand-new incentive only a few days in has a tiny
`period_days` denominator that can make it look dramatically more "effective" than it will once it
runs its full course — confirmed directly against this project's own seeded data (a 3-day-old
incentive showing ~40+ pts/agent/day against ~4-5 for two completed prior months). The fix wasn't
to change the formula (it's still the right one once a fair amount of time has passed) but to
flag the specific rows where the denominator is too small to trust yet (`early_data`, `period_days
< 7`) rather than let a technically-correct-but-misleading #1 stand with no caveat — worth applying
the same "flag, don't hide or silently exclude" instinct to any future per-day/per-agent/per-unit
ratio stat added to this app, especially ones an Analyst or Director might act on. (17) **when a
mechanic explicitly needs to look nothing like the one it replaces (the user's own words here were
"not like spin"), the fix is architectural, not cosmetic** — Round 22 didn't reskin the spin wheel
with different art, it removed every trace of randomness (`random.choices`, a weighted prize
table, a once-a-day gate) and replaced it with a mechanic that reads its state entirely from
already-existing, already-verified records (`Sale.reviewed_at`, `AgentTaskCompletion`,
`AgentGoalBonus`) with zero stochastic input anywhere in the code path. When a user's complaint is
about a mechanic's *nature* (random vs. earned) rather than its look, treat that as a hard
constraint on the implementation, not just a design brief — a "streak" that still secretly rolled
dice under a different name would not have satisfied this request even if the numbers happened to
look similar.

## Suggested next steps (told to the user, not yet built)
1. Bespoke Analyst incentive-editing screen, replacing the current admin-linked placeholder (Round
   12 built the login/routing/overview page; the editing actions themselves still route to the
   Django admin). The equivalent Director *approval* screen was built in Round 19 — see that
   round's detail — so this is now the one remaining admin-linked placeholder of the two.
2. Still offered-but-declined so far: nearby-agent live pop-up notifications, random encouragement
   pop-ups, parallax header, collapsing Overview sections. (Daily login streak + a skill-based
   Clean Streak, weekly challenges, and XP levels were all offered and built across Rounds 21–22;
   the originally-built spin-the-wheel mechanic was explicitly removed in Round 22 on user request.)
3. If the user gets real commission numbers, replace `CASH_PER_POINT` in `insights.py` — this now
   also feeds the Round 22 Analyst/Director "est. value" incentive-comparison figure, not just
   `total_cash_earned()`, so a real rate would sharpen both at once.
4. If the user gets Charter's actual brand guidelines, swap the approximated `--accent` hex (app)
   and the landing page's `--navy`/`--blue` hexes (Round 18).
5. Possible refinement: a live-updating "you have N sales pending review" indicator (the Round 19
   Director queue shows this on the Director side; nothing yet shows the agent their own pending
   count outside the log-sale modal's recent-submissions list).
6. Consider making demo data self-healing (auto-seed "this month" if none active) so a deployed
   Render instance stays presentable between manual re-seeds. Not built; flagged as an option.
7. Leaderboard/Rewards/Goals tabs are balanced now rather than empty-looking, but still genuinely
   sparse in content (Leaderboard shows only 2 agents in Jordan's region) — seeding more agents
   per region, or adding a secondary card, would be the next-level fix if the user wants it fuller.
8. The login page's teaser banner is still built from `insights.public_teaser()` — worth checking
   periodically that it doesn't itself go stale/empty the same way the dashboard incentive did
   (Round 9); it's lower-stakes since the page still works fine with the teaser section just not
   rendering (`{% if teaser %}`), but worth knowing if the user asks about it looking sparse. The
   same applies to the Round 18 landing page's live stats card, which reuses the same function.
9. An `Incentive.status` field (`draft`/`pending_approval`/`approved`) so a Director could approve
   an *incentive* an Analyst set up, not just approve individual sales — currently there's no
   analyst→director incentive-approval loop, only the sale-approval one from Round 8/19.
10. If the user or their manager reviews this in a non-Chromium browser (Safari, Firefox), it'd be
    worth a spot-check there — this project's whole verification method has only ever run in
    Chromium (see Round 13 lesson #4), so a similar latent cross-browser issue could exist
    elsewhere and just hasn't been noticed yet.
11. The user offered, unprompted, to trim the README's feature list and "Why we did X" sections
    down to something terser/less exhaustive if that's wanted — not done yet (see Round 18 detail).
12. The Round 19 Director queue's Reject button has no "are you sure" confirmation — a misclick
    rejects a sale immediately (recoverable only by re-logging it as the agent, since there's no
    "un-reject" action). Not raised by the user; worth a quick confirm-dialog or undo toast if this
    becomes a real workflow rather than a demo. The same is now also true of a Clean Streak break —
    a misclicked Reject also resets an agent's current-run milestone bookkeeping, not just the sale.
13. The weekly challenge board's 6-template catalog only ever surfaces 3 at a time — if the user
    wants more variety over time, growing `WEEKLY_CHALLENGE_TEMPLATES` costs nothing structurally
    (the deterministic weekly `sample()` just picks 3 from however many exist).
14. `CLEAN_STREAK_MILESTONES`/`CLEAN_STREAK_MILESTONE_POINTS` (Round 22) are a first pass, not
    tuned against any real economy — worth revisiting the thresholds/point values once there's a
    sense of how often agents' sales actually get rejected in practice, the same open question
    Round 21 flagged for the (now-removed) spin wheel's prize weights.
15. The Round 22 `effectiveness` metric and `early_data` threshold (`period_days < 7`) are
    reasonable defaults, not numbers requested by the user — worth revisiting the 7-day cutoff, or
    exposing it as a configurable setting, once there's a sense of how long this org's incentives
    typically run.
16. The Round 23 "Signal Spectrum" bar heights (`GOAL_SPECTRUM_BAR_HEIGHT_CYCLE`) are a fixed
    cosmetic pattern, not tuned to anything — fine as-is, but if the user wants the meter to look
    less repetitive across many goals on one screen, a longer or more varied cycle is a one-line
    change with no other effects (bar height carries no data).
17. A colleague is apparently building portal features independently outside this session (the
    pool-ball/pocket board that prompted Round 23) — that code isn't in this project's zip or
    doc, so if the user later asks to reconcile or merge the two, a future session should ask to
    see that code/repo first rather than assuming it matches anything described here.
18. Round 24's Coverage Map deliberately shows zone-level detail on tile click (product/sold/
    target/points), not per-unit sale attribution (which specific sale lit which tile) — the data
    model doesn't currently track per-unit provenance cheaply, only per-goal totals. If the user
    wants "this tile = this specific sale," that needs a real per-unit event list built from
    ordered `Sale` rows, not just `product_goal_progress()`'s aggregate sold/target.
19. Between Rounds 23 and 24, the user hit `django.db.utils.OperationalError: no such column:
    agent_portal_agentprofile.last_spin_date` running `seed_data` locally — a partial pull of
    Round 21/22 files (some files updated, others, likely `models.py` or the `migrations/` folder,
    left on an older version) left their local code and local SQLite schema disagreeing about
    whether that Round-22-removed column exists. Not a bug in the delivered code — confirmed by
    the fact this session's own copy runs clean — but a recurring risk of this project's
    copy-files-by-hand delivery workflow, worth flagging to the user again if it recurs: the fix is
    always "make sure *every* file listed for the round is actually replaced, then delete
    `db.sqlite3` and rerun `migrate`+`seed_data`," never a partial patch.
20. Round 24 (Coverage Map) was built, fully verified, delivered, and rejected by the user one
    round later on taste/feel grounds, not a bug — worth remembering that this project's
    verification discipline (checks, tests, screenshots) proves a feature *works*, not that it
    *lands*. A future gamification round should weigh whether to check in on the *concept* before
    fully building it (a quick sketch/description) when the ask is this open-ended ("more
    interactive," "something unique"), rather than building a complete, polished first attempt on
    spec alone — Round 24 wasn't unreasonable given what was asked, but a lighter-weight check
    first might have saved a full round's work.
21. (Superseded twice over — applied to Signal Launch, then to Tower Build, neither of which exists
    as of Round 27.) Signal River's equivalent point: packets *are* color-coded by kind (sale =
    blue, task = green, goal = gold) plus a per-kind icon, carried forward unchanged from Tower
    Build, so this original Signal-Launch-era gap has stayed closed across two more replacements
    without being separately re-requested each time.
22. `SIGNAL_RIVER_MAX = 24` is an arbitrary cap (back up from Tower Build's 18, matching Signal
    Launch's original number — a flowing stream has more room than a vertical stack), not requested
    by the user — an agent with more than 24 lifetime positive events will simply never see their
    oldest ones in the river (older packets silently age out of the timeline slice as new ones push
    the cap, same "not shown" behavior every prior version of this mechanic had). There's no "+N
    more" indicator for this the way some other capped visuals in this app have one — worth adding
    if it comes up.
23. **Corrected from an earlier draft of this list, which had claimed Round 26 (Tower Build) "broke
    the pattern... and it landed" — it did not; Tower Build was rejected in Round 27 on essentially
    the same grounds as Coverage Map and Signal Launch before it.** The real lesson, now that three
    gamification rounds in a row have been rejected on taste/feel rather than bugs: asking the user
    to pick a concept via AskUserQuestion before building (done for Rounds 26 and 27 both) is
    necessary but was not, on its own, sufficient — Round 26's options still didn't share any
    constraint about *when* motion had to be visible, so a plausible-sounding option (a tower that
    animates once per event) still reproduced the same "mostly static" failure as Coverage Map two
    rounds earlier, just with a different skin. Round 27's AskUserQuestion added the specific
    constraint learned from that failure ("motion running continuously, all the time, not just on
    new events") directly into every option offered, rather than leaving it implicit. Worth treating
    *that* — naming the specific failure mode as an explicit constraint on the next round's options,
    not just offering alternatives in general — as the actual takeaway for any future round that
    follows a rejection in this project.
24. Signal River's packets are capped at a fixed 18s traversal duration for all of them (see
    `@keyframes river-flow` in `style.css`) — every packet moves at the same speed regardless of
    kind or recency. A future round could vary speed by kind (e.g. goal-hit packets travel slower,
    to linger longer as the most valuable event type) if the user wants event importance reflected
    in the motion itself, not just the color; not built since it wasn't asked for and risks making
    an already-continuous scene feel busier rather than clearer.

## Where the code lives
Built in this session's cloud workspace at /home/claude/spectrum_project (ephemeral — confirmed
across rounds 9–14 that the container can be fully recycled between sessions). The zip sent via
SendUserFile is the durable copy, most recently re-sent after Round 27 with Signal River (Tower
Build fully removed) — every earlier round's work (Round 23's "Signal Spectrum" Goals-tab redesign,
Round 22's Clean Streak mechanic and Analyst/Director incentive comparison, Round 21's daily
streak/weekly challenges/XP levels, Round 19's Director approval queue/smarter Log-a-sale
flow/accessibility pass, Round 20's login-page role-enforcement fix) is still included, same as
every previous zip. As of Round 19 the user also has their own durable copy via a real Git-tracked
local clone pushed to GitHub — arguably now the more authoritative source than this session's zip,
since it's what's actually deployed. **Given the real `OperationalError` a partial pull already
caused once (lesson 19 above), the simplest reliable path for the user's local clone at this point
is: replace every file in the Round 27 list below wholesale rather than trying to track which
specific lines changed across seven rounds of gamification work — no `migrate` needed this round
(Round 27 added no migration, same as Round 26), but still worth a `seed_data` re-run for a clean
demo state.**

Round 27 file list (current versions — these supersede every earlier round's copy of the same
file): `agent_portal/models.py` (comment-only change — no migration), `agent_portal/insights.py`,
`agent_portal/views.py`, `templates/agent_portal/dashboard.html`,
`templates/agent_portal/_signal_river.html` (new), `static/agent_portal/css/style.css`,
`static/agent_portal/js/dashboard.js`. One file needs actively **deleting**, not replacing, from
the user's local clone if it's there: `templates/agent_portal/_tower_build.html` — Round 26's
partial, dead now that nothing includes it (and, if either somehow survived that far, Round 25's
`_signal_launch.html` and Round 24's `_coverage_map.html` too — none of the three should exist in a
clone that's actually current). Unchanged since Round 22 and not part of this list: `admin.py`,
`seed_data.py`, `urls.py`, `analyst_dashboard.html`, `director_dashboard.html`,
`_incentive_comparison.html`, `_goals.html`. Migration-wise, the last new migration file is still
Round 25's `0008_agentprofile_last_seen_positive_event_at` — neither Round 26 nor Round 27 needed
one.

A future session continuing this work should ask the user whether to continue from their GitHub
repo (preferred, now that it's real git history) or re-upload a zip, and should expect to re-run
`migrate` + `seed_data` from scratch if this cloud workspace comes up empty again.
