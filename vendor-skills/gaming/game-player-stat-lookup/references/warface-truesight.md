# Warface TrueSight extraction checklist

Use for Warface player-stat requests such as "вф тру статс", "TrueStats", "WF TrueSight", or a Warface nickname.

## Current tracker

- Active site observed: `https://wfts.su/` (Warface TrueSight)
- Player search path: home page/navigation **Игроки** → input **Позывной персонажа** → **ИСКАТЬ**
- Direct profile shape: `https://wfts.su/profile/<nickname>`

## Fields to capture

### Profile/Summary

- Nickname and server/region
- Tracker freshness warning, especially: data stopped updating because the player has been inactive
- Player orientation line, e.g. "PvP-игрок, предпочитающий ..."
- Clan status
- Known previous nicknames
- First achievement timestamp
- Total match duration and total time in game
- Longest match

### PvP tab

- Kills / deaths / У-С
- Matches played
- Wins / losses / draws
- Win rate
- Time in PvP
- Shots and hits
- Mines/melee/team/self stats if useful
- Favorite class and class breakdown: time, accuracy, headshots
- Useful derived metrics when judging style: overall accuracy, kills/deaths per match, kills/deaths per hour, class time share, headshots as a share of hits, and support actions per hour when visible. Use an actual calculation tool for arithmetic; do not do it mentally.
- For support-oriented profiles, capture the summary support counters if shown: revived players, restored HP, restored armor, and ammo replenished. These can matter more than pure K/D for judging medics/team players.

### Ranked matches / РМ

- Summary may expose only the approximate RM band (for example `≈1800-2400 RP`). Capture it exactly and say it is approximate.
- **История игр** contains recent matches but can require VIP; if locked, state that recent RM matches are not publicly visible.
- **Тренды** can include RM K/D dynamics, match counts by day, frequent teammates, and achievement heatmaps, but can require VIP; if locked, do not claim current RM form.
- If only general PvP stats are open, phrase ranked conclusions as cautious interpretation: “по открытым данным”, “косвенно”, “похоже”, not as definitive РМ-stat facts.
- For style reads like “штурм”, “крысит”, “позиционер”, compare: class preference/time share, K/D vs win rate, RP range, mines, accuracy/headshot share, and whether the preferred class is actually штурмовик or another class such as инженер.
- For roster/recruiting reads (“брать в состав?”, “каким классом?”, “опенфрагер?”), do not stop at “жёсткий/не жёсткий”. Add a decision section with:
  - **take/test/avoid** recommendation and confidence level;
  - best class to trial and backup class, based on time share + role-specific quality signals;
  - whether the player looks like a true opener, second entry/trade player, sniper/picker, anchor, or flexible fill;
  - concrete trial checks: current form, comms, tilt, ability to follow calls, first-contact timing, trade discipline, and performance against strong stacks.
- Openfragger interpretation: high kill tempo + meaningful deaths + rifleman/engineer time + low mine reliance supports an opener/entry read; sniper-heavy profiles usually imply “picker/line opener” rather than classic entry; strong K/D with moderate deaths can mean second number or positional player rather than first-in entry.
- If TrueSight history/trends are VIP-locked or the snapshot is stale, avoid “take straight into core” as a hard recommendation. Prefer “take on test” and explain what the test must prove.

### PvE tab

- Kills / deaths / У-С
- Missions played / completed / failed
- Completion rate
- Signs used
- Time in PvE
- Shots and hits
- Favorite class and class breakdown
- Mission difficulty completion rows only if the user asks for detail

### Achievements tab

- Counts: значки, жетоны, нашивки
- Data freshness timestamp for achievements can differ from profile/PvP/PvE timestamp
- Mention a few notable achievements only if useful; don't dump the whole list

### Tournament / esports evidence

- If search engines are blocked by CAPTCHA or return noisy results, do not stop: TrueSight achievements can still provide public tournament evidence.
- On **Достижения**, scan achievement titles/descriptions for tournament names and words like `турнир`, `Cup`, `League`, `Open Cup`, `CyberWarface`, `Clans Cup`, `Battle Cup`, `Fast Cup`, `Astrum`, `K.I.W.I.`, `Синдикат`, `чемпион`.
- Treat most such achievements as **participation evidence** unless the description explicitly says winner/champion/prize place. Example: “Стать участником турнира …” = participated, not won.
- If browser snapshots are huge, use the page DOM to filter link text / achievement blocks for these terms, then report only notable tournament evidence and dates.

### Weapon tab

- If the page says "Статистика оружия недоступна", report that. Do not infer weapon usage from achievement titles unless the user explicitly asks for a rough clue.

## Role-specific interpretation notes

Use these as soft judgement lenses after the factual stats and caveats:

- **Снайпер / авик**: prioritize sniper time share, sniper accuracy, K/D, win rate, and whether the profile suggests holding lines vs. aggressive duels. If weapon stats/history are unavailable, do not name a specific rifle or current RM behavior.
- **Медик**: K/D should be judged together with revives, restored HP/armor, win rate, and low/high melee count. A medic with moderate K/D, high win rate, and many revives can be a strong team player even if not a pure aim demon.
- **Штурмовик**: compare class time share, general accuracy, headshot share, kills per hour, and win rate. Avoid treating "favorite class" alone as proof of style if another class has comparable time.
- **Инженер**: check mines, headshots, accuracy, and class time share. High mine kills suggest trap/utility play; low mines with good headshot share points more toward direct dueling.
- **РМ/current form**: if **История игр** and **Тренды** are VIP-locked, explicitly say current ranked form is not public and keep the verdict to “по открытым данным”.

## Output pattern for Telegram

```text
Нашёл профиль: <url>
Важно: данные старые/свежие — <timestamp/caveat>.

## <nickname> — краткая сводка
- Сервер: ...
- Клан: ...
- Любимый класс: ...

## PvP
- Убийства: ...
- Смерти: ...
- У/С: ...
- Побед: ...

## PvE
- Убийства: ...
- Смерти: ...
- У/С: ...

## Вывод
<1 short paragraph interpreting the stats, clearly as judgement>
```

## Interpretation guardrails

- K/D around 1.0-1.3 in PvP is usually "normal/working" rather than elite by itself.
- High win rate can reflect team play, mode choice, or coordinated stacks; don't treat it as pure mechanical skill.
- Old snapshots are not reliable evidence of current activity or current skill.
