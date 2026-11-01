# Research exchange and discovery

A catalog is a local directory containing a SQLite index and immutable `.orepro`
blobs. No database server is needed. Publishing here copies a validated package;
it does not publish to the Internet or mint a DOI.

```bash
openrepro publish study.orepro --catalog exchange --json
openrepro search exchange --query biology --limit 20 --json
openrepro search exchange --experiment EXPERIMENT_UUID --json
openrepro fetch exchange PACKAGE_SHA256 experiments/received --json
openrepro cite exchange PACKAGE_SHA256 --json
```

Each package has a content identity `urn:sha256:HASH`. Re-publishing identical bytes
returns the same record; different bytes for the same experiment UUID receive the
next catalog revision. Previous revisions remain available. Hashes are checked before
fetching/downloading, and import validates archive structure and payload inventory.
Search uses bound SQL parameters and escapes wildcard characters. Limits are bounded.
`cite` returns CSL JSON with literal author names, revision and package hash; it includes
a DOI only when the experiment explicitly declares one. It never invents a DOI.

## Read-only HTTP access

```bash
openrepro serve exchange --host 127.0.0.1 --port 8080
```

The service provides a human-readable search page, `GET /search?q=...` JSON results
and `GET /packages/HASH.orepro` verified downloads with an ETag. Other routes and
write methods are unsupported. It does not expose arbitrary filesystem paths,
uploads, shell execution or a Docker socket. Catalog metadata is HTML-escaped.

Local binding is the default. Public access requires an administrator-controlled
host and TLS reverse proxy; binding alone is not public deployment. Use a dedicated
service account, read-only catalog filesystem permissions for the serving process,
request/rate limits, backups and the reverse proxy's authentication when records are
private. The built-in server is intended for modest research exchanges; Internet-scale
operations need an appropriate production service layer. Run publication separately
with write access. Do not expose private datasets through an anonymous catalog.

For public preservation, citation and DOI registration use the [Zenodo workflow](zenodo.md).
Zenodo then supplies the public record and discovery page; running this optional
catalog service is not a prerequisite for Zenodo deposition.
