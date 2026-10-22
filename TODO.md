# TODO

> Move all of the optyx work into discopy-next, keep the license, make sure you keep the attribution of commits, copy all the open issues and pull requests adding giodefelice-agents as assignee. I had planned for him to do it (prompt attached) but I got some spare tokens so I'll do it myself instead.

toumix, 2026-10-22, interactive. The attached prompt, verbatim:

> Move optyx into rel-int/discopy-next as the module `discopy.optyx`, and move my open optyx work along with it, the way the open discopy agent PRs were moved in [rel-int/discopy-next#2](https://github.com/rel-int/discopy-next/issues/2).
>
> Context: rel-int/optyx is our fork of Quantinuum's optyx. The IP is ours, but the GitHub repo can't be transferred, so the code moves into discopy-next instead. Read discopy-next's `AGENTS.md` (the `Next` section above all), `RULES.md` and `STYLE.md` first, then #2 to see how the discopy move went. On discopy-next the agents merge into `main` themselves once checks pass. Upstream discopy stays human-reviewed, and nothing here opens an upstream PR.
>
> 1. Triage first, in one issue on discopy-next
>
> Open an issue titled "Triage: moving optyx into discopy.optyx". Quote this prompt verbatim at the top. Then give one row for each open rel-int/optyx PR (#16, #29, #44, #49, #52, #53, #56, #67, #76, #82, #84, #87, #88, #89), each with what it is, `+lines` measured from its merge base, what it is stacked on, and a proposed fate:
>
> - next: merged or ported into `discopy.optyx` on next `main`
> - own repo: a big, speculative experiment (e.g. `experiments/brec_exact`, sudoku) moves to a repository of its own, or becomes a notebook if it is small
> - close: superseded, or already covered by discopy itself (e.g. #44 "evaluate through discopy's contraction engines" may be moot once optyx lives inside discopy)
>
> List the open optyx issues too, each marked re-file or drop. Then stop and wait for me to rule on the issue before you move anything but `main`.
>
> 2. Bring optyx `main` in with its history
>
> - Rewrite optyx `main` (`c8b7117`) into a subdirectory with `git filter-repo --to-subdirectory-filter`, then merge it into a branch off next `main` with `--allow-unrelated-histories`. Every commit keeps its author: Mateusz Kupper, Boldizsár Poór, armandld and the others, not only us. No squash.
> - Layout: library in `discopy/optyx/`, tests in `test/optyx/`, notebooks in `docs/notebooks/optyx/`, examples as notebooks next to them. Leave behind the repo-level files that discopy-next already has (`AGENTS.md`, `RULES.md`, `STYLE.md`, `CONTRIBUTING.md`, `pyproject.toml`, `docs/conf.py`) and stray images like `ghz_circuit_qiskit.png`.
> - License: optyx stays Apache-2.0 while discopy is BSD-3. Keep optyx's `LICENSE` as `discopy/optyx/LICENSE`, carry over any `NOTICE` file, keep every copyright and attribution line in the files, and say in `discopy/optyx/__init__.py`'s docstring and in the CHANGELOG entry that the module is under Apache-2.0. Do not relicense anything.
> - Imports go from `optyx.` to `discopy.optyx.`. Third-party dependencies (perceval, graphix, the pytket packages, qiskit) go in a new `optyx` extra and dependency group, never in core. `import discopy` and `import discopy.optyx` must not import any of them at module level, and a test should check that, the way `test/neural/network.py` does for `discopy.neural`. Tests that need an extra are skipped by `--skip-extra`.
> - optyx pins discopy at `88895277`, so the real porting work is the API drift since then: `ob`/`ar` → `ob_map`/`ar_map`, `PRO` → `Nat`, `Ob` → `Wire`, `Swap` as a `Permutation`, `Matrix.ob` as `Nat`, the `feedback`/`traced` merge, `markov`/`comarkov` split, `List[type]` for `python.Function`. Port onto next `main` as it stands. Don't add compatibility shims to discopy.
> - Don't deduplicate during the move. `optyx.core.zx` against `discopy.quantum.zx`, optyx channels against `discopy.quantum.channel`, the backends against `tensor`: file one issue per overlap with what each side has, and leave it there. The move itself does not change behaviour.
> - Checks: `pflake8`, `pylint` (at or above `fail-under`, read with `--output-format=json2`), the full test suite with the `optyx` extra, and a `CHANGELOG.md` entry under `Added`. CI on the PR is the authority.
> - It is ~12k lines, over the thousand-line guideline. That is fine for next `main`, but split it into reviewable PRs in dependency order (e.g. `core` → `channel`/`classical`/`qubits`/`photonic` → `compiler` → notebooks). Each PR gets a `TODO.md` per `RULES.md` and carries the history merge from the first one.
>
> 3. Then the triaged PRs
>
> For each next row: merge it as it stands if it rebases cleanly onto the subdirectory (a merge commit of its head, rewritten with the same filter, so its commits survive), otherwise port it in a PR of its own carrying its optyx description. After it merges, close the optyx PR with a comment pointing to the discopy-next PR. Do own repo and close rows only after I've agreed on the issue, each with a comment saying where it went or why it closed. Re-file each kept optyx issue on discopy-next with its body headed `Ported from rel-int/optyx#N (<author>, <date>)`, and close the original with `Moved to rel-int/discopy-next#M`.
>
> 4. Last
>
> Once everything is moved, propose (don't do) a README on rel-int/optyx pointing to `discopy.optyx`, and archiving the repo.
>
> Only move my own work. Other people's optyx branches and PRs are theirs to bring. Keep the triage issue's checkboxes current as you go, as #2 does.

Ruled in the same session: experiments copied as draft PRs, each optyx original closed with a
pointer, the move as one PR with one commit per layer, the library PRs ported and merged. Triage
and the copied PRs and issues: #225.

- [x] merge optyx `main` `c8b7117`, rewritten into `discopy/optyx/`, `test/optyx/`,
  `docs/notebooks/optyx/`, `docs/_static/optyx/`, with its 198 commits and their authors
- [x] merge the 160 pre-squash commits of optyx#12, #15 and #57 (`backup/main-before-squash`,
  same tree as `1e3eab9`), so the copied PRs merge from their true merge base
- [x] license: `LICENSE` and a `NOTICE` carrying `docs/conf.py`'s copyright line in
  `discopy/optyx/`, Apache-2.0 said in the module docstring and the CHANGELOG
- [x] an `optyx` extra and dependency group, nothing of it in core
- [x] optyx's pins onto next `main`: numpy 2, Python 3.12–3.14, discopy's `pyzx` pin
- [x] imports from `optyx.` to `discopy.optyx.`
- [x] the API drift since discopy `88895277`, in dependency order: `core`, then `channel`,
  `classical`, `qubits`, `photonic`, then `compiler` and `utils`
- [x] `import discopy` and `import discopy.optyx` import no extra, and a test says so
- [x] `--skip-extra` skips what needs the extra
- [x] docs: the API page, the docstring images under `docs/_static/optyx/`
- [x] one issue per overlap: `core.zx` #270, channels #271, backends #272
- [ ] pflake8, pylint at or above `fail-under`, the full suite with the extra, CHANGELOG under `Added`
