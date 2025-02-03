from pathlib import Path


# Define directories
REPO_ROOT_DIR = Path(__file__).parent.parent

DATA_DIR_NAME = Path(__file__).parent.parent.name.replace("Code", "Data")

DATA_DIR = REPO_ROOT_DIR.parent / DATA_DIR_NAME
SPATIAL_DATA = DATA_DIR / "spatial_data"
STREET_NETWORKS = SPATIAL_DATA / "street_networks"
POINT_GRIDS = SPATIAL_DATA / "point_grids"
PANO_DIR = SPATIAL_DATA / "pano_data"
GVI_DIR = SPATIAL_DATA / "greenview_index"

MAP_DIR = DATA_DIR / 'maps/Kypseli-All'
MAP_SHAPE_FILE = MAP_DIR / 'Kypseli-All.shp'
GSV_DIR_METADATA = DATA_DIR / 'maps/Kypseli-All/metadata/'

GENERATED_DIR = MAP_DIR / "generated"
METADATA_DIR = MAP_DIR / "metadata"

MAP_A3_GENERATED = GENERATED_DIR / "A3-Generated.gpkg"
MAP_A30_GENERATED = GENERATED_DIR / "A30-Generated.gpkg"
MAP_A300_GENERATED = GENERATED_DIR / "A300-Generated.gpkg"
MAP_ALL_GENERATED = GENERATED_DIR / "ALL-Generated.gpkg"

MAP_BUILDINGS_GENERATED = GENERATED_DIR / "Buildings-Generated.gpkg"
MAP_BUILDINGS_GENERATED_ORG = GENERATED_DIR / "Buildings-Generated-ORG.gpkg"


MAP_A3_TREE_LOCATIONS = GENERATED_DIR / "A3-Tree-Locations.gpkg"

MAP_PARKS_ALL = GENERATED_DIR / "Parks-Forests-All.gpkg"
MAP_PARKS_SELECTED = GENERATED_DIR / "Parks-Forests-SELECTED.gpkg"

GRAPH_WALKING = GENERATED_DIR / "Graph-Walking.graphml"


# Make directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)
# SPATIAL_DATA.mkdir(parents=True, exist_ok=True)
# STREET_NETWORKS.mkdir(parents=True, exist_ok=True)
# POINT_GRIDS.mkdir(parents=True, exist_ok=True)
# PANO_DIR.mkdir(parents=True, exist_ok=True)
# GVI_DIR.mkdir(parents=True, exist_ok=True)


def format_folder_name(area_number):
    return f"community_area_{area_number}"
