import directories
import Parameters_3_30_300 as P
import geopandas as gpd
import os.path


def main():
    root = directories.DATA_DIR
    print("ROOT: ", root)

    if os.path.exists(directories.MAP_BUILDINGS_GENERATED):
        print("Loading existing building data...")
        buildings_gdf = gpd.read_file(directories.MAP_BUILDINGS_GENERATED)
    else:
        print(f"Couldn't Find Buildings File: {directories.MAP_BUILDINGS_GENERATED}")
        exit(1)
    if 'tree_count' not in buildings_gdf.columns:
        print("Adding trees_in_proximity column")
        buildings_gdf['tree_count'] = int(0)


    if os.path.exists(directories.MAP_A3_TREE_LOCATIONS):
        print("Loading Tree Location data...")
        trees_gdf = gpd.read_file(directories.MAP_A3_TREE_LOCATIONS)
    else:
        print(f"Couldn't Tree Location File: {directories.MAP_A3_TREE_LOCATIONS}")
        exit(1)

    buildings_gdf = buildings_gdf.to_crs(epsg=32633)
    trees_gdf = trees_gdf.to_crs(epsg=32633)

    buildings_gdf["buffer_meters"] = buildings_gdf.geometry.buffer(P.TREE_DISTANCE_TO_WINDOW_MAX)

    # Spatial join: attach each tree to the building (via the buffer) it falls within.
    join_gdf = gpd.sjoin(
        trees_gdf,
        buildings_gdf.set_geometry("buffer_meters"),
        how="left",
        predicate="within"
    )

    tree_counts = join_gdf.groupby("index_right").size()
    # Add a new column 'tree_count' to buildings; fill missing counts with 0.
    buildings_gdf["tree_count"] = buildings_gdf.index.map(tree_counts).fillna(0).astype(int)

    # Optionally, drop the buffer column if it's no longer needed.
    buildings_gdf = buildings_gdf.drop(columns=["buffer_meters"])
    buildings_gdf.to_file(directories.MAP_A3_GENERATED, driver="GPKG")
    print(f"Saved new building data to file {directories.MAP_A3_GENERATED}")

    # Calculate the mean tree count
    mean_tree_count = buildings_gdf["tree_count"].mean()
    print("Mean tree count:", mean_tree_count)

    # Calculate the percentage of buildings with 3 or more trees
    total_buildings = len(buildings_gdf)
    buildings_with_3_or_more = (buildings_gdf["tree_count"] >= 3).sum()
    percentage_3_or_more = (buildings_with_3_or_more / total_buildings) * 100

    print(f"Percentage of buildings with 3 or more trees: {percentage_3_or_more:.2f}%")


    print("Done!")


if __name__ == "__main__":
    main()
