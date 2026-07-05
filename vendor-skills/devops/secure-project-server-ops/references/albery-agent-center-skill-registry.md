# Albery Agent Center — adding a per-agent skill through the GitHub registry

Use this when the owner asks to give an Albery subagent a durable behavior/skill (for example the lawyer agent should draft contracts by first researching strong examples). Albery Agent Center's source of truth is the GitHub-backed `agent_knowledge/` registry in the production checkout, not an ad-hoc note in the database.

## Pattern

1. Load the Albery project card first and use the secure project `.env` for SSH. Do not print credentials or full environment values.
2. On the production checkout (`/var/www/albery`), inspect the live agent slug with the app helpers rather than trusting the visible UI name. Historical slugs may be misleading: the visible `Агент-юрист` can live under the old slug/manifest `agent-sklad`.
3. Put reusable behavior in a shared skill file:
   - `agent_knowledge/skills/<skill-slug>/SKILL.md`
   - include normal frontmatter (`name`, `version`, `description`, tags) and a rich body with trigger, workflow, pitfalls, and verification.
4. Connect the skill in the agent manifest:
   - `agent_knowledge/agents/<agent-slug>.yaml`
   - the `skills:` entry must use the registry id form: `skill:<skill-slug>`.
   - A bare `<skill-slug>` in the manifest is not enough; `_load_agents_full()` will expose it as linked, but `agent_selected_knowledge()` will not match `_hermes_skills()` ids.
5. Verify before reporting success:
   ```python
   import os, sys
   from pathlib import Path
   os.chdir('/var/www/albery')
   for line in Path('.env').read_text(errors='ignore').splitlines():
       if line.strip() and not line.strip().startswith('#') and '=' in line:
           k, v = line.split('=', 1)
           os.environ.setdefault(k.strip(), v.strip().strip('"\''))
   sys.path.insert(0, '.')
   import agent_center
   agent_center._agent_cache_bust()
   agent = agent_center._agent_by_slug('<agent-slug>')
   print(agent.get('linked_skill_ids'))
   print(agent_center.agent_selected_knowledge(agent))
   ```
   The selected skills must contain the new skill title/description.
6. Commit and push on the live branch, respecting the Albery deploy rules. Restart only `albery.service` if the running process must reread the registry, then verify `systemctl is-active albery.service`, the listening port, and a local page/API response.
7. Update `/root/.hermes/agent-knowledge/projects/albery/agent-center.md` with the durable project-specific fact: visible agent name, actual slug, skill id/path, commit, and verification result.

## Example: lawyer agent contract drafting skill

For the legal drafting request, the durable skill was:

- file: `agent_knowledge/skills/legal-contract-drafting/SKILL.md`
- manifest: `agent_knowledge/agents/agent-sklad.yaml`
- required manifest id: `skill:legal-contract-drafting`
- intended behavior: before drafting a contract, find strong examples/legal basis, then draft, self-check legal structure, risks, placeholders, VAT/payment/timing/acceptance/liability, and clearly state limitations.

## Pitfalls

- Do not create a local-only Hermes skill and assume Albery subagents will see it; they read the Albery registry/manifests.
- Do not rely on the UI display name to derive a slug.
- Do not stop at a Git commit: verify `agent_selected_knowledge()` actually returns the skill. This catches the missing `skill:` prefix bug.
- Do not dump secrets while running remote Python; parse `.env` and set environment variables in memory only.
