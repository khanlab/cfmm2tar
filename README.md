# cfmm2tar

Download a tarballed DICOM dataset from the CFMM DICOM server

## Requirements

- Python 3.11+
- uv (for dependency management)

## Docker image

1. Install Docker

2. Clone this repo and build the image:

```bash
git clone https://github.com/khanlab/cfmm2tar
cd cfmm2tar
docker build -t cfmm2tar .
```

3. Run the containerized `cfmm2tar`:

```bash
OUTPUT_DIR=/path/to/dir
mkdir ${OUTPUT_DIR}
docker run -i -t --rm --volume ${OUTPUT_DIR}:/data cfmm2tar
```

This will display help on using `cfmm2tar`

Search and download a specific dataset, e.g.

```bash
docker run -i -t --rm --volume ${OUTPUT_DIR}:/data cfmm2tar -p 'Everling^Marmoset' -d '20180803' /data
```

(You will be asked for your UWO username and password, and will only be able to find and download datasets to which you have read permissions).

## Local Installation

### Using uv (recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e .
```

### Using pip

```bash
pip install -r requirements.txt
```
