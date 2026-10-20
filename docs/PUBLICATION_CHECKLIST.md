# Publication safeguards

The initial public launch is authorized under the Mini PC AI Lab identity, with sanitized references to AI Retro Game Studio, SladePuzzleCo and MischiefToons. Future releases must preserve these safeguards.

- Select only files listed in `publication-files.json`; inspect changes to that list explicitly.
- Keep private evidence, internal audit/handoff reports, campaign history, contact lists, trackers, correspondence, drafts, agreements, archives and unresolved ownership material out of Git.
- Scan all selected files and every reachable commit/object before pushing. Ignore rules alone do not remove tracked history.
- Publish only supported sanitized claims, original fixtures and owner-authorized material. Keep unavailable results labeled **Pending — not yet measured**.
- Apply MIT to original code and CC BY 4.0 to original documentation/report material according to [licensing boundaries](../LICENSING.md). Do not relicense third-party assets or names.
- Run `python -m unittest discover -s tests -v` and `python scripts/check_repository.py`; validate fixture results and relative links.
- Use a project commit identity and the account's GitHub noreply address. Do not include personal email, address or phone details.
- Verify the public repository, README, internal links, licenses, file inventory and published commit after pushing.

Publishing does not authorize emails, hardware agreements, purchases, model downloads, extended benchmarks or changes to existing projects. No private source files, screenshots or source-project binaries belong in this repository.
