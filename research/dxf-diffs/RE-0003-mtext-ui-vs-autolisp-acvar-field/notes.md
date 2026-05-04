# Notes

## Why This Experiment Matters

The current evidence already suggests that UI-authored fields and inline AutoLISP field strings may serialize differently. This comparison should determine whether `ezdxf` needs to support:

- a minimal inline field-string mode
- a full AutoCAD-compatible object-backed mode
- or both

## Recommended Inputs

Use the same baseline geometry and the same visible `MTEXT` location for both runs so the diff stays focused on field storage.

Current setup already satisfies this:

- UI-edit baseline contains one `MTEXT` with text `FIELD_BASE`
- AutoLISP comparison output uses the same one-entity shape and location

## Expected Outcome

Result: AutoCAD does support multiple storage representations for apparently similar fields.

## Practical Takeaway

For `ezdxf`, this suggests a likely split between:

1. inline field-string authoring support
2. full object-backed AutoCAD-compatible field authoring support

Those should probably be treated as separate feature levels rather than one implementation.
