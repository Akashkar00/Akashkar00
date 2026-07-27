# SETUP — manual steps

Everything in this list has to be done by a human, in a browser or a terminal.
Do them **in order** — later steps depend on earlier ones.

Repo: `Akashkar00/Akashkar00`, branch `main`.

---

## 1. Copy the repo contents into `Akashkar00/Akashkar00`

The profile repo **already exists** and already has an old `README.md`. Copying
this folder in will **replace** that README — that is intended. Nothing else in
the old repo is preserved by this process, so if there is anything in there you
want to keep, grab it first.

- Copy the full contents of this folder (`README.md`, `assets/`, `parts/`,
  `.github/workflows/`, `SETUP.md`) into your local clone of
  `Akashkar00/Akashkar00`.
- Commit and push to `main`.
- Open `https://github.com/Akashkar00` and confirm the new README is rendering.
  Some pieces will still be broken at this point (stats cards, snake) — that is
  expected until steps 3 and 5 are done.

---

## 2. Create a GitHub classic Personal Access Token

1. GitHub → your avatar → **Settings** → **Developer settings** →
   **Personal access tokens** → **Tokens (classic)** → **Generate new token
   (classic)**.
2. Note: something like `readme-stats-pat`.
3. Expiration: **No expiration** (otherwise the stats cards silently die the day
   it expires).
4. Scope: tick **`repo`** (the whole top-level `repo` box). Nothing else is
   needed.
5. Generate, then copy the token **immediately** — GitHub will never show it
   again.

> **Treat this token as a high-value secret.**
> The `repo` scope gives full **read AND write** access to **every private
> repository you own or can access** — the token can clone your private code,
> push commits, and delete branches. It is functionally a password for all your
> repos.
>
> - Never paste it into a public repo, an issue, a gist, a screenshot, a Discord
>   message, or a chat with an AI assistant.
> - Only ever paste it into the Vercel environment-variable field in step 3.
> - If you think it leaked, revoke it at
>   **Settings → Developer settings → Tokens (classic)** and generate a new one.

---

## 3. Deploy the `github-readme-stats` fork to Vercel

The public `github-readme-stats.vercel.app` instance is shared by everyone and
is permanently rate-limited. You need your own instance.

1. Fork <https://github.com/anuraghazra/github-readme-stats> to your account.
2. Go to <https://vercel.com> → sign in with GitHub → **Add New… → Project** →
   import your fork.
3. Before clicking Deploy, open **Environment Variables** and add:
   - **Name:** `PAT_1`
   - **Value:** the classic PAT from step 2
   - Apply to Production (Preview/Development too is fine).
4. Deploy. Wait for the build to go green.
5. Copy your production domain, e.g. `akash-readme-stats.vercel.app`.
6. Open `README.md` and replace **every** occurrence of `YOUR-INSTANCE` with
   that domain. Check the whole file — the placeholder appears in more than one
   card URL.
   ```
   https://YOUR-INSTANCE/api?username=Akashkar00...
   →
   https://akash-readme-stats.vercel.app/api?username=Akashkar00...
   ```
7. Commit and push. Confirm the stats cards now render on your profile.

---

## 4. Give Actions write permission — on the REPOSITORY

The snake workflow needs to push a generated branch, so it needs write access.

Go to:

```
https://github.com/Akashkar00/Akashkar00/settings/actions
```

→ **Actions** → **General** → scroll to **Workflow permissions** → select
**"Read and write permissions"** → **Save**.

> **This is the repository's settings page, not your account settings.**
> It is the tab labelled *Settings* along the top of the
> `Akashkar00/Akashkar00` repo page — **not** the *Settings* under your profile
> avatar in the top-right corner. The account-level page has a similar-looking
> Actions section and changing it there will do nothing for this repo. If the
> URL in your address bar does not contain `/Akashkar00/Akashkar00/settings/`,
> you are on the wrong page.

---

## 5. Run the snake workflow once, and wait for green

The contribution-snake images in the README point at an `output` branch.
**That branch does not exist yet.** It is created by the first successful run of
the workflow — until then the snake images will 404 and show as broken.

1. Repo → **Actions** tab.
2. Left sidebar → **Generate Snake**.
3. **Run workflow** → branch `main` → **Run workflow**.
4. **Wait for the run to finish with a green check.** Roughly 30–60 seconds.
   A yellow dot means still running; a red X means it failed (almost always
   because step 4 was skipped or done on the wrong settings page — fix that and
   re-run).
5. Confirm an `output` branch now exists in the branch dropdown.
6. Hard-refresh your profile page. The snake should animate.

After this first run the workflow re-runs on its own schedule; you never have to
trigger it manually again.

---

## Troubleshooting

### (a) "I edited the SVG and pushed, but the profile looks exactly the same"

This is almost always **CDN cache**, not a broken file. GitHub serves README
images through `camo` and caches them aggressively — your change is usually
already live, you just aren't being served it.

Verify what is actually on the server, bypassing cache with a junk query string:

```
https://raw.githubusercontent.com/Akashkar00/Akashkar00/main/assets/banner-dark.svg?v=999
```

Open that, **view source**, and search for the hex colour you changed
(e.g. `22D3EE`, `10B981`, `A78BFA`). If your new colour is in there, the file
is fine and you are looking at a cached copy — bump the `?v=` number, wait a
few minutes, and hard-refresh (Cmd+Shift+R). If the old colour is still there,
your commit didn't land — check `git log` and that you pushed to `main`.

**Also check your colour theme.** The `-dark` assets are wrapped so they only
render for viewers in **dark mode**; the `-light` assets only render in light
mode. If you are viewing GitHub in light theme, editing `banner-dark.svg` will
correctly produce no visible change. Switch theme
(Settings → Appearance) or edit the other file.

### (b) Snake images show as broken / 404

The workflow has not completed a green run yet, so the `output` branch it pushes
to does not exist. Go back to **step 5** and run it. If the run goes red, the
cause is nearly always **step 4** — repository workflow permissions are still
"Read-only", or they were set on the account settings page instead of the repo
settings page.

### (c) Stats cards say "Maximum retries exceeded" / "rate limit exceeded"

You are hitting the **public** github-readme-stats instance, which is shared and
permanently throttled. It means the `YOUR-INSTANCE` placeholder was not
substituted everywhere.

- Search `README.md` for `YOUR-INSTANCE` — every hit is a broken card.
- Also check for any leftover `github-readme-stats.vercel.app` URLs.
- Replace them all with your own Vercel domain from step 3, commit, push.
- If the URL *is* correct and it still rate-limits, your Vercel deployment is
  missing `PAT_1`, or the token was revoked/expired. Re-add the env var in
  Vercel and **redeploy** — env var changes do not apply to an existing
  deployment until you redeploy it.
