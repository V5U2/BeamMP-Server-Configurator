# Agent Notes

- After implementing changes that affect the running app, rebuild and restart the local Docker containers so the user can test the updated behavior.
- After significant feature, configuration, or behavior changes, update `README.md` so the documentation stays aligned with the current app.
- Keep `example.env` and any documented environment variable sections in `README.md` updated whenever configuration changes.
- Add or update automated tests for new features and behavior changes so coverage keeps pace with the code.
- Keep GitHub release automation aligned with repo changes. If versioning, release tagging, published image behavior, or deployment expectations change, update the release workflows and documentation.
- Use Conventional Commits for commit messages: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `perf:`, `build:`, and `ci:`. Use `!` or `BREAKING CHANGE:` for breaking changes so release automation can classify them correctly.
- Use SemVer tags and GitHub Release names in the form `vX.Y.Z`.
