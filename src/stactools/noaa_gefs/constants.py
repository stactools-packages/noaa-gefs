from pystac import Link, Provider, ProviderRole, RelType

RASTER_EXTENSION_V11 = "https://stac-extensions.github.io/raster/v1.1.0/schema.json"

DEFAULT_COLLECTION_ID = "noaa-gefs"
TITLE = "NOAA Global Ensemble Forecast System (GEFS)"
DESCRIPTION = (
    "The Global Ensemble Forecast System (GEFS) is a weather model created by the "
    "National Centers for Environmental Prediction (NCEP) that generates 21 separate "
    "forecasts (ensemble members) to address underlying uncertainties in the input "
    "data such limited coverage, instruments or observing systems biases, and the "
    "limitations of the model itself. "
    "GEFS quantifies these uncertainties by generating multiple forecasts, which in "
    "turn produce a range of potential outcomes based on differences or perturbations "
    "applied to the data after it has been incorporated into the model. "
    "Each forecast compensates for a different set of uncertainties.\n\n"
    "GEFS runs 4 times per day (00; 06; 12; 18UTC) with 31 members at each lead-time "
    "at C384L64 (about 25 km horizontal resolution and 64 vertical hybrid levels for "
    "atmosphere component) and out to 16 days at each cycle, except for 35 days at 0000 UTC."
)

KEYWORDS = ["NOAA", "GEFS", "global", "ensemble", "forecast", "GRIB2"]

PROVIDERS = [
    Provider(
        name="NOAA National Centers for Environmental Information",
        roles=[ProviderRole.PRODUCER, ProviderRole.LICENSOR],
        url="https://www.ncei.noaa.gov",
    ),
]

# I can't find a license that is directly associated with GEFS,
# but https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gefs/faq.php#
# links to the URL below ("Disclaimer"), which claims it is "public domain" and
# the GEFS data on AWS also states something similar ("Open Data").
LINK_LICENSE = Link(
    target="https://www.weather.gov/disclaimer",
    rel=RelType.LICENSE,
    media_type="text/html",
    title="Public Domain",
)
LINK_HOME = Link(
    target="https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast",
    rel="about",
    media_type="text/html",
    title="GEFS Homepage",
)


GRIB2_KEY = "grib2"
GRIB2_TITLE = "GRIB2 file"
GRIB2_MEDIATYPE = "application/wmo-GRIB2"
GRIB2_ROLES = ["data", "source"]

IDX_KEY = "index"
IDX_TITLE = "Index file"
# todo: is there a better alternative? looks like a CSV file but with : instead of ,
IDX_MEDIATYPE = "text/plain"
IDX_ROLES = ["metadata", "index"]
