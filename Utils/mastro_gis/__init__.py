import logging
logging.basicConfig(level=logging.getLevelName('INFO'))

from .checkdeps import HAS_GDAL, HAS_PYPROJ, HAS_IMGIO, HAS_PIL
from .settings import settings
from .errors import OverlapError

from .utils import XY, BBOX

from .proj import reprojPt, reprojBbox, meters2dd

from .georaster import GeoRaster, NpImage

from .basemaps import GRIDS, SOURCES, MapService
