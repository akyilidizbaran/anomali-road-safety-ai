# Camera Screen Requirements

## Required UI

* Live camera preview must be visible.
* Target vehicle bounding box must be overlaid.
* Track ID must be visible.
* Risk level must be visible.
* Current mode must be visible: normal / critical.
* QoD status must be visible.
* Scene/weather/light/visibility context must be visible.
* Road context and external user/pedestrian status must be visible.
* FPS and latency must be visible in debug/system mode.

## Acceptance Criteria

* Low-risk events remain in normal mode overlay.
* Risky target vehicle can visually switch to critical mode style.
* QoD candidate/request/active status can be represented without claiming always-on QoD.
