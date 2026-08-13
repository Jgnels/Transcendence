# WH3 Campaign Timer Semantics Audit v0.2I-r1

## Scope

Re-audit the timer choice used by the v0.2I campaign-feasibility request executor after the first owner-runtime limiting observation reached `FEASIBILITY_EXECUTOR_READY` and produced a valid request but emitted no query result or rejection while the owner remained idle on the campaign map.

## Primary source

- WH3 Campaign Manager documentation: https://chadvandy.github.io/tw_modding_resources/WH3/campaign/campaign_manager.html
- Inspected 2026-08-01.

## Relevant documented semantics

The campaign manager documents `callback` / `repeat_callback` as timers synchronized to the **campaign model**. It separately documents `real_callback` / `repeat_real_callback` as timers synchronized to **UI updates**, with real-timer intervals expressed in milliseconds.

The v0.2I owner workload intentionally requires no turn advance, army movement, save, or other campaign-model action: load the campaign and leave the map idle. Therefore a model-synchronized polling loop is a poor transport primitive for a request that is written asynchronously by an external sidecar after first-tick snapshot processing.

## Adjudication

- Owner observation: `LIMITING_RESULT`. The request existed and `FEASIBILITY_EXECUTOR_READY` was observed, but zero query results/rejections/packet-end events were emitted.
- Root cause: `SUPPORTED`, not directly observed. The old probe had no poll-heartbeat event, so the limiting run cannot prove the callback never fired.
- Corrective design: invoke one immediate read-only poll at executor start, then use `cm:repeat_real_callback(..., 250, ...)`; emit one `FEASIBILITY_POLL_TICK` and one `FEASIBILITY_REQUEST_SEEN` marker for future diagnostics; remove the real callback after packet completion or explicit rejection.

## Authority

Changing the timer source affects only lifecycle/transport scheduling. It does not add a campaign mutation, order adapter, save write, route solver, acknowledgement claim, execution claim, or causal-outcome claim. Authority remains `NO_ORDERS`; application remains `PROHIBITED`.
