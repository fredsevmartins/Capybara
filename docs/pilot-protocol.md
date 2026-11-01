# Independent acceptance protocol

No external participants or approvals are claimed here. This is a runnable protocol
for the remaining scientific and usability acceptance gate.

Ask a researcher who did not implement OpenRepro to install the candidate on another
machine, obtain a package through its versioned catalog/DOI, inspect the protocol,
license, provenance and dependencies, and reproduce the declared outputs using only
the published documentation. Use a real dataset/method the researcher is qualified
to assess, not only the supplied demonstrations.

Record software/package version and identifiers, operating system/architecture,
image identity, exact commands, expected units/tolerances, elapsed work, errors,
manual interventions and the resulting report. Independently check numerical
references and scientific assumptions. Record whether the researcher understood
that PASS is result agreement, not proof of correctness or authorship.

Acceptance requires a successful fresh-machine workflow, correct interpretation,
no unexplained data changes, and documented resolution of blocking usability or
scientific-method issues. A failed case is evidence to investigate, not permission
to weaken comparisons or omit outputs. Deployment security review should cover
image/dependency trust, shared-kernel isolation, quotas/recovery, catalog access,
publication rights and credential handling for the intended threat model.

The verification record should contain actual reviewer identity/consent where
appropriate, date, artifact IDs, observed outcomes and unresolved findings. Do not
replace these observations with generated testimonials, invented studies or a
local automated-test count. The final release decision is recorded against the
[launch checklist](launch-checklist.md).
