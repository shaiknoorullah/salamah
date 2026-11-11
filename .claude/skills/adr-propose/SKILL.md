---
name: adr-propose
description: Propose a decision record. Use when a design choice needs the owner to accept it.
---

# Propose a decision

1. Read `docs/templates/decision.md` and `docs/decisions/README.md`.
2. Pick the next number: the highest in the decisions index plus one.
3. Copy the template to `docs/decisions/<number>-<slug>.md`.
4. Set `status: proposed` in the front matter. Never write `accepted`.
5. Fill Context, Decision and Consequences. Keep Context to two sentences.
6. Add a row to the table in `docs/decisions/README.md`.
7. Add a link in `docs/README.md` under Decisions.
8. Run `just docs`.
9. Open a `decision` issue with the `needs-human` label and link the record.

The owner changes the status to `accepted`.
