# Quick start

From the checkout, activate the installed environment and use fresh paths:

```bash
openrepro init experiments/study --title 'Model study' --description 'Synthetic training' --author 'A. Researcher' --reproduction 'Read protocol; run scripts manually in a trusted environment'
openrepro add experiments/study README.md --role protocol --description 'Demonstration input'
openrepro list experiments --json
openrepro inspect experiments/study --json
openrepro validate experiments/study
openrepro export experiments/study study.orepro
openrepro import study.orepro experiments/imported
openrepro validate experiments/imported --json
```

The source README remains unchanged. The copied file appears under `protocol/`.
An existing destination is an error. Never treat a successful validation report as
approval to execute an imported analysis script.
