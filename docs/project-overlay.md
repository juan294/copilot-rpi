# Project overlays

A project overlay holds one project's additions to one Copilot RPI workflow skill. The project keeps its own procedure in the overlay and does not edit the managed skill. An edited managed skill can conflict with a later update; an overlay cannot, because the lifecycle never owns it.

## Location and ownership

- One file per workflow skill: `.rpi/project/<skill>.md`, for example `.rpi/project/rpi-release.md`.
- The project owns the file. Track it in Git. Plan, apply, check, detach and rollback never read, write or delete anything under `.rpi/project/`. No package destination can name `.rpi/project`, `.rpi/copilot` or `.rpi/local/copilot`, or anything below them, in any letter case.
- From Copilot RPI 2.1.0, each of the 16 workflow skills has a `## Project overlay` section that tells the agent to open the file by its exact path and read it when it exists (a file search can skip the hidden `.rpi` directory): `rpi-assess`, `rpi-brainstorm`, `rpi-describe-pr`, `rpi-explore-release`, `rpi-fix-ci`, `rpi-implement`, `rpi-plan`, `rpi-pre-launch`, `rpi-release`, `rpi-remediate`, `rpi-research`, `rpi-status`, `rpi-tool-design`, `rpi-triage`, `rpi-update-docs` and `rpi-validate`.
- The four lifecycle skills (`rpi-adopt`, `rpi-bootstrap`, `rpi-detach`, `rpi-update`) have no overlay. Other skills, such as `rpi-debug` and `rpi-quality-review`, do not read one either.

## Profiles

The overlay path is a repository path, so one file serves every profile:

| Profile | Installed copy that reads the overlay |
| --- | --- |
| `cli` | `.github/skills/<skill>/SKILL.md`, a byte copy of the authored skill |
| `agent-host` | `.github/skills/<skill>/SKILL.md`, a byte copy of the authored skill |
| `vscode-local` | `.github/prompts/<skill>.prompt.md`, a wrapper that embeds the skill body |

The render receipt `.rpi/copilot-render.json` records `authored_sha256` on each skill `SKILL.md` record and each prompt wrapper record. The value is the SHA-256 of `templates/skills/<skill>/SKILL.md`, so it is the same in all three profiles. The lifecycle copies it into that entry of `.rpi/copilot/manifest.json`.

## File format

```text
<!-- rpi-overlay: skill=rpi-release; written-against=<12 hex characters> -->
# Project overlay for rpi-release

## Procedure
Project steps, checks and profile choices.

## Declared overrides
- Stock rule: "<exact quoted sentence from the stock skill>"
  Override: <what the project does instead>
  Reason: <why>
  Source: <commit or document that held the text>
  Owner decision: <YYYY-MM-DD, where recorded>
```

The first line is the header. `written-against` is the first 12 hex characters of the `authored_sha256` recorded for that skill. When the manifest records it, `diagnose` prints the full header as `header_line`. The value changes only when the stock skill changes, which is when the overlay needs a review.

Leave out `## Declared overrides` when there are none. Each entry starts with a `- Stock rule:` line that quotes the stock sentence, followed by indented `Override`, `Reason`, `Source` and `Owner decision` lines. `Owner decision` starts with the date of the decision. `diagnose` reports the number of entries as `overrides` and names the first malformed entry in `reason`.

## Diagnose

Run the read-only report from the rendered package or a blueprint checkout:

```bash
python3 "$package_dir/.rpi/copilot/runtime/rpi-distribution.py" diagnose \
  --target "$project_dir"
```

The command prints JSON and always exits 0; problems are data in the report. It never prints overlay text.

- `installation` has `status` (`present`, `missing` or `unreadable`), `manifest`, `profile`, `source_version`, `drift`, `reason` and `fix`. `drift` lists each owned destination whose bytes differ from the recorded baseline, with `state` `modified` or `missing`. For an unreadable manifest, `fix` names the `check` command to run.
- `project_overlays` has one item for each `.rpi/project/*.md`. Every item has the same fields: `file`, `skill`, `status`, `reason`, `fix`, `written_against`, `current`, `header_line` and `overrides`. `current` is the first 12 hex characters of the recorded `authored_sha256`. A field that does not apply is `null`; `overrides` is `null` when the file was not read.

## Statuses

The first status that applies is reported, in this order:

| Status | Meaning | Fix |
| --- | --- | --- |
| `invalid` | Not a regular file (symlinks and directories included), an uppercase file name, larger than 64 KiB, not UTF-8, not one of the 16 workflow skills (lifecycle skills included), or a first line that is not that skill's header. | Follow the printed `fix`: rename, shorten, re-save or remove the file, or write the printed header. |
| `inert` | The installed copy for the recorded profile is missing or has no `## Project overlay` section, so the agent ignores the overlay. | Update the installation with `rpi-update`, then run `diagnose` again. |
| `stale` | The stock skill changed since the overlay was reviewed. | Review the overlay against the installed skill, then replace its first line with `header_line`. |
| `present` | The header matches the installed skill, or no authored hash is recorded yet (see Limits). | None. |

A problem in `## Declared overrides` adds a `reason` and a `fix` without changing the status, so a `present` or `stale` item can carry both. Two problems are reported: a malformed entry (`declared override <n> lacks: ...`, naming the missing parts) and a section with no entries (`the ## Declared overrides section has no entries; remove it or add an entry`).

## Limits

- Files whose names start with a dot are skipped, and so are names that do not end in `.md`. A directory named like an overlay is `invalid`.
- Symlinks are not followed. The file is opened without following a final symlink and only regular files are read.
- File names must be lowercase. On a case-insensitive filesystem, rename with `git mv` in two steps if needed.
- At most 65,536 bytes are read. A UTF-8 byte order mark and CRLF line endings are accepted.
- Staleness is not checked for an installation that has not recorded authored hashes yet. An otherwise valid overlay then reads as `present` with `current` set to `null`, `fix` set to `null` and the reason "staleness is not checked until the next update records authored hashes". Updating from the same package does not record them, because that update is a no-op; the next update that changes installed files does. `check` stays healthy meanwhile. Until then the header accepts any 12 hex characters.
- Without a readable manifest, `diagnose` checks both the skill copy and the prompt wrapper, and does not check staleness; a `present` item carries the same reason.

## What an overlay can and cannot do

An overlay can add steps and checks and make the workflow stricter.

An overlay cannot grant push, tag, merge, deployment or publication authority. It cannot relax a gate. A gate is any rule that blocks or permits a release, publication, merge, deployment or phase acceptance. Gates include which findings block, the required checks and verification, and every safety or authorization rule, such as fixture, cleanup, real-user data and outward-action rules.

A declared override can change other procedure detail only. Each entry quotes the stock rule and names the reason, the source and the owner decision. The owner decision is a decision the owner made and recorded; the commit that first held the text is its source, not its approval.

A choice that the stock skill already leaves to the project, such as whether the release profile selects Wave B exploratory charters, belongs in `## Procedure`. It is not an override.

## Enforcement

This is an instruction contract. Nothing parses an overlay to stop forbidden text, and `diagnose` checks only the structure described above. Push protection stays with the optional receipt gate and destructive-command hook described in [native policy](native-policy.md). Review overlays like any other change to the project's release procedure.
