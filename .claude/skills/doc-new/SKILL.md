---
name: doc-new
description: Add a new doc to docs/. Use when a feature, recipe or fact needs a page.
---

# New doc

1. Pick the Diataxis folder: `guides` (do), `reference` (look up), `explanation` (why), `tutorials` (learn).
2. Copy `docs/templates/doc.md` to `docs/<folder>/<name>.md`.
3. Fill the front matter: `type`, `status`, `covers` and today's `reviewed` date.
4. Write short sentences, 25 words or fewer. Name only paths and recipes that exist.
5. Link the doc from its folder README.
6. Link the doc from `docs/README.md`.
7. Run `just docs` and fix every failure.

Keep guides and explanations under 150 lines. Create `tutorials/` only with its first tutorial.
