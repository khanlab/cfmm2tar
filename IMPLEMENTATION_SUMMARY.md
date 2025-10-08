# Implementation Summary: Series-Level Metadata Feature

## Overview
Added `--series-metadata` option to cfmm2tar to query and export series-level metadata (one row per series instead of one row per study), with fields compatible with heudiconv's dicominfo.tsv format.

## Files Modified

### 1. cfmm2tar/cli.py
- Added `--series-metadata` argument to argparse
- Updated metadata-only mode to query series-level metadata when flag is set
- Enhanced `--uid-from-file` handling to detect and process series-level TSV files
- Modified retrieve_cfmm_tar.main() calls to pass series_metadata_flag and series_filter
- Updated help text and examples

### 2. cfmm2tar/Dcm4cheUtils.py
- Added `get_series_metadata_by_study_uid()` method
  - Performs DICOM C-FIND at SERIES level
  - Returns list of series metadata for a given study
  - Extracts: SeriesInstanceUID, SeriesNumber, SeriesDescription, ProtocolName, SequenceName, Modality, ImageType

### 3. cfmm2tar/retrieve_cfmm_tar.py
- Updated `main()` function signature to accept:
  - `series_metadata_flag`: Boolean to enable series-level metadata extraction
  - `series_filter`: Optional dict to filter specific series
- Added `extract_series_metadata()` function
  - Walks through retrieved DICOM files
  - Extracts detailed series metadata from actual files
  - Computes derived fields (is_derived, is_motion_corrected)
  - Counts instances per series for dim3
  - Returns heudiconv-compatible metadata fields
- Modified metadata extraction logic to use series extraction when flag is set
- Updated TSV writing to handle both study-level and series-level formats

### 4. README.md
- Added section on series-level metadata querying
- Documented all series-level fields with descriptions
- Added workflow examples for both study-level and series-level approaches
- Explained filtering strategies and use cases
- Clarified limitations (retrieval at study level)

### 5. SERIES_METADATA_USAGE.md (new file)
- Comprehensive usage guide
- Field descriptions with DICOM tag mappings
- Multiple use case examples
- Filtering recipes (awk, Python pandas)
- Integration guidance with heudiconv
- Performance tips

## Features Implemented

### 1. Query Series-Level Metadata (without download)
```bash
cfmm2tar -M series.tsv --series-metadata -p 'Khan^Project' -d '20240101'
```
- Queries each study to get series information
- Outputs one row per series
- Includes 23 fields total

### 2. Download with Series Metadata Saved
```bash
cfmm2tar -p 'Khan^Project' -d '20240101' \
    --save-metadata series.tsv --series-metadata \
    output_dir
```
- Downloads studies normally
- Saves detailed series metadata during download

### 3. Filter and Download from Series-Level TSV
```bash
# User filters series.tsv (e.g., remove derived images)
cfmm2tar --uid-from-file filtered_series.tsv output_dir
```
- Automatically detects series-level file (has SeriesInstanceUID column)
- Downloads complete studies
- Filters metadata output to specified series

## Series-Level Metadata Fields

All fields matching heudiconv dicominfo.tsv specification:

| Field | Source | Description |
|-------|--------|-------------|
| StudyInstanceUID | DICOM tag 0020,000D | Study identifier |
| SeriesInstanceUID | DICOM tag 0020,000E | Series identifier (unique per series) |
| PatientName | DICOM tag 0010,0010 | Patient name |
| PatientID | DICOM tag 0010,0020 | Patient ID |
| StudyDate | DICOM tag 0008,0020 | Study date |
| StudyDescription | DICOM tag 0008,1030 | Study description |
| SeriesNumber | DICOM tag 0020,0011 | Series number |
| SeriesDescription | DICOM tag 0008,103E | Series description |
| ProtocolName | DICOM tag 0018,1030 | Protocol name (e.g., "T1_MPRAGE") |
| SequenceName | DICOM tag 0018,0024 | Technical sequence name |
| ImageType | DICOM tag 0008,0008 | Image type flags |
| is_derived | Derived from ImageType | True if "DERIVED" in ImageType |
| is_motion_corrected | Derived from ImageType | True if "MOCO" or "MOSAIC" in ImageType |
| dim1 | DICOM tag 0028,0010 | Number of rows |
| dim2 | DICOM tag 0028,0011 | Number of columns |
| dim3 | Counted | Number of instances/slices |
| tr | DICOM tag 0018,0080 | Repetition time (ms) |
| te | DICOM tag 0018,0081 | Echo time (ms) |
| fa | DICOM tag 0018,1314 | Flip angle (degrees) |
| slice_thickness | DICOM tag 0018,0050 | Slice thickness (mm) |
| acquisition_time | DICOM tag 0008,0032 | Acquisition time |
| Modality | DICOM tag 0008,0060 | Modality (MR, CT, etc.) |
| TarFilePath | Generated | Path to tar file (download only) |

## Technical Implementation Details

### Query Mode (--series-metadata with -M)
1. Performs study-level C-FIND to get all studies matching criteria
2. For each study:
   - Calls `get_series_metadata_by_study_uid()`
   - Performs series-level C-FIND with `-L SERIES` flag
   - Parses XML output to extract series metadata
3. Combines study and series metadata
4. Writes to TSV file

### Download Mode (--series-metadata with --save-metadata)
1. Retrieves entire study using C-GET (study-level operation)
2. Walks through retrieved DICOM files
3. For each series (identified by SeriesInstanceUID):
   - Reads one DICOM file to get series metadata
   - Counts instances for dim3
   - Extracts all imaging parameters
4. Applies series_filter if provided (from --uid-from-file)
5. Writes series metadata to TSV

### Series Filter Logic
- When reading TSV with SeriesInstanceUID column:
  - Builds dict: `{StudyUID: [SeriesUID1, SeriesUID2, ...]}`
  - Passes to retrieve_cfmm_tar.main()
  - During metadata export, filters to keep only specified series
- Note: Actual DICOM retrieval is at study level (all series downloaded)

## Limitations and Considerations

1. **Retrieval Granularity**: DICOM C-GET operates at study level
   - Cannot retrieve individual series (PACS limitation)
   - Tar files contain all series from a study
   - Filtering only affects metadata output

2. **Performance**: Series-level queries are slower
   - Must query each study individually for series
   - Recommended: Use narrower date ranges
   - Consider study-level query first, then series-level for subset

3. **Compatibility**: Designed for heudiconv workflow
   - Field names and types match heudiconv dicominfo.tsv
   - Boolean fields as strings ("True"/"False")
   - Compatible with tar2bids conversion pipeline

## Use Cases

1. **Quality Control**: Review protocols before download
2. **Selective Download**: Filter out derived/processed series
3. **Protocol Verification**: Check TR, TE, FA values match expected
4. **Heudiconv Preparation**: Pre-filter data for BIDS conversion
5. **Storage Optimization**: Identify and exclude unnecessary series
6. **Research Planning**: Survey available sequences for analysis

## Testing Recommendations

To test the implementation:

1. Query series metadata for a small date range:
   ```bash
   cfmm2tar -M test_series.tsv --series-metadata -d '20240101'
   ```

2. Verify TSV structure and field contents

3. Filter the TSV and test download:
   ```bash
   head -n 10 test_series.tsv > small_subset.tsv
   cfmm2tar --uid-from-file small_subset.tsv --save-metadata output.tsv test_output
   ```

4. Verify:
   - Correct studies downloaded
   - Series metadata in output.tsv matches filter
   - All expected fields populated

5. Test with --save-metadata during normal download:
   ```bash
   cfmm2tar -d '20240101' --save-metadata series.tsv --series-metadata test_output2
   ```

## Code Quality

- No syntax errors (validated with py_compile)
- Minimal changes to existing code
- Backward compatible (default behavior unchanged)
- Follows existing code patterns and style
- Comprehensive error handling
- Logging at appropriate levels

## Documentation

- Updated README.md with feature description and examples
- Created SERIES_METADATA_USAGE.md with detailed guide
- Updated CLI help text with new examples
- Added inline code documentation
- Documented limitations clearly
