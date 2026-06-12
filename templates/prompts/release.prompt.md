---
mode: agent
description: "Prepare and publish a new version release, adapted to the project type"
---
Model tier: **sonnet** — invoke this prompt in a Sonnet session.

# Release New Version

Prepare and publish a new version release, adapted to the project type.

## Step 1: Orientation

Gather release context before making any changes.

1. **Detect project type** from manifest files:

   | Check | Type | Version source | Publish action |
   |-------|------|---------------|----------------|
   | `package.json` | Node/npm | `version` field | Advisory: "Ready for `npm publish`" |
   | `Cargo.toml` | Rust | `version` field | Advisory: "Ready for `cargo publish`" |
   | `pyproject.toml` | Python | `version` field | Advisory: "Ready for `twine upload`" |
   | `go.mod` | Go | Git tags only | Advisory: "Tag pushed, `go get` ready" |
   | None of above | Docs/generic | CHANGELOG.md or git tags | No publish step |

2. **Find current version** from the manifest file or latest git tag.

3. **Find last release tag** and compute changes since then:
   `git log <last-tag>..HEAD --oneline`

4. **Identify all version-bearing files** -- scan for the current version
   string across the project: manifests, README badges, install instructions,
   constants files, docker tags, CI configs, doc site configs.

5. **Detect branching strategy:**
   - Check if current branch is main/master
   - Check git log for merge commits from feature/release branches
   - If on main AND no merge-branch pattern: **main-only**
   - Otherwise: **feature-branch**

6. **Present findings** to the user:
   - Project type and version source
   - Current version
   - Commits since last release, categorized by type
   - All version-bearing files found
   - Detected branching strategy
   - Suggest major/minor/patch bump based on commit types

7. **Consider related commands:**
   - If there are unreleased changes, remind the user to consider
     running `/update-docs` first to refresh all documentation.
   - If this is the first release, recommend running `/pre-launch`.
   - Run `/status` for a quick orientation if the project state is unclear.

**STOP.** Ask the user for the version number before proceeding.

## Step 2: Preparation

After the user provides a version number, prepare all files. Do not publish.

1. **Bump version in manifest files** (package.json, Cargo.toml, etc.).
   If a lock file tracks the version (package-lock.json), update it too.

2. **Generate CHANGELOG entry** from commits since last tag. Categorize
   by conventional commit prefix into Keep a Changelog format:

   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD

   ### Added
   - feat: commits summarized here

   ### Fixed
   - fix: commits summarized here

   ### Changed
   - refactor/chore commits summarized here
   ```

   Present the draft to the user for review. Apply edits before writing.

3. **Update version references** in all files identified in Step 1:
   README badges, install instructions, constants, docker tags, etc.

4. **Run verification commands** via terminal (chain sequentially):
   typecheck, lint, test, build.
   If any fail, fix before proceeding.

5. **Present the full diff** to the user.

**STOP.** Wait for the user to review and approve before publishing.

## Step 3: Publish

After human approval, execute the release. The flow depends on the
branching strategy detected in Step 1.

### Main-only flow

Confirm with the user before creating the tag and GitHub release.
Present what will be tagged and published, then proceed after approval.

1. Create the release commit:
   `git commit -m "release: vX.Y.Z -- [summary from CHANGELOG]"`

2. Create an annotated git tag:
   `git tag -a vX.Y.Z -m "vX.Y.Z"`

3. Push the commit, then the tag by name:
   `git push origin main && git push origin vX.Y.Z`

4. Create the GitHub release:
   `gh release create vX.Y.Z --notes "[CHANGELOG entry]"`

5. Verify CI:
   `gh run list --branch main --limit 1`

6. Report the result with a link to the GitHub release.
   If the project has a registry publish step, remind the user:
   "Release is published. When ready, run `npm publish` / etc."

### Feature-branch flow

1. Create a release branch and commit:
   `git checkout -b release/vX.Y.Z`

2. Push the branch:
   `git push -u origin release/vX.Y.Z`

3. Check for an existing PR before creating one:
   `gh pr list --head release/vX.Y.Z`
   If no existing PR, create one (Error #29).

4. Verify CI on the PR.

5. **STOP.** Tell the user to review and merge the PR. After merge,
   provide the commands to tag and release:

   ```bash
   git checkout main && git pull
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   gh release create vX.Y.Z --notes "[CHANGELOG entry]"
   ```

6. Report the result with a link to the PR.

## Rules

- NEVER use `git push --tags` -- push tags by name (Error #20).
- NEVER use `--body` with `gh release create` -- use `--notes`.
- ALWAYS check for an existing PR before creating one (Error #29).
- ALWAYS verify CI after push.
- ALWAYS present the diff before committing (Step 2 gate).
- ALWAYS ask for the version number -- never guess or auto-increment.
- Registry publish (npm/cargo/twine) is ADVISORY ONLY -- tell the user
  it is ready, do not run it. Most registries require 2FA and publishing
  cannot be undone.
- Run verification commands sequentially, not in parallel.
