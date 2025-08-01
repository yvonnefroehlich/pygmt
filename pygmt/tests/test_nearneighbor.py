"""
Test pygmt.nearneighbor.
"""

from pathlib import Path

import numpy as np
import numpy.testing as npt
import pytest
import xarray as xr
from pygmt import nearneighbor
from pygmt.datasets import load_sample_data
from pygmt.enums import GridRegistration, GridType
from pygmt.exceptions import GMTTypeError
from pygmt.helpers import GMTTempFile


@pytest.fixture(scope="module", name="ship_data")
def fixture_ship_data():
    """
    Load the table data from the sample bathymetry dataset.
    """
    return load_sample_data(name="bathymetry")


@pytest.mark.parametrize("array_func", [np.array, xr.Dataset])
def test_nearneighbor_input_data(array_func, ship_data):
    """
    Run nearneighbor by passing in a numpy.array or xarray.Dataset.
    """
    data = array_func(ship_data)
    output = nearneighbor(
        data=data, spacing="5m", region=[245, 255, 20, 30], search_radius="10m"
    )
    assert isinstance(output, xr.DataArray)
    assert output.gmt.registration is GridRegistration.GRIDLINE
    assert output.gmt.gtype is GridType.GEOGRAPHIC
    assert output.shape == (121, 121)
    npt.assert_allclose(output.mean(), -2378.2385)


@pytest.mark.benchmark
def test_nearneighbor_input_xyz(ship_data):
    """
    Run nearneighbor by passing in x, y, z numpy.ndarrays individually.
    """
    output = nearneighbor(
        x=ship_data.longitude,
        y=ship_data.latitude,
        z=ship_data.bathymetry,
        spacing="5m",
        region=[245, 255, 20, 30],
        search_radius="10m",
    )
    assert isinstance(output, xr.DataArray)
    assert output.shape == (121, 121)
    npt.assert_allclose(output.mean(), -2378.2385)


def test_nearneighbor_wrong_kind_of_input(ship_data):
    """
    Run nearneighbor using grid input that is not file/matrix/vectors.
    """
    data = ship_data.bathymetry.to_xarray()  # convert pandas.Series to xarray.DataArray
    with pytest.raises(GMTTypeError):
        nearneighbor(
            data=data, spacing="5m", region=[245, 255, 20, 30], search_radius="10m"
        )


def test_nearneighbor_with_outgrid_param(ship_data):
    """
    Run nearneighbor with the 'outgrid' parameter.
    """
    with GMTTempFile() as tmpfile:
        output = nearneighbor(
            data=ship_data,
            spacing="5m",
            region=[245, 255, 20, 30],
            outgrid=tmpfile.name,
            search_radius="10m",
        )
        assert output is None  # check that output is None since outgrid is set
        assert Path(tmpfile.name).stat().st_size > 0  # check that outgrid exists
        grid = xr.load_dataarray(tmpfile.name, engine="gmt", raster_kind="grid")
        assert isinstance(grid, xr.DataArray)  # ensure netCDF grid loads ok
        assert grid.shape == (121, 121)
        npt.assert_allclose(grid.mean(), -2378.2385)
