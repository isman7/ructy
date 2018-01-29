import json
import os
import sys

from bokeh.io import output_file, show
from bokeh.models import (
  GMapPlot, GMapOptions, ColumnDataSource, Circle, Range1d, PanTool, WheelZoomTool, BoxSelectTool
)

map_options = GMapOptions(lat=30.29, lng=-97.73, map_type="roadmap", zoom=11)
plot = GMapPlot(x_range=Range1d(), y_range=Range1d(), map_options=map_options)

data = []


for ii in range(85):
    try:
        with open("../db/{}.json".format(ii)) as data_file:
            data.append(json.loads(data_file.read()))
    except:
        print(ii)

# For GMaps to function, Google requires you obtain and enable an API key:
#
#     https://developers.google.com/maps/documentation/javascript/get-api-key
#
# Replace the value below with your personal API key:
plot.api_key = sys.argv[1]

source = ColumnDataSource(
    data=dict(
        lat=[30.29, 30.20, 30.29],
        lon=[-97.70, -97.74, -97.78],
    )
)

circle = Circle(x="lon", y="lat", size=15, fill_color="blue", fill_alpha=0.8, line_color=None)
plot.add_glyph(source, circle)

plot.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool())
output_file("gmap_plot.html")
show(plot)