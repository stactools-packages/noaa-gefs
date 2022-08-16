import logging
from typing import Optional

import click
from click import Command, Group
from pystac import Collection

from stactools.noaa_gefs import stac

logger = logging.getLogger(__name__)


def create_noaagefs_command(cli: Group) -> Command:
    """Creates the stactools-noaa-gefs command line utility."""

    @cli.group(
        "noaa-gefs",
        short_help=("Commands for working with stactools-noaa-gefs"),
    )
    def noaagefs() -> None:
        pass

    @noaagefs.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("destination")
    @click.option(
        "--id",
        default="",
        help="A custom collection ID, defaults to 'noaa-mrms-qpe-{t}h-pass{p}'",
    )
    @click.option(
        "--thumbnail",
        default="",
        help="URL for the PNG or JPEG collection thumbnail asset (none if empty)",
    )
    @click.option(
        "--start_time",
        default=None,
        help="The start timestamp for the temporal extent, defaults to now. "
        "Timestamps consist of a date and time in UTC and must be follow RFC 3339, section 5.6.",
    )
    def create_collection_command(
        destination: str,
        id: str = "",
        thumbnail: str = "",
        start_time: Optional[str] = None,
    ) -> None:
        """Creates a STAC Collection

        Args:
            destination (str): An HREF for the Collection JSON
        """
        collection = stac.create_collection(thumbnail, start_time)
        if len(id) > 0:
            collection.id = id
        collection.set_self_href(destination)
        collection.save_object()

        return None

    @noaagefs.command("create-item", short_help="Create a STAC item")
    @click.argument("source")
    @click.argument("destination")
    @click.option(
        "--collection",
        default="",
        help="An HREF to the Collection JSON. "
        "This adds the collection details to the item, but doesn't add the item to the collection.",
    )
    def create_item_command(
        source: str, destination: str, collection: str = ""
    ) -> None:
        """Creates a STAC Item

        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Item
        """
        stac_collection = None
        if len(collection) > 0:
            stac_collection = Collection.from_file(collection)

        item = stac.create_item(source, stac_collection)
        item.save_object(dest_href=destination)

        return None

    return noaagefs
