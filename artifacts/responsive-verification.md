# Responsive refinement — 14 October 2026

Tested in desktop Chrome with 320, 375, 430, 768, 1024 and 1440 pixel viewports. Tests use the seeded local database and do not edit records.

- 102 public/account/workspace route checks across six widths, with no page-wide horizontal overflow.
- Phone hero/search remain in normal flow with the complete search form contained in the hero.
- Public menu and workspace drawer support Escape, visible close/backdrop controls, restored focus, scroll locking and inert background content for the drawer.
- Mobile record tables become labeled cards. Wide reports retain a dedicated horizontal scroll area and hint.
- CRM pipeline scrolls horizontally with snap alignment, readable card text and 48px stage controls.
- Touch controls and form text were enlarged; input text is 16px on phones to avoid automatic focus zoom on common mobile browsers.
- Six-width tests include directory/details, public profiles, login/registration, both dashboards, properties, tenants, leads, leases, inspection/property forms, pipeline, reports and performance.
- No JavaScript page errors observed. JavaScript syntax check and Django system/migration checks pass.
- 29 Django workflow, permission and sample-import tests pass.

Screenshots: `mobile-public-refined.png`, `mobile-management-refined.png`, `mobile-records-refined.png`, `mobile-pipeline-refined.png`, `desktop-management-refined.png`.

These are browser viewport tests, not physical iOS/Android hardware tests. Browser results: `responsive-results.json`. Test script: `tests/responsive_smoke.py`.

Production asset URLs include the release identifier, so the new CSS and JavaScript do not reuse previous cached URLs. No data schema, authentication roles, account passwords or agency records are changed by this UI release.
