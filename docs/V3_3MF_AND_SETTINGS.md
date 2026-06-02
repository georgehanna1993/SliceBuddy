# SliceBuddy v3: 3MF and richer slicer settings

## What changed

- The upload flow accepts STL and 3MF model files.
- 3MF archives are inspected in memory without extracting arbitrary files.
- Archive member count, expanded archive size, and model XML size are bounded.
- 3MF units are converted to millimeters before geometry analysis.
- 3MF build items, component references, and transforms are resolved.
- Deterministic plans include conservative print, outer-wall, first-layer,
  travel, support, and bridge speeds.
- Plans include cooling and temperature-profile guidance without inventing
  printer-specific temperatures.

## Reliability boundary

3MF is a broad container format. SliceBuddy uses standardized geometry, unit,
build-item, and component data. It intentionally does not trust or apply
vendor-specific slicer metadata as though it were universal.

STL files remain supported. Because STL files do not declare units, SliceBuddy
continues to assume millimeters for STL dimensions.
