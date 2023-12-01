#!/usr/bin/env python
from functools import partial

import geopandas as gp
import pandas as pd
from pyogrio import read_dataframe, write_dataframe
from shapely import set_precision, unary_union

pd.set_option("display.max_columns", None)

TENFOOT = 25.4 * 12.0 * 10.0 / 1000.0
CRS = "EPSG:2272"
OUTPATH = "neighbour-data.gpkg"

set_precision_pointone = partial(set_precision, grid_size=0.1)

try:
    land = read_dataframe(OUTPATH, layer="land")
except:
    land = gp.read_file("https://opendata.arcgis.com/datasets/19c35fb02d544a9bad0032b58268c9f9_0.geojson")
    write_dataframe(land, OUTPATH, layer="land")

simple_land = land.to_crs(CRS).explode(index_parts=False).reset_index(drop=True)
simple_land["geometry"] = simple_land["geometry"].map(set_precision_pointone)
ix = simple_land["geometry"].is_empty
simple_land = simple_land[~ix]
simple_land = simple_land.reset_index(drop=True)
write_dataframe(simple_land, OUTPATH, layer="simple_land")

buffer_land = land.to_crs(CRS).buffer(TENFOOT).map(set_precision_pointone)
buffer_land = gp.GeoSeries(unary_union(buffer_land.values), crs=CRS)
buffer_land = buffer_land.explode(index_parts=True).reset_index(level=0, drop=True)
buffer_land = buffer_land.to_frame("geometry").reset_index(drop=True)
write_dataframe(buffer_land, OUTPATH, layer="buffer_land")

count_land = simple_land.sjoin(buffer_land).sort_index()
count_land = count_land.rename(columns={"index_right": "lot_id"})
count_land = count_land.set_index("lot_id")
count = count_land["OBJECTID"].groupby("lot_id").count()
count = count.rename("count")
count_land = count_land.join(count).reset_index()
count_land["class"] = (count_land["count"] // 5) * 5
write_dataframe(count_land, OUTPATH, layer="count_land")
