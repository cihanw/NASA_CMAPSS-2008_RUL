# Task Plan

- [x] Inspect the local git status, remote target, and current project layout.
- [x] Confirm the current FD002 preprocessing script path and notebook workflow.
- [x] Update `.gitignore` so it only ignores `AGENTS.md`.
- [x] Rewrite `README.md` in English for the current FD002 workflow.
- [x] Keep machine-local or GitHub-size-blocking files out of the commit without changing repository `.gitignore`.
- [x] Run verification with the local virtual environment.
- [ ] Stage the intended local project version.
- [ ] Commit the local project version.
- [ ] Push `main` to GitHub so the remote branch reflects the local project state.

## Review

- `python -m pip check` passed inside `.venv`.
- `python preprocess/fd002_sensor_selection_and_clustering.py` passed inside `.venv`.
- The FD002 preprocessing run produced 53,759 train rows, 33,991 test rows, `final_k=6`, and best silhouette at k=6.
- Generated `reports/`, `artifacts/`, `.venv/`, and `.DS_Store` files are kept out through local git exclude; repository `.gitignore` only contains `AGENTS.md`.
- Commit and push are still pending.
