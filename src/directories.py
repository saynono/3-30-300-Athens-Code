from pathlib import Path


# Define directories
REPO_ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT_DIR / "data"
SPATIAL_DATA = DATA_DIR / "spatial_data"
STREET_NETWORKS = SPATIAL_DATA / "street_networks"
POINT_GRIDS = SPATIAL_DATA / "point_grids"
PANO_DIR = SPATIAL_DATA / "pano_data"
GVI_DIR = SPATIAL_DATA / "greenview_index"


# Make directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
SPATIAL_DATA.mkdir(parents=True, exist_ok=True)
STREET_NETWORKS.mkdir(parents=True, exist_ok=True)
POINT_GRIDS.mkdir(parents=True, exist_ok=True)
PANO_DIR.mkdir(parents=True, exist_ok=True)
GVI_DIR.mkdir(parents=True, exist_ok=True)


def format_folder_name(area_number):
    return f"community_area_{area_number}"
