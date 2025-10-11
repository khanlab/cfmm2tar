# cfmm2tar API Examples

This directory contains example scripts demonstrating how to use the cfmm2tar Python API.

## Files

- **`api_usage.py`**: Interactive examples showing various API usage patterns
- **`Snakefile_example`**: Example Snakemake workflow using the API

## Running the Examples

### Interactive API Examples

Run the interactive examples script:

```bash
python examples/api_usage.py
```

This will present a menu with different examples:
1. Query study metadata (list)
2. Query study metadata (DataFrame)
3. Download studies by search criteria
4. Query then download filtered studies (complete workflow)
5. Download from metadata file

### Snakemake Workflow

To run the Snakemake workflow example:

1. Create a `config.yaml` file:
   ```yaml
   username: "your_username"
   password: "your_password"
   project: "Khan^TestProject"
   date_range: "20240101-20240131"
   ```

2. Run the workflow:
   ```bash
   snakemake --snakefile examples/Snakefile_example --cores 1
   ```

   Or provide config via command line:
   ```bash
   snakemake --snakefile examples/Snakefile_example --cores 1 \
       --config username=myuser password=mypass project="Khan^TestProject"
   ```

## Example Code Snippets

### Basic Query

```python
from cfmm2tar import query_metadata

studies = query_metadata(
    username="your_username",
    password="your_password",
    study_description="Khan^NeuroAnalytics",
    study_date="20240101-20240131"
)

print(f"Found {len(studies)} studies")
```

### Query with DataFrame

```python
from cfmm2tar import query_metadata

df = query_metadata(
    username="your_username",
    password="your_password",
    study_description="Khan^*",
    return_type="dataframe"
)

# Filter and analyze
recent = df[df['StudyDate'] > '20240601']
print(recent.head())
```

### Download Studies

```python
from cfmm2tar import download_studies

download_studies(
    username="your_username",
    password="your_password",
    output_dir="/path/to/output",
    study_description="Khan^TestProject",
    study_date="20240101"
)
```

### Complete Workflow

```python
from cfmm2tar import query_metadata, download_studies_from_metadata

# Query
studies = query_metadata(
    username="your_username",
    password="your_password",
    study_description="Khan^*",
    study_date="20240101-20240131",
    return_type="dataframe"
)

# Filter
filtered = studies[studies['PatientName'].str.contains('subj01')]

# Download
download_studies_from_metadata(
    username="your_username",
    password="your_password",
    output_dir="/path/to/output",
    metadata=filtered
)
```

## Tips

- Store credentials securely (e.g., environment variables, config files with restricted permissions)
- Use the DataFrame return type for advanced filtering and analysis
- The metadata file can be used for reproducible downloads
- Combine with other tools in your workflow (BIDS conversion, quality checks, etc.)
