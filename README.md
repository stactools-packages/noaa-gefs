# stactools-noaa-gefs

[![PyPI](https://img.shields.io/pypi/v/stactools-noaa-gefs)](https://pypi.org/project/stactools-noaa-gefs/)

- Name: noaa-gefs
- Package: `stactools.noaa_gefs`
- PyPI: https://pypi.org/project/stactools-noaa-gefs/
- Owner: @m-mohr
- Dataset homepage: <https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast>
- STAC extensions used:
  - [forecast](https://github.com/stac-extensions/forecast/)
  - [raster](https://github.com/stac-extensions/raster/)
  - [processing](https://github.com/stac-extensions/processing/)
  - [proj](https://github.com/stac-extensions/projection/)
  - [timestamps](https://github.com/stac-extensions/timestamps/)
- Extra fields:
  - `grib:discipline`: The discipline as lower-case string (e.g. `SCTAOTK`)
  - `grib:element`: The element type as string (e.g. `meteorological`)
  - `grib:short_name`: The short name as string (e.g. `0-SFC`)

A stactools package for NOAA's Global Ensemble Forecast System (GEFS) dataset.

This package can generate STAC files from GRIB2 files that link to the original GRIB2 files (+ .idx sidecar files).

## STAC Examples

- [Collection](examples/collection.json)
- [Item](examples/item.json)
- [Browse the example in a human-readable form](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/noaa-gefs/main/examples/collection.json)

## Installation

```shell
pip install stactools-noaa-gefs
```

## Command-line Usage

Use `stac noaa-gefs --help` to list all commands and options.

### Collection

Create a collection:

```shell
stac noaa-gefs create-collection collection.json
```

Get information about all options for collection creation:

```shell
stac noaa-gefs create-collection --help
```

### Item

Create an item:

```shell
stac noaa-gefs create-item /path/to/gefs.chem.t00z.a2d_0p25.f000.grib2 item.json --collection collection.json
```

Get information about all options for item creation:

```shell
stac noaa-gefs create-item --help
```

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
$ pip install -e .
$ pip install -r requirements-dev.txt
$ pre-commit install
```

To check all files:

```shell
$ pre-commit run --all-files
```

To run the tests:

```shell
$ pytest -vv
```
