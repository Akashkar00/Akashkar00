## Self-hosting the stats cards

The public `github-readme-stats` instance is shared by thousands of profiles and constantly returns "API rate limit exceeded", so the cards below render as broken images unless you run your own copy on Vercel.

1. **Create a GitHub classic token.** Go to Settings → Developer settings → Personal access tokens (classic) → Generate new token (classic), select the `repo` scope, and set expiration to *No expiration*. Copy the token immediately — GitHub will never show it again — and never paste it into a README, an issue, a commit, or anywhere else public.
2. **Fork** [`anuraghazra/github-readme-stats`](https://github.com/anuraghazra/github-readme-stats).
3. **Set up Vercel:** go to [vercel.com](https://vercel.com), sign up with GitHub, choose the **Hobby** (free) plan, then **Add New Project** and import your fork.
4. **Add the environment variable** `PAT_1` with the token from step 1 as its value, then click **Deploy**.
5. **Replace `github-readme-stats.vercel.app`** in the URLs below with the Vercel domain you get back (e.g. `github-readme-stats-abc123.vercel.app`).

<p align="center">
  <a href="https://github.com/Akashkar00">
    <img width="100%" src="https://streak-stats.demolab.com?user=Akashkar00&hide_border=false&background=0A101F&border=1E2A44&stroke=1E2A44&ring=10B981&fire=10B981&currStreakLabel=22D3EE&sideLabels=22D3EE&currStreakNum=C9D4E8&sideNums=C9D4E8&dates=C9D4E8" alt="GitHub streak stats" />
  </a>
</p>

<!-- NOTE: these two cards currently point at the PUBLIC github-readme-stats
     instance so the profile renders immediately. That instance is shared by
     thousands of users and intermittently returns "API rate limit exceeded",
     which shows up as a broken image. Follow the steps above, then replace
     `github-readme-stats.vercel.app` with your own Vercel domain. -->

<p align="center">
  <a href="https://github.com/Akashkar00">
    <img width="49%" src="https://github-readme-stats.vercel.app/api?username=Akashkar00&show_icons=true&hide_rank=true&count_private=true&include_all_commits=true&hide_border=false&bg_color=0A101F&title_color=22D3EE&text_color=C9D4E8&icon_color=10B981&border_color=1E2A44" alt="GitHub stats" />
  </a>
  <a href="https://github.com/Akashkar00">
    <img width="49%" src="https://github-readme-stats.vercel.app/api/top-langs?username=Akashkar00&layout=compact&langs_count=8&hide_border=false&bg_color=0A101F&title_color=22D3EE&text_color=C9D4E8&icon_color=10B981&border_color=1E2A44" alt="Top languages" />
  </a>
</p>

`hide_rank=true` is set on purpose. The rank badge is heavily stars-weighted, so for a newer account — this one was created in October 2025 and has 0 followers — it grades social reach rather than engineering, and reads far worse than the underlying work deserves. Hiding it keeps the card honest about what it can actually measure.
