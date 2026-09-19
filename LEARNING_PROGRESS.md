# OrderFlow QA Automation Learning Progress

## Current lesson

- Phase: Phase 0 — Understand and verify the system under test
- Lesson: Lesson 1 — Repository and architecture inspection
- Status: In progress
- Current objective: Understand the application and confirm its local runtime components.

## Roadmap

- [ ] Phase 0 — Understand and verify the system under test
- [ ] Phase 1 — Test strategy and planning
- [ ] Phase 2 — Python and pytest foundations
- [ ] Phase 3 — Professional framework architecture
- [ ] Phase 4 — REST API testing
- [ ] Phase 5 — PostgreSQL database testing
- [ ] Phase 6 — Playwright UI automation with Python
- [ ] Phase 7 — Cross-layer integration and E2E testing
- [ ] Phase 8 — Framework reliability and reporting
- [ ] Phase 9 — Docker
- [ ] Phase 10 — GitHub Actions and CI/CD
- [ ] Phase 11 — Company-style quality engineering practices
- [ ] Phase 12 — Portfolio completion

## Phase 0 lessons

- [x] Inspect the repository structure
- [x] Identify the frontend, backend, and database components
- [x] Establish and merge the OrderFlow application baseline
- [ ] Start the complete application locally
- [ ] Verify the health endpoint and Swagger
- [ ] Log in as administrator and staff
- [ ] Explore products, customers, and orders
- [ ] Inspect the PostgreSQL schema and relationships
- [ ] Complete one order workflow manually
- [ ] Document workflows, business rules, risks, and testability observations

## Important decisions

- Application code and QA framework work will use separate Git commits and branches.
- API tests will eventually be the main automation layer.
- PostgreSQL will be used directly; SQLite and mocked persistence will not replace it.
- Test data must not damage seed or development data.
- Development password reset must remain disabled outside local training environments.

## Commands learned

- `git status`
- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- `git switch -c <branch-name>`
- `git pull --ff-only origin main`
- `git merge --ff-only main`
- `git diff --cached --stat`
- `git diff --cached --check`

## Problems encountered

### Application code existed only as uncommitted files

Resolution: created an application-baseline branch, reviewed and verified the staged files, committed them, pushed the branch, and merged pull request #1.

### Documentation branch was created from an outdated commit

Resolution: switched to the branch and fast-forwarded it to the synchronized local `main`.

### `rg` was unavailable in the interactive terminal

Resolution: used the built-in macOS `grep` command instead of installing an unnecessary dependency.

## Skills completed

- Read basic Git status and history
- Distinguish tracked, modified, untracked, staged, and ignored files
- Create a focused feature branch
- Understand that a branch points to the current commit when created
- Fast-forward a branch safely
- Review staged files before committing
- Push a branch and merge it through a pull request

## Remaining work

Continue Phase 0 by starting and manually exploring the complete OrderFlow system.
