# DXF Diff Research

This directory tracks reverse-engineering experiments based on DXF before/after diffs.

Rules:

- one experiment per folder
- one AutoCAD change per experiment whenever possible
- keep the exact source artifact paths
- keep both observations and implementation guesses separate

Suggested experiment contents:

- `meta.yaml`: machine-readable metadata
- `procedure.md`: exact reproduction steps
- `findings.md`: observed structural changes and key excerpts
- `notes.md`: open questions, noise, next steps
- source artifact paths to `before.dxf`, `after.dxf`, and normalized files

Workflow:

1. Create or generate a minimal baseline DXF.
2. Make one controlled AutoCAD or AutoLISP change.
3. Save in the same DXF format.
4. Run normalized diff.
5. Record only confirmed observations in `findings.md`.
6. Map likely implementation targets in `ezdxf`.

Helper tools:

- `new-experiment.ps1`: scaffolds a numbered experiment folder and appends an entry to `index.md`
- `RE-0000-template/`: reference template for manual editing
