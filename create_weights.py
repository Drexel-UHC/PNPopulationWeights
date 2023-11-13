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

def get_household_data(census_url, variables, column_rename):
    var_names = ",".join(variables)

    # print(f"{census_url}?get={var_names}&for=block:*&in=state:42+county:101")
    dhc = pd.read_json(f"{census_url}?get={var_names}&for=block:*&in=state:42+county:101")
    dhc = pd.DataFrame(dhc.iloc[1:, ].values, columns=dhc.iloc[0].tolist()).rename(columns=column_rename)
    # print(dhc)
    dhc[["Total", "P20_003N", "P20_006N", "P20_011N", "P20_017N"]] = dhc[["Total", "P20_003N", "P20_006N", "P20_011N", "P20_017N"]].apply(pd.to_numeric)
    # COLUMNS TO SUM
    dhc["Under18"] = dhc[["P20_003N", "P20_006N", "P20_011N", "P20_017N"]].sum(axis=1)

    dhc.drop(["P20_003N", "P20_006N", "P20_011N", "P20_017N"], axis=1, inplace=True)

    return dhc

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

def calc_household_weights(household_data, pn_census_blocks, under18, total_households):
    pn_cb = pn_census_blocks.copy()

    # get Tract codes and recreate GEOIDs for merging
    pn_blocks = household_data.loc[household_data["tract"].isin(pn_cb["TRACTCE20"].astype(str).str.zfill(6))].copy()
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
    household_weights = pd.concat([pn_blocks.groupby("tract")[total_households].sum().rename("in_tract"),
                                   pn_blocks.loc[pn_blocks["inPN"] == 1,].groupby("tract")[total_households].sum().rename("inPN"),
                                   pn_blocks.groupby("tract")[under18].sum(),
                                   pn_blocks.loc[pn_blocks["inPN"] == 1,].groupby("tract")[under18].sum().rename(
                                       "Under18_inPN")], axis=1)
    # calculate weights
    household_weights["Household Weight"] = household_weights["inPN"] / household_weights["in_tract"]
    household_weights["Household weight_With children under 18"] = household_weights["Under18_inPN"] / household_weights["Under18"]

    household_weights["State"] = "42"
    household_weights["County"] = "101"

    household_weights.reset_index(inplace=True)

    return household_weights

if __name__ == "__main__":
    pn_blocks = get_blocks_in_pn(r"D:\Public Data\Census Shapefiles\census_blocks 2020\tl_2021_42_tabblock20.shp",
                                 r"S:\Promise Zone Addresses\Geodatabases\PromiseZone2.gdb").to_crs("EPSG:4269")

    # household_data = get_household_data("https://api.census.gov/data/2020/dec/dhc",
    #                                     variables=["GEO_ID", "P20_001N", "P20_003N", "P20_006N", "P20_011N", "P20_017N"],
    #                                     column_rename={"P20_001N": "Total", "GEO_ID": "GEOID20"})

    pop_data = get_population_data("https://api.census.gov/data/2020/dec/pl",
                                   variables=["GEO_ID", "P1_001N", "P3_001N", "H1_001N", "H1_002N"],
                                   column_rename={"P1_001N": "Total", "P3_001N": "Over18", "H1_001N": "TotalHouseholds",
                                                  "H1_002N": "OccupiedHouseholds", "GEO_ID": "GEOID20"})
    calc_pop_weights(pop_data, pn_blocks, "Under18", "Total")
    # calc_household_weights(household_data, pn_blocks, "Under18", "Total")