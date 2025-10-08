# Series-Level Metadata Feature Usage Guide

## Overview

The `--series-metadata` option enables querying and filtering DICOM studies at the series level, providing detailed metadata similar to heudiconv's `dicominfo.tsv` format.

## Use Cases

### 1. Query Series-Level Metadata

Export detailed series information for review:

```bash
cfmm2tar -M series_metadata.tsv --series-metadata -p 'Khan^Project' -d '20240101'
```

This creates a TSV file with one row per series containing:
- Study identifiers (StudyInstanceUID, PatientName, PatientID, StudyDate)
- Series identifiers (SeriesInstanceUID, SeriesNumber, SeriesDescription)
- Protocol information (ProtocolName, SequenceName, Modality)
- Image properties (ImageType, is_derived, is_motion_corrected)
- Dimensions (dim1, dim2, dim3)
- Imaging parameters (tr, te, fa, slice_thickness)
- Timing (acquisition_time)

### 2. Filter Series Before Download

After querying, you can filter the TSV file to select specific series:

```bash
# Filter out derived series (keep only original acquisitions)
awk -F'\t' 'NR==1 || $12=="False"' series_metadata.tsv > original_only.tsv

# Filter for specific protocols (e.g., only T1-weighted)
grep -E "^|T1" series_metadata.tsv > t1_series.tsv

# Filter by modality
awk -F'\t' 'NR==1 || $22=="MR"' series_metadata.tsv > mr_only.tsv
```

### 3. Download with Series Filter

When you use `--uid-from-file` with a series-level TSV, cfmm2tar:
1. Detects that it's a series-level file (has SeriesInstanceUID column)
2. Downloads the complete studies
3. When `--save-metadata` is used, only writes metadata for the specified series

```bash
cfmm2tar --uid-from-file original_only.tsv --save-metadata downloaded.tsv output_dir
```

**Important Limitation:** The tar file will contain ALL series from each study because DICOM retrieval (C-GET) operates at the study level. The series filtering only affects which series metadata is written to the output TSV file. If you need to exclude specific series from the tar files, you'll need to filter them after retrieval (e.g., using DICOM tools or during tar2bids conversion).

### 4. Normal Download with Series Metadata

You can also download studies normally while saving series-level metadata:

```bash
cfmm2tar -p 'Khan^Project' -d '20240101' \
    --save-metadata series_info.tsv --series-metadata \
    output_dir
```

This downloads all matching studies and saves detailed series metadata alongside them.

## Field Descriptions

| Field | Description | DICOM Tag |
|-------|-------------|-----------|
| `StudyInstanceUID` | Unique study identifier | 0020,000D |
| `SeriesInstanceUID` | Unique series identifier | 0020,000E |
| `PatientName` | Patient name | 0010,0010 |
| `PatientID` | Patient ID | 0010,0020 |
| `StudyDate` | Study date (YYYYMMDD) | 0008,0020 |
| `StudyDescription` | Study description | 0008,1030 |
| `SeriesNumber` | Series number | 0020,0011 |
| `SeriesDescription` | Series description | 0008,103E |
| `ProtocolName` | Protocol name | 0018,1030 |
| `SequenceName` | Sequence name | 0018,0024 |
| `ImageType` | Image type flags | 0008,0008 |
| `is_derived` | Is derived image (Boolean) | Derived from ImageType |
| `is_motion_corrected` | Is motion corrected (Boolean) | Derived from ImageType |
| `dim1` | Image rows | 0028,0010 |
| `dim2` | Image columns | 0028,0011 |
| `dim3` | Number of slices/instances | Counted |
| `tr` | Repetition time (ms) | 0018,0080 |
| `te` | Echo time (ms) | 0018,0081 |
| `fa` | Flip angle (degrees) | 0018,1314 |
| `slice_thickness` | Slice thickness (mm) | 0018,0050 |
| `acquisition_time` | Acquisition time | 0008,0032 |
| `Modality` | Imaging modality | 0008,0060 |
| `TarFilePath` | Path to tar file (download only) | Generated |

## Comparison with Study-Level Metadata

### Study-Level (default):
- One row per study
- Basic study information only
- Faster queries
- Suitable for downloading complete studies

```bash
cfmm2tar -M study_metadata.tsv -p 'Khan^Project' -d '20240101'
```

Output columns: `StudyInstanceUID`, `PatientName`, `PatientID`, `StudyDate`, `StudyDescription`

### Series-Level (with --series-metadata):
- One row per series
- Detailed series and imaging parameters
- Takes longer to query (must query each series)
- Suitable for selective series filtering

```bash
cfmm2tar -M series_metadata.tsv --series-metadata -p 'Khan^Project' -d '20240101'
```

Output: All fields listed in the table above

## Integration with Heudiconv

The series-level metadata format is designed to be compatible with heudiconv's `dicominfo.tsv`:

1. **Query series metadata:**
   ```bash
   cfmm2tar -M series_metadata.tsv --series-metadata -p 'Khan^Project' -d '20240101'
   ```

2. **Review and filter series** based on your heuristic needs

3. **Download filtered studies:**
   ```bash
   cfmm2tar --uid-from-file series_metadata_filtered.tsv output_dir
   ```

4. **Convert with tar2bids/heudiconv:**
   ```bash
   tar2bids -i output_dir -o bids_dir -h heuristic.py
   ```

The metadata helps you:
- Exclude derived series before conversion
- Verify protocol compliance
- Plan heudiconv heuristics
- Document acquisition parameters

## Tips

1. **Performance:** Series-level queries take longer because they must query each study individually. For large date ranges, consider:
   - Querying study-level first, then series-level for specific studies
   - Using smaller date ranges
   - Running queries during off-peak hours

2. **Filtering:** Common filters for series metadata:
   ```bash
   # Original images only
   awk -F'\t' 'NR==1 || $12=="False"' series.tsv > original.tsv
   
   # Exclude motion correction
   awk -F'\t' 'NR==1 || $13=="False"' series.tsv > no_moco.tsv
   
   # Specific TR range (e.g., 1900-2100 ms)
   awk -F'\t' 'NR==1 || ($17>=1900 && $17<=2100)' series.tsv > filtered_tr.tsv
   ```

3. **Excel/LibreOffice:** The TSV files can be opened in spreadsheet applications for easier filtering and sorting.

4. **Python:** For complex filtering:
   ```python
   import pandas as pd
   
   df = pd.read_csv('series_metadata.tsv', sep='\t')
   
   # Filter for original T1-weighted images
   filtered = df[
       (df['is_derived'] == 'False') & 
       (df['ProtocolName'].str.contains('T1', case=False))
   ]
   
   filtered.to_csv('t1_original.tsv', sep='\t', index=False)
   ```
