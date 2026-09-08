# Validation — 2026-09-08

Verified in the development container (Linux / Python 3.12 / Node 22+):

- `python -m pytest -q`: **20 passed**. Covers all five roles, exclusions, duplicate/contradictory draft input, replacement of the user's own hovered slot, small win-rate samples, position isolation, hover weighting, lane context, manual hero-pool persistence, missing credentials, origin validation, queue/account/time-window isolation, image validation, and structured vision output with a mocked provider.
- `npm run typecheck`: passed for the local React application and its imported components.
- `npm run build:local`: production Vite build passed.
- Sites/Vinext scaffold build: passed. This is retained tooling, not a hosted full-stack deployment.
- FastAPI in-process smoke check: compiled frontend and a champion portrait return HTTP 200; `.env` and Python source return HTTP 404.
- The supplied BP screenshot decodes successfully into the complete image and a top detail strip. No live model result was produced or claimed.
- Startup and GitHub publishing scripts pass shell syntax validation.

Not yet verified:

- Paid OpenAI vision calls on actual BP screenshots. No API credential was supplied.
- Riot calls against a real NA account. No API credential or Riot ID was supplied.
- Mac-specific startup and interactive browser behavior. No browser automation was performed.
- Predictive accuracy or win-rate improvement. The initial recommendation engine uses transparent heuristics and has no empirical calibration.

GitHub: the user created `clf899/lol-draft-coach` after the initial ZIP delivery. The verified source, documentation, and champion assets are being imported into its default `main` branch. The original ZIP remains the earlier standalone delivery. Live API and Mac verification status above is unchanged.
