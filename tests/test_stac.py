from stactools.noaa_gefs import stac


def test_create_collection() -> None:
    # Write tests for each for the creation of a STAC Collection
    # Create the STAC Collection...
    collection = stac.create_collection()
    collection.set_self_href("")

    # Check that it has some required attributes
    assert collection.id == "noaa-gefs"

    # Validate
    collection.validate()


def test_create_item() -> None:
    # Write tests for each for the creation of STAC Items
    # Create the STAC Item...
    item = stac.create_item("tests/data-files/ncep/atmos/geavg.t00z.pgrb2a.0p50.f000")

    # Check that it has some required attributes
    # assert item.id == "my-item-id"

    # Validate
    item.validate()
