# Brain index/autocommit blockers

Use this reference when `scripts/build_section_index.py` or an automatic brain commit fails while updating `/root/.hermes/agent-knowledge`.

## Symptoms

- `TypeError: sequence item N: expected str instance, int found` from `doc_label()` or tag joining.
- `section-index.md is stale — run: python scripts/build_section_index.py` after a seemingly successful edit.
- Push rejected with `fetch first` after a local brain commit.
- `git rebase --continue` fails with `Terminal is dumb, but EDITOR unset`.

## Durable fixes / workflow

1. Inspect the file named in the traceback and its frontmatter.
2. Make frontmatter schema-safe:
   - Quote numeric-looking tags: `tags: ["217", hermes]`, not `tags: [217, hermes]`.
   - Add required frontmatter to indexed docs that are missing it.
   - Do not store secret values; use `secret_refs` only.
3. Rebuild and verify the index before validation:
   ```bash
   python3 scripts/build_section_index.py \
     && python3 scripts/build_section_index.py --check \
     && python3 scripts/validate.py
   ```
4. If you then append to `logs/changelog.md`, rerun the same index+validation command. The changelog is indexed too, so it can make `section-index.md` stale again.
5. Commit/push. If push is rejected because remote advanced:
   ```bash
   git pull --rebase
   # resolve conflicts, usually both changelog entries should be kept under the same date
   python3 scripts/build_section_index.py \
     && python3 scripts/build_section_index.py --check \
     && python3 scripts/validate.py
   git add -A
   GIT_EDITOR=true git rebase --continue
   git push
   git status --short
   ```

## Pitfalls

- Do not treat the first fixed traceback as the whole problem; index rebuild can reveal the next invalid document.
- Do not forget to rerun index generation after changelog conflict resolution.
- Do not mix unrelated dirty files into a brain commit unless they are explicitly the accumulated approved brain changes being unblocked; otherwise stop and separate them.
