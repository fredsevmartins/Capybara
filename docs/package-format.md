# Package format 0.1

`.orepro` is a ZIP filename convention. ZIP_STORED is used on export for predictable
bytes and to avoid rejecting legitimate highly compressible data on round trip.
ZIP_STORED and ZIP_DEFLATED regular files are accepted on import. Explicit ZIP
directory entries, encrypted files and special files are rejected in v0.1.

Required documents:

| Path | Meaning |
| --- | --- |
| `manifest.json` | OpenRepro schema `0.1`, experiment and payload inventory |
| `ro-crate-metadata.json` | RO-Crate 1.1 JSON-LD graph generated from manifest |
| `README.md` | Inventoried human summary |
| `provenance/provenance.json` | Inventoried creation-event record |

Manifest fields include UUID identifier, title, description, nonempty authors,
timezone-aware creation date, software version, license, optional domain, keywords,
DOI, institution, experimental date and reproduction instructions. Files specify
relative path, byte size, SHA-256, role, description and `derived_from` references.
References must identify other registered files. Unknown manifest fields and schema
versions are rejected. A relationship is required only when declared; the software
does not infer scientific dependencies.

Roles map to raw → `data/raw`, processed → `data/processed`, protocol → `protocol`,
script → `analysis/scripts`, figure → `results/figures`, table → `results/tables`,
supplementary → `supplementary`. Filenames must be NFC UTF-8, relative POSIX paths
without traversal, Windows reserved names, trailing dots/spaces or forbidden characters.
Case-insensitive collisions are rejected for portable extraction.

The manifest complements RO-Crate with checksums, roles and package-version rules.
The JSON-LD graph contains a metadata descriptor, root Dataset, author Person nodes
and File nodes linked by `hasPart` and `isBasedOn`. Integrity inventory excludes the
two metadata documents to avoid circular hashing. These documents are compared for
consistency, not cryptographically authenticated. Metadata and payload can be replaced
by an attacker who recomputes all hashes; signatures are not implemented.

Validation checks exact agreement with the generated RO-Crate profile offline. It
is not a general JSON-LD expansion, remote-context resolution or certification tool.
An external RO-Crate with extra graph entities may require explicit conversion.

Limits: 10,000 entries, 128 MiB per file, 512 MiB total expanded/archive bytes,
200:1 maximum decompression ratio, 4 MiB per JSON metadata document. UTF-8 filenames
are retained; archive timestamps normalize to 1980-01-01 and file mode to 0644.
Sorted entries make repeated exports of the same workspace identical.

[Package structure diagram](diagrams/package-structure.md)
