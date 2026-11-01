# Repository rename: Capybara

The canonical GitHub repository is now
[fredsevmartins/Capybara](https://github.com/fredsevmartins/Capybara).
It is the same project previously hosted as fredsevmartins/OpenRepro, with the
existing history, tags and releases preserved. The README uses Capybara as the
repository name, inspired by the capybara scientist mascot.

This is a repository rename, not a package-format or Python-interface migration:

- The distribution/module and CLI commands remain `openrepro` and `openrepro-mcp`.
- Existing `.orepro` packages and published artifact filenames are unchanged.
- Existing immutable tags and Zenodo files are preserved; the rename does not mint a DOI.
- Project/citation/download links use the new canonical repository URL.
- The release workflow derives its repository from `github.repository`, so it follows the new name.

For an existing checkout, update the remote without moving the working directory:

```bash
git remote set-url origin https://github.com/fredsevmartins/Capybara.git
git remote -v
```

GitHub redirects old repository links; new references should use Capybara. A local
checkout may still be named OpenRepro. Preserve that directory and its installed
virtualenv rather than moving it just to match the remote name.
