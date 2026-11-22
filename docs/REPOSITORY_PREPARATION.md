# Repository preparation

Prepared on 2026-11-22 for the MECHENG 754 Capstone GitHub repository.

## Changes

- Imported the supplied project, experimental data and recorded results.
- Grouped the five research documents under `docs/` and linked them from the main README.
- Replaced workstation-specific setup instructions with commands run from the repository root.
- Added Git ignore rules and byte-preserving Git attributes to protect source-data checksums across Windows and other platforms.
- Excluded the compiled Python cache; retained the original scripts, configurations, data, figures and historical audits without content changes.
- Regenerated the file manifest after organization. Historical audit file counts and document locations describe the original package.

## Checks and limits

- Checked every entry in the supplied SHA-256 manifest before organization. One existing mismatch was found in `results/baseline/traces/SPM_1C_25degC.csv`; the copied CSV is byte-identical to the user's source file. It has been retained without changing its contents. The original manifest is archived in [provenance/ORIGINAL_MANIFEST_SHA256.json](provenance/ORIGINAL_MANIFEST_SHA256.json).
- Checked all seven Python entry points for syntax without importing scientific dependencies.
- Parsed all JSON files and checked local Markdown links after organization.
- Compared every retained non-document study file against its original bytes.
- Verified the regenerated manifest covers all distributed files except the manifest itself and `.git/`.

No simulations were rerun during repository preparation. The current preparation environment does not have PyBaMM installed. Existing numerical results and their recorded limitations are preserved; the original test platform and pinned dependencies are documented in the README and guide.
