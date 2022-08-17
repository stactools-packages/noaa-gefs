import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import rasterio
from dateutil.parser import isoparse
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

# from pystac.extensions.raster import DataType
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
    summaries.add("example", ["abc"])

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
    item = None

    with rasterio.open(asset_href) as dataset:

        [w, s, e, n] = dataset.bounds
        bbox = [w, n, e, s]
        geometry = bbox_to_polygon(bbox)

        time = datetime.now(tz=timezone.utc)

        properties: Dict[str, Any] = {}
        id = str(time) + "_" + dataset.name

        item = Item(
            # Raster extension v1.1 not supported by PySTAC
            stac_extensions=[constants.RASTER_EXTENSION_V11],
            id=id,
            properties=properties,
            geometry=geometry,
            bbox=bbox,
            datetime=time,
            collection=collection,
        )

        # Projection extension for assets
        proj_attrs = ProjectionExtension.ext(item, add_if_missing=True)
        if isinstance(dataset.crs, CRS):
            proj_attrs.epsg = None
            proj_attrs.projjson = dataset.crs.to_dict(projjson=True)
        if len(dataset.shape) == 2:
            proj_attrs.shape = [dataset.shape[1], dataset.shape[0]]
        if dataset.transform:
            proj_attrs.transform = list(dataset.transform)[0:6]

        # Add GRIB2 assets to the item
        asset = create_grib2_asset(asset_href)

        asset["raster:bands"] = []
        for i in range(1, dataset.count):
            stats = dataset.statistics(i)
            band = {
                "data_type": dataset.dtypes[i],  # todo: check whether that is valid
                "statistics": {
                    "minimum": stats.min,
                    "maximum": stats.max,
                    "mean": stats.mean,
                    "stddev": stats.std,
                },
            }

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

            asset["raster:bands"].append(band)

        item.add_asset(constants.GRIB2_KEY, Asset.from_dict(asset))

        # Add Index assets to the item (if available)
        [path, ext] = os.path.splitext(asset_href)
        if ext == "grib2" or ext == "grb2":
            idx_href = path + ".idx"
        else:
            # Some source files don't have the .grib2 extension!
            idx_href = asset_href + ".idx"

        if os.path.exists(idx_href):
            idx_asset = create_idx_asset(idx_href)
            item.add_asset(constants.IDX_KEY, Asset.from_dict(idx_asset))

    return item


def create_grib2_asset(href: Optional[str] = None) -> Dict[str, Any]:
    asset: Dict[str, Any] = {
        "roles": constants.GRIB2_ROLES,
        "type": constants.GRIB2_MEDIATYPE,
        "title": constants.GRIB2_TITLE,
    }
    if href is not None:
        asset["href"] = href
    return asset


def create_idx_asset(href: Optional[str] = None) -> Dict[str, Any]:
    asset: Dict[str, Any] = {
        "roles": constants.IDX_ROLES,
        "type": constants.IDX_MEDIATYPE,
        "title": constants.IDX_TITLE,
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
