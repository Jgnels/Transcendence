# v0.2Q cutover transport

This directory exists only on `agent/v0.2q-cutover-loader` as a transport boundary for the sealed v0.2Q archive.

Upload exactly one `.zip` file here. The workflow will refuse to act unless its SHA-256 is exactly:

`653d2d4cd231f91d3acae91d3ae117907cde9bc3a93ddf3642565304cb557f6c`

If the hash matches, the workflow validates all 588 manifest entries, verifies the frozen Lua probe identities, runs the canonical repository validator, constructs an exact replacement Git tree, and fast-forwards `agent/v0.2q-canonical-cutover` from the preserved stale parent.

This loader branch and this directory are not canonical and must never be merged into `main`.
