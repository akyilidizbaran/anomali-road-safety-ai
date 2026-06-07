# Decision: Repository Private Visibility

## Date

2026-06-08

## Decision

GitHub repository visibility was changed from public to private.

## Rationale

The project may later include sensitive contracts, API integration details, model experiment notes, evidence metadata, and privacy-sensitive road safety material. Private visibility reduces unnecessary exposure while the project is still being developed.

## Impact

* Repository visibility is now `PRIVATE`.
* The existing security rule remains unchanged: credentials, API keys, raw videos, evidence images, model weights and private data must not be committed.
* Public-facing wording in core documentation was updated to repository/private wording.

## Alternatives

* Keep the repository public and rely only on `.gitignore` and process controls.
