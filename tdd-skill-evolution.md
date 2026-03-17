# TDD Skill Evolution

## Goal
Evolve `tdd-workflow` into an AI-paired TDD skill where the human defines what and why, and the AI drives tests-first execution with Python and `pytest`.

## Tasks
- [x] Audit current `tdd-workflow` copies and identify gaps -> Verify: all target files are listed and compared before editing.
- [x] Rewrite the canonical skill content around Navigator/Architect and Pilot/AI roles -> Verify: the new text defines roles, RED/GREEN/REFACTOR, edge cases, and Python/`pytest` defaults.
- [x] Sync the workspace and global skill copies -> Verify: `.opencode/skills/tdd-workflow/SKILL.md` and `../../../.config/opencode/skills/tdd-workflow/SKILL.md` share the same content.
- [x] Sync the `Crafting-Table` repo copies -> Verify: `_dest_Crafting-Table/.agent/skills/tdd-workflow/SKILL.md` and `_dest_Crafting-Table/.kilocode/skills/tdd-workflow/SKILL.md` share the same content.
- [ ] Review git diff, commit on `chore/platform-architecture-pack`, and push to `origin` -> Verify: `git status` is clean except for the new commit and the branch is ahead of remote.

## Done When
- [x] The skill explicitly enforces tests before production logic.
- [x] The human/AI responsibility split is clear and reusable.
- [x] Python + `pytest` guidance covers fixtures, mocks, and edge cases.
- [ ] The repo changes are committed and pushed.

## Notes
- The same skill text is intentionally mirrored across workspace, global, and repo-specific locations.
- Commit and push are deferred until after diff review.
