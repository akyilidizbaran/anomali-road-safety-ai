# Evidence Screen Requirements

## Required UI

* Shows recent evidence cards.
* Each card shows event ID, timestamp, risk type and risk level.
* Each card shows confidence score and QoD status.
* Each card exposes detail and evidence actions.
* Evidence detail loads by `event_id`.

## Acceptance Criteria

* Evidence card can be created from `architecture/contracts/event.schema.json`.
* Missing image/crop URI does not break the card.
* Decision reason is visible in detail view.
