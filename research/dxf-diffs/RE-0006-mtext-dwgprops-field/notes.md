# Notes

## Noise Observed

- Standard AutoCAD save noise in classes, dictionaries, and unrelated object sections.

## Open Questions

1. Do all standard DWGPROPS fields map to the `CustomDP.*` naming pattern?
2. Are custom DWGPROPS entries stored the same way as the standard `Title` property?
3. Does the `%tc1` format appear consistently for other string drawing properties?

## Recommended Follow-Up Experiments

1. Compare `Title` against another standard drawing property such as `Subject` or `Comments`.
2. Compare `Title` against a custom DWGPROPS property from the custom tab.
3. Once the property naming pattern is clear, add convenience authoring support in `ezdxf`.
