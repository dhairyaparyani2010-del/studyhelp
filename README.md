# Next Step

A responsive student-support prototype for ages 13+, built from the supplied Student Support App Blueprint. Vite serves a dependency-light JavaScript application; no backend or credentials are required.

## Development

Use Node.js 22+ (validated with Node 24).

```sh
npm ci
npm run dev
```

Run `npm test` for planner rules and `npm run build` for a production build. `npm run preview` serves the built application.

## Included

- Twelve searchable, multi-select category branches, optional specifics, direct study access, and editable combined plans.
- Time and energy constraints, smaller alternatives, feedback adaptation, a pauseable timer, and human-support navigation.
- Retrieval workspace, self-checked corrections and review date, an algebra worked example with checked feedback, and error review.
- Editable help-request drafts with deliberate clipboard copying, source drawer, school/college support options, larger text, and responsive layouts.
- Guest use with in-memory state only. No analytics, local storage, automatic messages, notifications, or external AI calls.

Refreshing clears session inputs. Copying places text on the device clipboard; external links have their own privacy policies. Study workspace notes are temporary and are cleared when navigating away from that workspace.

## Boundaries before release

This is a functional prototype, not a clinically reviewed service. Sensitive routes provide general human-support navigation; no reviewed clinical intervention cards are claimed. Evidence metadata comes from the supplied blueprint and has not been independently reverified. Qualified educator and safeguarding review, local resource verification, student usability testing, and real browser/screen-reader accessibility evaluation are required before a public student release.

No live tutor, automated marking beyond the included algebra exercise, durable spaced-review reminders, school integrations, uploads, or backend report collection are implemented. Recall and error review are manual tools. The reporting panel explicitly explains that it cannot submit reports.

## GitHub preview

In the GitHub repository, open **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**. The included workflow deploys on pushes to `main`. If needed, open **Actions → Deploy app to GitHub Pages → Run workflow**. When deployment succeeds, the preview is at https://dhairyaparyani2010-del.github.io/studyhelp/ .

GitHub Pages availability depends on repository visibility and the account plan. This publishes a prototype with its review limitations visibly labeled.
