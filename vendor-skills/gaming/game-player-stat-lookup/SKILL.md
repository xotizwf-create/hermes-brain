---
name: game-player-stat-lookup
description: Use when looking up public player profiles or statistics for games (Warface, trackers, leaderboards, clan/rank sites). Find the canonical tracker, verify the exact nickname/server/date freshness, extract only source-backed stats, and report caveats instead of guessing missing API data.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gaming, player-stats, trackers, warface, web-research]
    related_skills: [research-intelligence-workflows]
---

# Game Player Stat Lookup

## Overview

Use this skill for quick, source-backed lookups of public player stats on game tracker sites: player profiles, PvP/PvE summaries, rank/clan membership, achievements, match history, and weapon stats. The goal is to give the user a practical answer in plain language while making clear what the tracker actually says and how fresh the data is.

Many game stat sites are dynamic, protected from search crawlers, or have several similar/old domains. Do not rely on memory or a search result snippet. Open the tracker/profile, use the site's own search when needed, and verify the profile name/server before summarizing.

## When to Use

- User asks for a player's stats by nickname, gamer tag, clan tag, or profile URL.
- User names a tracker informally (for example: "вф тру статс" → Warface TrueSight / WF TrueSight).
- User wants a quick judgement on whether a player is strong, old, active, PvP/PvE-oriented, etc.
- User asks to compare two players or check profile evidence.
- User asks whether to take a Warface player into a roster/composition, whether they are an opener/openfragger, or which class to trial them on.

Don't use for:

- Private/hidden account data, doxxing, or anything requiring account compromise.
- Anti-cheat accusations beyond what public stats support. You can say stats look unusual, but avoid claiming cheating without authoritative evidence.
- Pure gameplay advice unrelated to a public profile lookup.

## Workflow

1. **Resolve the tracker and profile**
   - Search the web if the tracker name is informal or ambiguous.
   - Prefer the tracker site's own player search over search-engine snippets.
   - Verify exact nickname, server/region, and any displayed aliases.
   - If the old domain redirects to a placeholder, continue looking for the active domain rather than declaring the service unavailable.

2. **Record freshness/caveats first**
   - Many trackers show stale snapshots when a player has been inactive.
   - Capture the exact "data as of" timestamp if present.
   - If a tab says data is unavailable (for example weapon stats), say that explicitly and do not infer the missing data.

3. **Extract the useful summary**
   - Identity: nickname, server/region, clan, known old names.
   - Activity: last update/last activity, total playtime, first achievement/account age if shown.
   - Core stats: kills, deaths, K/D or У/С, matches/missions, win rate, completion rate.
   - Role/class split: favorite class and time/accuracy by class if visible.
   - Achievements/rank: counts and notable recent/rare achievements if easy to verify.
   - Missing tabs: mention unavailable sections briefly.

4. **Report in the user's language and style**
   - Start with the result, not the methodology.
   - Use bullets/key-value lines; avoid large tables in Telegram.
   - Keep a short human judgement at the end, clearly separated from factual stats.
   - Link the profile when available.

## Warface TrueSight Pattern

For Warface requests like "вф тру статс" or "TrueStats":

- The active tracker may be **Warface TrueSight** at `https://wfts.su/`.
- Use **Игроки → ПОИСК СТАТИСТИКИ** and enter the exact nickname.
- Profile URLs follow the shape `https://wfts.su/profile/<nickname>`.
- Important tabs: **Сводка**, **PvP**, **PvE**, **Оружие**, **Достижения**, **История игр**, **Тренды**.
- If the user asks specifically about **РМ / ranked matches**, first check what is public on **Сводка** (often only an approximate RP band such as `≈1800-2400 RP`). Then check **История игр** and **Тренды**, but note that TrueSight may lock match history, RM K/D dynamics, frequent teammates, and activity graphs behind VIP. Do not invent ranked-only K/D from general PvP stats.
- If the player is inactive, TrueSight may show: "Игрок долгое время не появлялся... данные по состоянию на ...". Include this caveat prominently.
- Weapon stats can be unavailable even when PvP/PvE stats exist. Report the site's message rather than trying to reconstruct weapons from achievements.
- When the user gives a gameplay-style hypothesis (e.g. “любит штурмы”, “сидит крысит”, “он авик”, “жёсткий или нет”), use it as an interpretation lens only: compare class time, win rate, K/D, accuracy, headshot share, mines, support actions, and RP range, but label the conclusion as a soft verdict, not a fact.
- For Warface role judgements, include a short role-specific verdict instead of only raw stats: sniper = line holding/accuracy/positioning, medic = revives/healing/close-range risk/team value, engineer = mines/utility/headshot pressure, rifleman = volume/accuracy/headshots.
- If the user is evaluating a player for a roster, add a practical recruitment verdict: **take / test / avoid**, best class to trial, backup class, and what to verify in scrims/RM (current form, comms, tilt, first-contact discipline, team play). Do not recommend immediate core placement solely from public tracker stats, especially when history/trends are VIP-locked or the snapshot is stale.
- When the user asks whether a Warface player “won tournaments” or has esports history, check **Достижения** on TrueSight for tournament/league achievement evidence (e.g. Astrum Junior League, Clans Cup, Battle Cup, Fast Cup, Warface Open Cup, CyberWarface, K.I.W.I., “Синдикат”). Phrase these carefully: achievements often prove **participation**, not prize placement or victory, unless the achievement text explicitly says winner/champion.

See `references/warface-truesight.md` for a compact extraction checklist, role-specific interpretation notes, roster/openfragger evaluation notes, RM caveats, and example fields.

## Common Pitfalls

1. **Using an old/dead domain as final evidence.** If one WF stats address redirects to a placeholder, search for the current tracker/domain.

2. **Confusing PvP and PvE K/D.** Warface TrueSight shows separate У/С for PvP and PvE; label them clearly.

3. **Ignoring stale snapshots.** A profile with old data should be described as a historical snapshot, not current live stats.

4. **Overclaiming skill level.** K/D, win rate, class time, and achievement counts can support a soft judgement, but they do not prove cheating, boosting, or exact current skill.

5. **Hallucinating unavailable tabs.** If the tracker says weapon stats/history are unavailable, say so and stop there.

## Verification Checklist

- [ ] Exact nickname and server/region match the user's target.
- [ ] Profile URL is included if public.
- [ ] Data freshness timestamp/caveat is included when shown.
- [ ] PvP and PvE stats are separated and labeled.
- [ ] Missing/unavailable sections are explicitly marked unavailable.
- [ ] Final judgement is phrased as interpretation, not fact beyond the stats.
