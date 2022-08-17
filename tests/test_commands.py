import os.path
from tempfile import TemporaryDirectory
from typing import Callable, List

import pystac
from click import Command, Group
from stactools.testing.cli_test import CliTestCase

from stactools.noaa_gefs.commands import create_noaagefs_command


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_noaagefs_command]

    def test_create_collection(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            destination = os.path.join(tmp_dir, "collection.json")

            result = self.run_command(f"noaa-gefs create-collection {destination}")

            assert result.exit_code == 0, "\n{}".format(result.output)

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            assert len(jsons) == 1

            collection = pystac.read_file(destination)
            assert collection.id == "noaa-gefs"

            collection.validate()

    def test_create_item(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            infile = "tests/data-files/ncep/atmos/geavg.t00z.pgrb2a.0p50.f000"
            destination = os.path.join(tmp_dir, "item.json")
            result = self.run_command(f"noaa-gefs create-item {infile} {destination}")
            assert result.exit_code == 0, "\n{}".format(result.output)

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            assert len(jsons) == 1

            item = pystac.read_file(destination)
            # assert item.id == "my-item-id"

            item.validate()
