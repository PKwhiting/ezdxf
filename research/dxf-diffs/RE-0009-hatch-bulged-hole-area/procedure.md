# Procedure

1. Generate the baseline drawing:
   - `experiments/field-hatch-bulged-hole/generated/after.dxf`
2. Open the baseline in AutoCAD 2026.
3. Create a solid `HATCH` between the outer rectangle and the inner bulged loop.
4. Save as AutoCAD 2018 ASCII DXF:
   - `experiments/field-hatch-bulged-hole/manual/after-ui-hatch.dxf`
5. Generate a probe drawing that attaches an `AcObjProp Area` field to that saved hatch:
   - `experiments/ezdxf-generated-fields/probe-ui-authored-hatch-area.dxf`
6. Run `scripts/run-dxf-diff.ps1` with `testdata/noop.lsp` to capture the first Core Console save.

Files used in the final comparison:

- Baseline: `experiments/field-hatch-bulged-hole/generated/after.dxf`
- Edited: `experiments/field-hatch-bulged-hole/manual/after-ui-hatch.dxf`
- Probe: `experiments/ezdxf-generated-fields/probe-ui-authored-hatch-area.dxf`
- First Core Console save: `experiments/ezdxf-generated-fields/validate-probe-ui-authored-hatch-area/before.dxf`
