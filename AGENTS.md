# AGENTS.md

## Git Workflow Policy (strict)

- Never commit or push directly to `main`. All work happens on a new branch (`git checkout -b <descriptive-name>`).
- Never run `git push origin main`, `git merge` into `main`, or `git commit` while on `main`, unless Angel explicitly asks for it in that specific moment.
- If asked to make changes while on `main`, create/switch to a branch first, then proceed.
- Merging a branch into `main` (including via PR) requires Angel's explicit approval at that time — do not assume standing approval from a past instruction.
