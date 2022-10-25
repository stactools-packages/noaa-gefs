import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

import rasterio
from dateutil.parser import isoparse
from isodate import duration_isoformat
from pystac import (
    Asset,
    CatalogType,
    Collection,
    Extent,
    Item,
    MediaType,
    SpatialExtent,
    Summaries,
    TemporalExtent,
)
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.utils import datetime_to_str
from rasterio.crs import CRS

from . import constants

logger = logging.getLogger(__name__)


def create_collection(
    thumbnail: str = "",
    start_time: Optional[str] = None,
) -> Collection:
    """Create a STAC Collection for NOAA MRMS QPE sub-products.

    Args:
        thumbnail (str): URL for the PNG or JPEG collection thumbnail asset (none if empty)
        start_time (str): The start timestamp for the temporal extent, default to now.
            Timestamps consist of a date and time in UTC and must follow RFC 3339, section 5.6.

    Returns:
        Collection: STAC Collection object
    """
    # Time must be in UTC
    if start_time is None:
        start_datetime = datetime.now(tz=timezone.utc)
    else:
        start_datetime = isoparse(start_time)

    extent = Extent(
        SpatialExtent([[-180.0, 90.0, 180.0, -90.0]]),
        TemporalExtent([[start_datetime, None]]),
    )

    summaries = Summaries({})
    # summaries.add("forecast:horizon", ["PT0H", "PT6H", "PT12H", "PT18H"])
    summaries.add("processing:facility", ["US-NCEP"])

    collection = Collection(
        stac_extensions=[],
        id=constants.DEFAULT_COLLECTION_ID,
        title=constants.TITLE,
        description=constants.DESCRIPTION,
        keywords=constants.KEYWORDS,
        license="proprietary",
        providers=constants.PROVIDERS,
        extent=extent,
        summaries=summaries,
        catalog_type=CatalogType.RELATIVE_PUBLISHED,
    )

    collection.add_link(constants.LINK_LICENSE)
    collection.add_link(constants.LINK_HOME)

    if len(thumbnail) > 0:
        if thumbnail.endswith(".png"):
            media_type = MediaType.PNG
        else:
            media_type = MediaType.JPEG

        collection.add_asset(
            "thumbnail",
            Asset(
                href=thumbnail,
                title="Preview",
                roles=["thumbnail"],
                media_type=media_type,
            ),
        )

    item_assets = {}

    asset = create_grib2_asset()
    item_assets[constants.GRIB2_KEY] = AssetDefinition(asset)

    idx_asset = create_idx_asset()
    item_assets[constants.IDX_KEY] = AssetDefinition(idx_asset)

    item_assets_attrs = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_attrs.item_assets = item_assets

    return collection


def create_item(
    asset_href: str,
    collection: Optional[Collection] = None,
) -> Item:
    """Create a STAC Item

    This function should include logic to extract all relevant metadata from an
    asset, metadata asset, and/or a constants.py file.

    See `Item<https://pystac.readthedocs.io/en/latest/api.html#item>`_.

    Args:
        asset_href (str): The HREF pointing to an asset associated with the item
        collection (pystac.Collection): HREF to an existing collection

    Returns:
        Item: STAC Item object
    """
    with rasterio.open(asset_href, driver="GRIB") as dataset:

        # Go through bands and collect metadata
        band_numbers = range(1, dataset.count)
        discipline = set()
        element = set()
        forecast_seconds = set()
        ref_time = set()
        short_name = set()
        forecast_time = set()
        center = set()
        for i in band_numbers:
            meta = dataset.tags(i)
            # "GRIB_DISCIPLINE": "0(Meteorological)",
            # "GRIB_ELEMENT": "SCTAOTK",
            # "GRIB_FORECAST_SECONDS": "0",
            # "GRIB_IDS": "CENTER=7(US-NCEP) SUBCENTER=0 MASTER_TABLE=2 LOCAL_TABLE=1
            #   SIGNF_REF_TIME=1(Start_of_Forecast) REF_TIME=2022-08-12T00:00:00Z
            #   PROD_STATUS=0(Operational) TYPE=1(Forecast)",
            # "GRIB_PDS_PDTN": "48",
            # "GRIB_PDS_TEMPLATE_ASSEMBLED_VALUES":
            #   "20 112 62006 0 8 70 0 0 7 9 545 9 565 2 0 96 0 0 1 0 10 0 0 255 0 0",
            # "GRIB_PDS_TEMPLATE_NUMBERS":
            #   "20 112 242 54 0 8 0 0 0 70 0 0 0 0 0 7 9 0 0 2 33 9 0 0 2 53 2 0 96
            #   0 0 0 1 0 0 0 0 10 0 0 0 0 0 255 0 0 0 0 0",
            # "GRIB_REF_TIME": "1660262400",
            # "GRIB_SHORT_NAME": "0-EATM",
            # "GRIB_VALID_TIME": "1660262400",

            # Collection values in metadata
            if "GRIB_DISCIPLINE" in meta:
                discipline.add(meta["GRIB_DISCIPLINE"])
            if "GRIB_ELEMENT" in meta:
                element.add(meta["GRIB_ELEMENT"])
            if "GRIB_FORECAST_SECONDS" in meta:
                forecast_seconds.add(int(meta["GRIB_FORECAST_SECONDS"]))
            if "GRIB_REF_TIME" in meta:
                ref_time.add(int(meta["GRIB_REF_TIME"]))
            if "GRIB_SHORT_NAME" in meta:
                short_name.add(meta["GRIB_SHORT_NAME"])
            if "GRIB_VALID_TIME" in meta:
                forecast_time.add(int(meta["GRIB_VALID_TIME"]))
            # todo: parse SIGNF_REF_TIME=1(Start_of_Forecast)?
            # https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table1-2.shtml

            # Parse GRIB IDs field
            grib_ids = dict()
            if "GRIB_IDS" in meta:
                entries = meta["GRIB_IDS"].split()
                for entry in entries:
                    try:
                        [key, value] = entry.split("=", 1)
                        grib_ids[key] = value
                    except ValueError:
                        continue

            # Collection values in parsed GRIB IDs
            if "CENTER" in grib_ids and grib_ids["CENTER"] != 0:
                code = grib_ids["CENTER"]
                if "SUBCENTER" in grib_ids and grib_ids["SUBCENTER"] != "0":
                    code += " "
                    code += grib_ids["SUBCENTER"]
                center.add(code)

        forecast_timestamps: List[Optional[int]] = []
        if len(forecast_time) == 1:
            forecast_timestamps.append(forecast_time.pop())
        elif len(forecast_time) == 2:
            forecast_timestamps.append(min(forecast_time))
            forecast_timestamps.append(max(forecast_time))
        elif len(forecast_time) > 2:
            forecast_timestamps.append(min(forecast_time))
            forecast_timestamps.append(None)

        forecast_datetimes: List[Optional[datetime]] = []
        for timestamp in forecast_timestamps:
            forecast_datetimes.append(
                None if timestamp is None else timestamp_to_datetime(timestamp)
            )

        # Compile information for the item
        id_parts = list(map(lambda ts: str(ts), forecast_timestamps))
        basename = os.path.basename(asset_href)
        [filename, ext] = os.path.splitext(basename)
        # Some source files don't have the .grib2 extension!
        if ext != ".grib2" and ext != ".grb2":
            filename = basename
        id_parts.append(filename)

        [w, s, e, n] = dataset.bounds
        bbox = [w, n, e, s]
        geometry = bbox_to_polygon(bbox)

        add_ts_ext = False
        stac_extensions = [constants.RASTER_EXTENSION]
        if len(forecast_seconds) > 0 or len(forecast_time) > 0:
            stac_extensions.append(constants.FORECAST_EXTENSION)

        # Add properties to Item - common data has been extracted from the bands
        properties: Dict[str, Any] = {}
        forecast_datetime_instance: Optional[datetime] = None
        if len(forecast_datetimes) == 1:
            forecast_datetime_instance = forecast_datetimes[0]
            if forecast_datetime_instance is not None:
                properties["expires"] = temporal_to_iso(forecast_datetime_instance)
            add_ts_ext = True
        elif len(forecast_datetimes) == 2:
            properties["start_datetime"] = forecast_datetimes[0]
            properties["end_datetime"] = forecast_datetimes[1]
            if properties["end_datetime"] is not None:
                properties["expires"] = temporal_to_iso(properties["end_datetime"])
                add_ts_ext = True

        if len(discipline) == 1:
            properties["grib:discipline"] = parse_discipline(discipline.pop())

        if len(element) == 1:
            properties["grib:element"] = parse_bracket_str(element.pop())

        if len(ref_time) == 1:
            dt = temporal_to_iso(ref_time.pop())
            properties["forecast:reference_datetime"] = dt
        elif len(ref_time) > 1:
            raise Exception("Can't encode multiple reference datetimes")

        if len(forecast_seconds) == 1:
            properties["forecast:horizon"] = seconds_to_duration(forecast_seconds.pop())

        if len(center) == 1:
            properties["processing:facility"] = " ".join(
                map(lambda f: parse_bracket_str(f), center.pop().split())
            )

        # Create the item
        item = Item(
            stac_extensions=stac_extensions,
            id=constants.ID_SEP.join(id_parts),
            properties=properties,
            geometry=geometry,
            bbox=bbox,
            datetime=forecast_datetime_instance,
            collection=collection,
        )

        # Projection extension
        proj_attrs = ProjectionExtension.ext(item, add_if_missing=True)
        if isinstance(dataset.crs, CRS):
            proj_attrs.epsg = None
            proj_attrs.projjson = dataset.crs.to_dict(projjson=True)
        if len(dataset.shape) == 2:
            proj_attrs.shape = [dataset.shape[1], dataset.shape[0]]
        if dataset.transform:
            proj_attrs.transform = list(dataset.transform)[0:6]

        # Add Grib2 asset to the item (was filled above)
        asset = create_grib2_asset(asset_href)
        asset["raster:bands"] = []
        for i in band_numbers:
            stats = dataset.statistics(i)
            band = {
                # todo: check whether this is always valid
                "data_type": dataset.dtypes[i],
                "statistics": {
                    "minimum": stats.min,
                    "maximum": stats.max,
                    "mean": stats.mean,
                    "stddev": stats.std,
                },
            }

            meta = dataset.tags(i)

            if "GRIB_COMMENT" in meta:
                # Remove the unit from the comment
                band["description"] = re.sub(
                    r"\s*\[[^\]]+\]$", "", meta["GRIB_COMMENT"]
                )
            elif dataset.descriptions[i] is not None:
                band["description"] = dataset.descriptions[i]

            if "GRIB_UNIT" in meta:
                # Remove the square brackets from the unit
                unit = meta["GRIB_UNIT"].strip("[]")
                # Numeric is not a valid value
                if unit != "Numeric":
                    band["unit"] = unit
            elif dataset.units[i] is not None:
                band["unit"] = dataset.units[i]

            offset = dataset.offsets[i]
            scale = dataset.scales[i]
            if scale != 1 or offset != 0:
                band["scale"] = scale
                band["offset"] = offset

            if len(discipline) > 1 and "GRIB_DISCIPLINE" in meta:
                band["grib:discipline"] = parse_discipline(meta["GRIB_DISCIPLINE"])

            if len(element) > 1 and "GRIB_ELEMENT" in meta:
                band["grib:element"] = parse_discipline(meta["GRIB_ELEMENT"])

            if "GRIB_SHORT_NAME" in meta:
                band["grib:short_name"] = meta["GRIB_SHORT_NAME"]

            if len(forecast_seconds) > 1 and "GRIB_FORECAST_SECONDS" in meta:
                band["forecast:horizon"] = seconds_to_duration(
                    meta["GRIB_FORECAST_SECONDS"]
                )

            if len(forecast_time) > 1 and "GRIB_VALID_TIME" in meta:
                dt = temporal_to_iso(meta["GRIB_VALID_TIME"])
                band["datetime"] = dt
                band["expires"] = dt
                add_ts_ext = True

            asset["raster:bands"].append(band)

        item.add_asset(constants.GRIB2_KEY, Asset.from_dict(asset))

        # Add Index assets to the item (if available)
        idx_href = asset_href + ".idx"
        if os.path.exists(idx_href):
            idx_asset = create_idx_asset(idx_href)
            item.add_asset(constants.IDX_KEY, Asset.from_dict(idx_asset))

        if add_ts_ext:
            item.stac_extensions.append(constants.TIMESTAMPS_EXTENSION)

        return item


def create_grib2_asset(href: Optional[str] = None) -> Dict[str, Any]:
    asset: Dict[str, Any] = {
        "roles": constants.GRIB2_ROLES,
        "type": constants.GRIB2_MEDIATYPE,
        "title": constants.GRIB2_TITLE,
        "description": constants.GRIB2_DESCRIPTION,
    }
    if href is not None:
        asset["href"] = href
    return asset


def create_idx_asset(href: Optional[str] = None) -> Dict[str, Any]:
    asset: Dict[str, Any] = {
        "roles": constants.IDX_ROLES,
        "type": constants.IDX_MEDIATYPE,
        "title": constants.IDX_TITLE,
        "description": constants.IDX_DESCRIPTION,
    }
    if href is not None:
        asset["href"] = href
    return asset


def bbox_to_polygon(b: List[float]) -> Dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [[b[0], b[3]], [b[2], b[3]], [b[2], b[1]], [b[0], b[1]], [b[0], b[3]]]
        ],
    }


def seconds_to_duration(seconds: int) -> str:
    if seconds == 0:
        return "PT0H"
    return str(duration_isoformat(timedelta(seconds=seconds)))


def timestamp_to_datetime(seconds: int) -> datetime:
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def temporal_to_iso(temporal: Union[datetime, int]) -> str:
    if isinstance(temporal, int):
        temporal = timestamp_to_datetime(temporal)
    return datetime_to_str(temporal)


def parse_discipline(str: str) -> str:
    return parse_bracket_str(str).lower()


def parse_bracket_str(str: str) -> str:
    return re.sub(r"\d+\(([^\)]+)\)$", r"\1", str)
