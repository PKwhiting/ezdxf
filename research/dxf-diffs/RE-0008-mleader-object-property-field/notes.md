# Notes

## Why This Experiment Matters

`MTEXT` and `TEXT` object-property fields were already understood well enough to
generate stable host structures. `MULTILEADER` still showed a host-specific
roundtrip difference, so a UI-authored baseline was needed to separate generic
field behavior from `MULTILEADER` content encoding.

## Most Important Host-Specific Observation

The `MULTILEADER` `_text` wrapper is not shaped like the `MTEXT`/`TEXT`
wrappers:

1. it uses wrapper flag `94 = 9`
2. it omits the `ACFD_FIELDTEXT_CHECKSUM` dataset entirely

## Cache Behavior Note

The manually edited file saves with a normalized child `AcObjProp` cache:

- top-level `94 = 27`
- `ACFD_FIELD_VALUE` starts with `93 = 0`
- `302` and `301` are blank

But repeated Core Console saves do not converge. They alternate between two
cache states. A second save flips that child cache back to the populated form:

- top-level `94 = 59`
- `ACFD_FIELD_VALUE` starts with `93 = 4`
- `302` and `301` contain `10.0000`

And the next save flips it back to the normalized form again.

The field graph survives both states.
