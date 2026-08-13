# Runtime Probe Test Report — v0.1C

## Scope

Offline construction and adversarial validation of the first WH3 campaign observation and save/reload probes.

## Tests

- deterministic PFH5 build across independent output directories;
- PFH5 parse round trip through the existing audit reader;
- Mod pack type, zero dependencies, zero compression, deterministic timestamp, and expected internal paths;
- observer Lua static rejection of campaign/save mutation calls and unsynchronized randomness;
- persistence Lua limited to exactly one `get_saved_value` and one `set_saved_value` call;
- valid observer log parsing and capability promotion;
- valid two-session persistence round-trip promotion;
- rejection of private/path fields;
- rejection of out-of-order events;
- rejection of duplicate pack paths and traversal paths.

## Result

10 runtime-probe tests passed twice in the construction environment. The pre-existing 18 SyntheticLab tests also passed after integration.

## Deterministic build outputs

- observer pack SHA-256: `33f3f9cf43441470348e28e4ea03e5091ac47dd8ae99e17ba2ab2662d9db7abd`
- persistence pack SHA-256: `16d1a54d920b9e5fba74aa8b6bf3a999c6402b597f6864acbd2f824301e0b97b`
- aggregate build result digest: `427d7780a81e4a5c9a5e879d53a8489f5044d1473b2fc6aeef6736a0b55dda47`
- valid observer fixture summary digest: `41a9c637fa7d2188630af79d50c714eec6c57dbb0ed6bffcd017b5e2eee889b7`
- persistence fixture summary digest: `ba0b6923c416439606056701d0e5f730c0400493c544e1c75ce1e25d5cb008f7`

## Limitations

- Lua syntax and API behavior are not proven until WH3 loads the pack.
- A valid PFH5 structure does not prove launcher recognition or runtime compatibility.
- Fixture capability promotions are parser tests, not owner-machine evidence.
- Ordinary battle control, campaign objective control, and outcome acknowledgement remain unverified.

## Repeated integrated validation

- validation run 1: 1.82 seconds, 110,964 KB maximum RSS;
- validation run 2: 1.60 seconds, 110,792 KB maximum RSS;
- deterministic build run 1: 0.51 seconds, 110,476 KB maximum RSS;
- deterministic build run 2: 0.50 seconds, 110,248 KB maximum RSS;
- the two build JSON outputs were byte-identical;
- all generated pack and build-manifest bytes were identical across the two builds.

The complete validator covered 74 hashed repository files, 18 SyntheticLab tests, and 10 runtime-probe tests in each run.
