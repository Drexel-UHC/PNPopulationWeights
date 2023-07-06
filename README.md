This documents the population and household weights for the Promise Neighborhood. We use these weights to calculate
estimates from census tract data for the whole Promise Neighborhood.

## Types of Weights
We have created population based weights for all people within the Promise Neighborhood and for children between the
ages of 0 and 17 for both 2010 and 2020 census tracts. Additionally, we created weights for all households within the
Promise Neighborhood and households with at least child under the age of 18 for 2010 census tracts.

The 2020 household weights will be calculated when the census releases the 2020 files related to households at
households with children at the census block level.

## Weight Purpose
The weights are required because the Promise Neighborhood footprint does not align with census tract boundaries.
The weights correct for the percentage of the population or households of each census tract that fall outside the
Promise Neighborhood boundaries. They are only valid for creating a combined single estimate for the whole Promise
Neighborhood.

## Methodology
The weights are created using Decennial Census Data (2010 and 2020). We summed the populations or households of all
census blocks that are inside the Promise Neighborhood for each tract and divived by the total population or household
of the tract, creating a weight that accounts for the population distribution within the tract. In the case that a
census block was only partially within the Promise Neighborhood, we considered it a part of the Promise Neighborhood if
it was at least half in the Promise Neighborhood.

## Usage

### Numerical Estimates

Take the numerical estimate of each tract and multiply it by the weight of that tract. Then sum the resulting product
for each tract.  

### Percentages and Rates
Multiply the numerator and denominator for each estimate by the corresponding tract weight. Sum the numerators and
denominators then divide.

### Household vs Population Weights
Population weights should be used when you are attempting to get an estimate for the something measured at the
individual level such as employment. If you are most interested in children, use the population weights for the 0-17 age
group instead of the total population.

Household weights should be used when you are attempting to get an estimate for something at that is measured by
households or family units, such as household income.


### Files

| File Name            | Description                                                                           |
|----------------------|---------------------------------------------------------------------------------------|
| PZ Weights 2010.csv  | Weights for the 2010 census tracts, used for data collected<br/>between 2010 and 2019 |
| PZ Weights 2020.csv  | Weights for the 2020 census tracts, used for data collected<br/>between 2020 and 2029 |

| Column Name                             | Description                                     |
|------------------------------------------|-------------------------------------------------|
| State                                    | 2-Digit State FIPS Code                         |
| County                                   | 3-Digit County FIPS Code                        |
| Tract                                    | 6-Digit Census Tract Code                       |
| Population Weight                        | Weight for the total population                 |
| Population weight_0-17 pop               | Weight for the 0-17 population                  |
| Household Weight                         | Weight for all households                       |
| Household weight_With children under 18  | Weight for all households with a child under 18 |


