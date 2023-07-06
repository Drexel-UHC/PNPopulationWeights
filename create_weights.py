import geopandas as gpd
import pandas as pd


def get_blocks_in_pn(census_shp, pn_shp):
    """
    Get the intersection of PN area and census shapefile

    :param census_shp: Shapefile containing census block boundaries for Philadelphia
    :param pn_shp:
    :return:
    """

    cb20 = gpd.read_file(census_shp)
    pn = gpd.read_file(pn_shp).to_crs("EPSG:4269")

    # convert area to a proper geometry
    cb20["total_area"] = cb20.to_crs("EPSG:3857").geometry.area

    # get the intersection of the shapefiles
    blocks_in_pn = cb20.overlay(pn, how="intersection")
    blocks_in_pn["area_in_pn"] = blocks_in_pn.to_crs("EPSG:3857").geometry.area

    # only include blocks that are in the PN by at least 50% by area
    blocks_in_pn = blocks_in_pn[blocks_in_pn["area_in_pn"]/blocks_in_pn["total_area"] >= .5]

    return blocks_in_pn

def get_population_data(census_url, variables, column_rename):
    """
    Pull population data from census

    :param census_url: census dataset to get information from
    :param variables: variables to pull from the dataset
    :param column_rename: columns to rename must contain Over18 and Total
    :return:
    """

    var_names = ",".join(variables)

    # pull data
    redistricting = pd.read_json(f"{census_url}?get={var_names}&for=block:*&in=state:42+county:101")
    redistricting = pd.DataFrame(redistricting.iloc[1:,].values, columns=redistricting.iloc[0].tolist())\
        .rename(columns=column_rename)

    redistricting["Total"] = redistricting["Total"].astype(int)
    redistricting["Over18"] = redistricting["Over18"].astype(int)

    # contains households this is currently not used, placeholder for final data
    redistricting["OccupiedHouseholds"] = redistricting["OccupiedHouseholds"].astype(int)
    redistricting["TotalHouseholds"] = redistricting["TotalHouseholds"].astype(int)

    # get population under 18
    redistricting["Under18"] = redistricting["Total"] - redistricting["Over18"]

    return redistricting

def calc_pop_weights(population_data, pn_census_blocks, under18, total_pop):
    """

    :param population_data: population data from census
    :param pn_census_blocks: blocks in the Promise Neighborhood
    :param under18: Column containing data about population under 18
    :param total_pop: column contain data about total population
    :return:
    """
    pn_cb = pn_census_blocks.copy()

    # get Tract codes and recreate GEOIDs for merging
    pn_blocks = population_data.loc[population_data["tract"].isin(pn_cb["TRACTCE20"].astype(str).str.zfill(6))].copy()
    pn_blocks["ID"] = pn_blocks["state"].astype(str).str.cat(
        [pn_blocks["county"].astype(str), pn_blocks["tract"].astype(str).str.zfill(6),
         pn_blocks["block"].astype(str).str.zfill(4)])
    pn_cb["ID"] = pn_cb["STATEFP20"].astype(str).str.cat(
        [pn_cb["COUNTYFP20"].astype(str), pn_cb["TRACTCE20"].astype(str).str.zfill(6),
         pn_cb["BLOCKCE20"].astype(str).str.zfill(4)])

    # Get PN census blocks
    pn_blocks["inPN"] = 0
    pn_blocks.loc[pn_blocks["ID"].isin(pn_cb["ID"]), "inPN"] = 1

    # get population totals by tract
    pop_weights = pd.concat([pn_blocks.groupby("tract")[total_pop].sum().rename("in_tract"),
                             pn_blocks.loc[pn_blocks["inPN"] == 1,].groupby("tract")[total_pop].sum().rename("inPN"),
                             pn_blocks.groupby("tract")[under18].sum(),
                             pn_blocks.loc[pn_blocks["inPN"] == 1,].groupby("tract")[under18].sum().rename(
                                 "Under18_inPN")], axis=1)

    # calculate weights
    pop_weights["Total Population Weight"] = pop_weights["inPN"] / pop_weights["in_tract"]
    pop_weights["Total Population 0-17 Weight"] = pop_weights["Under18_inPN"] / pop_weights["Under18"]

    pop_weights["State"] = "42"
    pop_weights["County"] = "101"

    pop_weights.reset_index(inplace=True)

    return pop_weights[["State", "County", "tract", "Total Population Weight", "Total Population 0-17 Weight"]]