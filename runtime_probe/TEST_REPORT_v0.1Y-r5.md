# Runtime Probe Test Report v0.1Y-r5

- 108 Runtime Probe tests passed.
- A live watcher regression starts the watcher in-process, verifies a schema-2 handshake-bound status, requests shutdown, and verifies a clean `STOPPED` state.
- Static workflow regression forbids launcher-PID equality as the readiness contract.
- Final checkpoint verification accepts only the expected schema-2 handshake token and rejects a foreign token.
- Watcher stdout and stderr are redirected to private session diagnostics.
- Nonzero early exits and captured diagnostics are surfaced to the owner.
- Incomplete preflight sessions request orphan-watcher shutdown; canonical sessions with a private manifest are excluded.
- Public export boundaries remain unchanged.
