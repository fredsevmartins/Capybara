# GitHub-first releases

The current distribution path is GitHub plus Zenodo. PyPI is optional and has been
deferred by the user; it is never triggered by a tag push.

A new `v*` tag triggers `release.yml`. It first calls the full reusable OS/Python
and Docker compatibility workflow. The verification job then checks the requested
version against package metadata, runs lint/docs and real Docker tests, builds the
wheel/source archive and verifies their contents with Twine and the inventory checker.
Only the verified artifacts are passed to the publication job. JUnit outcomes are
summarized without changing the underlying pytest result.

The GitHub publication job uses GitHub's own short-lived workflow token, scoped to
`contents: write`. It creates a Release for the existing tag and attaches the verified
wheel, source archive and verification record. PEP 440 candidate/dev versions are
marked as pre-releases and are not promoted to latest stable. Existing releases and
assets are preserved on reruns; the workflow does not overwrite published bytes.

This workflow avoids requiring an API token in the development chat. A successful
Git push still does not establish a successful workflow or Release: verify the run,
release page and attached artifacts. A failure in verification blocks publication.

`workflow_dispatch` supports an existing tag as well. Its PyPI input defaults to
false and can run only with explicitly enabled manual dispatch plus a configured
trusted publisher. No PyPI account is required for the GitHub release path.

Zenodo may ignore releases marked as pre-release. Preserve the existing manual
rc1 deposit and use Zenodo's new-version workflow if a later candidate needs its
own archived record. Do not change the archived ZIP or reuse its version DOI as a
claim that a new revision has already been deposited.


The rc2 release was exercised end-to-end: the compatibility workflow and verification
passed, GitHub created the Release and the public wheel/source downloads matched
the CI checksum record. Installing the actual downloaded wheel in a clean virtualenv
passed the package/catalog lifecycle. See [verification](verification.md) for run URLs.
In `verification.json`, `published: false` describes the checker itself performing
no upload; the separate successful GitHub job/public asset URLs establish publication.
