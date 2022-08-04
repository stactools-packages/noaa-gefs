# stactools-noaa-gefs

[![PyPI](https://img.shields.io/pypi/v/stactools-noaa-gefs)](https://pypi.org/project/stactools-noaa-gefs/)

- Name: noaa-gefs
- Package: `stactools.noaa_gefs`
- PyPI: https://pypi.org/project/stactools-noaa-gefs/
- Owner: @m-mohr
- Dataset homepage: https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast
- STAC extensions used:
  - [proj](https://github.com/stac-extensions/projection/)
- Extra fields:
  - `noaa-gefs:custom`: A custom attribute

A short description of the package and its usage.

## STAC Examples

- [Collection](examples/collection.json)
- [Item](examples/item/item.json)

## Installation
```shell
pip install stactools-noaa-gefs
```

## Command-line Usage

Description of the command line functions

```shell
$ stac noaa-gefs create-item source destination
```

Use `stac noaa-gefs --help` to see all subcommands and options.

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
