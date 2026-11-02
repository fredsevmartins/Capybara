# Complete CLI options

Generated from the installed 1.0.0 parser; help wrapping can vary by Python version.
Do not edit help blocks by hand.
Regenerate with `python scripts/documentation_reference.py --write`.
See [CLI behavior and exit codes](cli-reference.md) for interpretation.

## Top-level help

```text
usage: openrepro [-h]
                 {init,add,list,inspect,validate,export,import,version,update,remove,replace,plan,reproduce,compare,environment-lock,environment-build,recipe,doctor,report,recover,publish,search,fetch,cite,serve,deposit-bundle,zenodo-deposit,convert-crate,schema}
                 ...

Share experiments. Reproduce science.

positional arguments:
  {init,add,list,inspect,validate,export,import,version,update,remove,replace,plan,reproduce,compare,environment-lock,environment-build,recipe,doctor,report,recover,publish,search,fetch,cite,serve,deposit-bundle,zenodo-deposit,convert-crate,schema}
    init                Init an experiment or package
    add                 Add an experiment or package
    list                List an experiment or package
    inspect             Inspect an experiment or package
    validate            Validate an experiment or package
    export              Export an experiment or package
    import              Import an experiment or package
    version             Version an experiment or package
    update              Update an experiment or package
    remove              Remove an experiment or package
    replace             Replace an experiment or package
    plan                Plan an experiment or package
    reproduce           Reproduce an experiment or package
    compare             Compare an experiment or package
    environment-lock    Environment-lock an experiment or package
    environment-build   Environment-build an experiment or package
    recipe              Recipe an experiment or package
    doctor              Doctor an experiment or package
    report              Report an experiment or package
    recover             Recover an experiment or package
    publish             Publish an experiment or package
    search              Search an experiment or package
    fetch               Fetch an experiment or package
    cite                Cite an experiment or package
    serve               Serve an experiment or package
    deposit-bundle      Deposit-bundle an experiment or package
    zenodo-deposit      Zenodo-deposit an experiment or package
    convert-crate       Convert-crate an experiment or package
    schema              Schema an experiment or package

options:
  -h, --help            show this help message and exit
```

## init

```text
usage: openrepro init [-h] [--json] --title TITLE --description DESCRIPTION
                      --author AUTHOR [--license LICENSE]
                      [--reproduction REPRODUCTION]
                      path

positional arguments:
  path

options:
  -h, --help            show this help message and exit
  --json                Print structured JSON
  --title TITLE
  --description DESCRIPTION
  --author AUTHOR
  --license LICENSE
  --reproduction REPRODUCTION
```

## add

```text
usage: openrepro add [-h] [--json] --role
                     {raw,processed,protocol,script,figure,table,supplementary}
                     [--description DESCRIPTION] [--derived-from DERIVED_FROM]
                     path source

positional arguments:
  path
  source

options:
  -h, --help            show this help message and exit
  --json                Print structured JSON
  --role {raw,processed,protocol,script,figure,table,supplementary}
  --description DESCRIPTION
  --derived-from DERIVED_FROM
```

## list

```text
usage: openrepro list [-h] [--json] path

positional arguments:
  path        Directory containing experiment workspaces

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
```

## inspect

```text
usage: openrepro inspect [-h] [--json] path

positional arguments:
  path

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
```

## validate

```text
usage: openrepro validate [-h] [--json] path

positional arguments:
  path

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
```

## export

```text
usage: openrepro export [-h] [--json] path output

positional arguments:
  path
  output

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
```

## import

```text
usage: openrepro import [-h] [--json] package destination

positional arguments:
  package
  destination

options:
  -h, --help   show this help message and exit
  --json       Print structured JSON
```

## version

```text
usage: openrepro version [-h] [--json]

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
```

## update

```text
usage: openrepro update [-h] [--json] --metadata METADATA path

positional arguments:
  path

options:
  -h, --help           show this help message and exit
  --json               Print structured JSON
  --metadata METADATA  JSON object of metadata changes
```

## remove

```text
usage: openrepro remove [-h] [--json] path file

positional arguments:
  path
  file        Registered relative file path

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
```

## replace

```text
usage: openrepro replace [-h] [--json] path file source

positional arguments:
  path
  file        Registered relative file path
  source

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
```

## plan

```text
usage: openrepro plan [-h] [--json] --spec SPEC path

positional arguments:
  path

options:
  -h, --help   show this help message and exit
  --json       Print structured JSON
  --spec SPEC  Reviewed reproduction recipe JSON
```

## reproduce

```text
usage: openrepro reproduce [-h] [--json] --spec SPEC [--environment ENVIRONMENT]
                           [--allow-build] --output OUTPUT [--allow-execution]
                           path

positional arguments:
  path

options:
  -h, --help            show this help message and exit
  --json                Print structured JSON
  --spec SPEC           Reviewed reproduction recipe JSON
  --environment ENVIRONMENT
                        Build from a registered environment lock
  --allow-build
  --output OUTPUT       New external run directory
  --allow-execution     Explicitly execute reviewed code
```

## compare

```text
usage: openrepro compare [-h] [--json] --spec SPEC --outputs OUTPUTS path

positional arguments:
  path

options:
  -h, --help         show this help message and exit
  --json             Print structured JSON
  --spec SPEC        Reviewed reproduction recipe JSON
  --outputs OUTPUTS  Directory of regenerated outputs
```

## environment-lock

```text
usage: openrepro environment-lock [-h] [--json] --requirements REQUIREMENTS
                                  --base-image BASE_IMAGE --output OUTPUT
                                  [--allow-download]
                                  path

positional arguments:
  path

options:
  -h, --help            show this help message and exit
  --json                Print structured JSON
  --requirements REQUIREMENTS
                        Registered requirements input
  --base-image BASE_IMAGE
                        Reviewed immutable base image ID
  --output OUTPUT
  --allow-download
```

## environment-build

```text
usage: openrepro environment-build [-h] [--json] --spec SPEC [--allow-build]
                                   path

positional arguments:
  path

options:
  -h, --help     show this help message and exit
  --json         Print structured JSON
  --spec SPEC
  --allow-build
```

## recipe

```text
usage: openrepro recipe [-h] [--json] --image IMAGE --output OUTPUT
                        [--script SCRIPT] [--interpreter INTERPRETER]
                        [--reference REFERENCE] [--result-name RESULT_NAME]
                        path

positional arguments:
  path

options:
  -h, --help            show this help message and exit
  --json                Print structured JSON
  --image IMAGE
  --output OUTPUT
  --script SCRIPT
  --interpreter INTERPRETER
  --reference REFERENCE
  --result-name RESULT_NAME
```

## doctor

```text
usage: openrepro doctor [-h] [--json] [--docker] path

positional arguments:
  path

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
  --docker
```

## report

```text
usage: openrepro report [-h] [--json] --output OUTPUT path

positional arguments:
  path

options:
  -h, --help       show this help message and exit
  --json           Print structured JSON
  --output OUTPUT
```

## recover

```text
usage: openrepro recover [-h] [--json] path

positional arguments:
  path

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
```

## publish

```text
usage: openrepro publish [-h] [--json] --catalog CATALOG path

positional arguments:
  path

options:
  -h, --help         show this help message and exit
  --json             Print structured JSON
  --catalog CATALOG
```

## search

```text
usage: openrepro search [-h] [--json] [--query QUERY] [--limit LIMIT]
                        [--experiment EXPERIMENT]
                        path

positional arguments:
  path

options:
  -h, --help            show this help message and exit
  --json                Print structured JSON
  --query QUERY
  --limit LIMIT
  --experiment EXPERIMENT
```

## fetch

```text
usage: openrepro fetch [-h] [--json] path checksum destination

positional arguments:
  path
  checksum
  destination

options:
  -h, --help   show this help message and exit
  --json       Print structured JSON
```

## cite

```text
usage: openrepro cite [-h] [--json] path checksum

positional arguments:
  path
  checksum

options:
  -h, --help  show this help message and exit
  --json      Print structured JSON
```

## serve

```text
usage: openrepro serve [-h] [--json] [--host HOST] [--port PORT] path

positional arguments:
  path

options:
  -h, --help   show this help message and exit
  --json       Print structured JSON
  --host HOST
  --port PORT
```

## deposit-bundle

```text
usage: openrepro deposit-bundle [-h] [--json] --output OUTPUT path

positional arguments:
  path

options:
  -h, --help       show this help message and exit
  --json           Print structured JSON
  --output OUTPUT
```

## zenodo-deposit

```text
usage: openrepro zenodo-deposit [-h] [--json] [--publish]
                                [--deposition-id DEPOSITION_ID]
                                path

positional arguments:
  path

options:
  -h, --help            show this help message and exit
  --json                Print structured JSON
  --publish             Publicly publish the reviewed deposit
  --deposition-id DEPOSITION_ID
```

## convert-crate

```text
usage: openrepro convert-crate [-h] [--json] --output OUTPUT [--license LICENSE]
                               [--author AUTHOR]
                               path

positional arguments:
  path

options:
  -h, --help         show this help message and exit
  --json             Print structured JSON
  --output OUTPUT
  --license LICENSE
  --author AUTHOR
```

## schema

```text
usage: openrepro schema [-h] [--json] --kind {manifest,recipe,environment}
                        --output OUTPUT

options:
  -h, --help            show this help message and exit
  --json                Print structured JSON
  --kind {manifest,recipe,environment}
  --output OUTPUT
```
