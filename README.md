# Next Step

A student-support and study app: practical next steps, a study workspace, and a research library. The public app is hosted at https://dhairyaparyani2010-del.github.io/studyhelp/ .

## What is included

- Twelve support categories, 122 distinct situation cards, smaller fallbacks, and support-first routes.
- A short plan flow with available time, energy, topic, primary concern, adjustable steps, and an optional timer. Only a user's explicit action marks a step complete.
- Recall cards with editable review dates, eight worked examples with answer checks, an error log, a deadline planner, and an editable weighted-grade calculator.
- A lazy-loaded index of 1,000 unique PubMed records across 14 topics, with search, filters, pagination, direct source links, and CSV export.
- Twenty-five checked research/guidance summaries, including an original retrieval study, with claims and scope limits linked to response cards.
- Draft requests for learning help, more time, access support, practical resources, or a private conversation. Nothing is sent automatically.
- Responsive phone/tablet/desktop layouts, visible keyboard focus, a skip link, larger-text control, modal keyboard navigation, and reduced-motion styles.

## Run locally

Requires Node.js 24 (the deployment workflow uses Node 24).

```sh
npm ci
npm run dev
npm test
npm run build
```

The Vite base is /studyhelp/. Build output is dist/. The existing GitHub Pages workflow runs tests and builds before deployment. The conflicting legacy Jekyll workflow was removed so there is one deployment path.

## Data and privacy

Session choices and unfinished work stay in page memory until refresh or tab close. Optional device saving stores Study studio work in this browser's localStorage; it does not persist personal support selections, explanations, or support drafts. Privacy controls clear saved study work or reset the current session. Downloads and clipboard contents are controlled by the user and are not erased by resetting the app.

There are no accounts, analytics, ads, notifications, third-party fonts, or automatic messages. External research/support links have their own privacy policies.

## Research scope

The 1,000-paper count means bibliographic records retrieved, deduplicated, automatically screened, and spot-checked. It does not mean all papers were fully read or critically appraised, and it does not demonstrate app effectiveness. Publication types and citation counts are metadata, not evidence-quality ratings. Read [RESEARCH_METHODS.md](RESEARCH_METHODS.md) for inclusion criteria, queries, allocation, exclusions, sample checks, and limits.

The 25 checked source summaries support specific underlying principles. Exact response cards, examples, timings, and schedules are app-authored and untested as a combined intervention. The tool does not diagnose or provide treatment. Sensitive support routes require qualified professional review. The app is not monitored and cannot contact help on a user's behalf.

To reproduce the catalog, run python3 scripts/collect-research.py. The source database changes, so regenerated citation counts and selected records may differ.

## Verification

Automated tests cover situation coverage and distinctness, source mapping, support routing, plan selection, energy limits, weighted grades, review dates, catalog count/deduplication/provenance, and catalog-summary-methods consistency. Browser checks cover the plan journey, retained fields when switching tools, review-card creation, research search and pagination, examples, and layouts at desktop plus 390px/768px iframe viewports.

