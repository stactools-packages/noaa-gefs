import stactools.core
from stactools.cli.registry import Registry

from stactools.noaa_gefs.stac import create_collection, create_item

__all__ = ["create_collection", "create_item"]

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.noaa_gefs import commands

    registry.register_subcommand(commands.create_noaagefs_command)


__version__ = "0.1.0"
