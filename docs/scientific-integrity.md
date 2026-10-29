# Scientific integrity

Data preservation means retaining the input bytes: registration copies files, never
silently overwrites an existing registered name, and retains source files.
Package integrity means the inventory and SHA-256 values agree with the packaged
bytes. Metadata validation checks required fields and agreement with the supported
RO-Crate profile. Neither establishes authenticity or correctness.

Scientific reproducibility means an independent analysis can reproduce stated
results under specified assumptions. Scientific correctness requires appropriate
models, measurements, units and inference. OpenRepro 0.1 does not assess either.
Reports always include `scientific_validity: NOT_EVALUATED`.

Synthetic examples are demonstrations, not laboratory observations, clinical evidence
or validated scientific methods. Imported analysis files are inert. Review provenance,
licenses and methods before reuse. The provenance record is descriptive and unsigned;
it is not an immutable audit log.
