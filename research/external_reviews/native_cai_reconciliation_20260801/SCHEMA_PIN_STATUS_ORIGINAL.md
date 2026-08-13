# RPFM WH3 Schema Pin — Acquisition Status

Repository: `Frodo45127/rpfm-schemas`
Default branch: `master`
Current `schema_wh3.ron` Git blob observed through GitHub connector: `232216808ff5d38edd9e056c7828afdc1700d297`.

RPFM repository's currently visible schema submodule pointer: `229a393f8973b182458bedec8146cab4ef6d97fb`.
At that ref, `schema_wh3.ron` blob: `e3440ccf3d7d03e8864492aaad49ce49ad2df8c7`.

A GitHub compare from `229a393` to schema-repo `master` reports:
- status: master ahead by 1 commit;
- only changed file: `schema_wh3.ron`;
- +863 / -2 lines.

Interpretation: the current schema-repo master contains a newer WH3 schema artifact than the schema ref presently surfaced by the RPFM repository submodule. The exact semantic meaning of that one-commit delta is **UNVERIFIED** until its commit metadata/content is acquired; do not label it an 8.1-specific update merely from timing.

Limitation: the 10.3 MB RON file could not be retrieved into the current analysis container through the available GitHub/web bridge because of large-file transport limits. The blob SHA is therefore pinned, but row-semantic decoding remains open.
