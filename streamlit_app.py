import datetime
import os
import pathlib
import requests
import zipfile
import pandas as pd
import pydeck as pdk
import geopandas as gpd
import streamlit as st
import leafmap.colormaps as cm
from leafmap.common import hex_to_rgb

st.set_page_config(layout="wide")

STREAMLIT_STATIC_PATH = pathlib.Path(st.__path__[0]) / "static"
# We create a downloads directory within the streamlit static asset directory
# and we write output files to it
DOWNLOADS_PATH = STREAMLIT_STATIC_PATH / "downloads"
if not DOWNLOADS_PATH.is_dir():
    DOWNLOADS_PATH.mkdir()

link_prefix = "/Users/macos/Desktop/streamlit-app/data/incheon_electricity_usage/"

data_links = {
    "dong": link_prefix + "dataset.gpkg",
    "hex": link_prefix + "dataset_hex.gpkg",
    }

def get_data_columns(df):
    del_cols = ['fid', 'NAME_3', 'x', 'y', 'y ', 'gu_name', 'dong_name', 'fid', 'hex_id', 'area', 'geometry']
    cols = df.columns.values.tolist()
    for col in cols:
        if col.strip() in del_cols:
            cols.remove(col)
    return cols

@st.cache
def get_geom_data(path):
    gdf = gpd.read_file(path)
    return gdf

def select_non_null(gdf, col_name):
    new_gdf = gdf[~gdf[col_name].isna()]
    return new_gdf

def select_null(gdf, col_name):
    new_gdf = gdf[gdf[col_name].isna()]
    return new_gdf

def app():

    st.title("Incheon Residential Electricity Usage")
    st.markdown(
        """**Introduction:** This interactive dashboard is designed for visualizing Incheon's household electricity usage and experimentation with SHAP-to-text interpretation.
    """
    )

    row1_col1, row1_col4, row1_col5 = st.columns(
        [0.6, 1.4, 2]
    )

    with row1_col1:
        frequency = st.selectbox("Data visualization", ["동", "Hex"])
    
    if frequency == "동":
        gdf = get_geom_data(data_links["dong"])
        
    if frequency == "Hex":
        gdf = get_geom_data(data_links["hex"])
    
    data_cols = get_data_columns(gdf)

    with row1_col4:
        selected_col = st.selectbox("Attribute", data_cols)
    
    row2_col1, row2_col2, row2_col3, row2_col4, row2_col5, row2_col6 = st.columns(
        [0.6, 0.68, 0.7, 0.7, 1.5, 0.8]
    )

    palettes = cm.list_colormaps()
    with row2_col1:
        palette = st.selectbox("Color palette", palettes, index=palettes.index("Blues"))
    with row2_col2:
        n_colors = st.slider("Number of colors", min_value=2, max_value=20, value=8)
    with row2_col3:
        show_3d = st.checkbox("Show 3D view", value=False)
    with row2_col5:
        if show_3d:
            elev_scale = st.slider(
                "Elevation scale", min_value=1, max_value=100, value=1, step=1
            )
            with row2_col6:
                st.info("Press Ctrl and move the left mouse button.")
        else:
            elev_scale = 1

    gdf_null = select_null(gdf, selected_col)
    gdf = select_non_null(gdf, selected_col)
    gdf = gdf.sort_values(by=selected_col, ascending=True)

    colors = cm.get_palette(palette, n_colors)
    colors = [hex_to_rgb(c) for c in colors]

    for i, ind in enumerate(gdf.index):
        index = int(i / (len(gdf) / len(colors)))
        if index >= len(colors):
            index = len(colors) - 1
        gdf.loc[ind, "R"] = colors[index][0]
        gdf.loc[ind, "G"] = colors[index][1]
        gdf.loc[ind, "B"] = colors[index][2]

    gdf_disolved = gdf.dissolve().centroid
    gdf_x = gdf_disolved.x.values[0]
    gdf_y = gdf_disolved.y.values[0]

    # print(f'COORDS: {gdf_x, gdf_y}')

    initial_view_state = pdk.ViewState(
        latitude=gdf_y,
        longitude=gdf_x,
        zoom=10,
        max_zoom=16,
        pitch=0,
        bearing=0,
        height=800,
        width=None,
    )

    min_value = gdf[selected_col].min()
    max_value = gdf[selected_col].max()
    color = "color"
    
    # color_exp = f"[({selected_col}-{min_value})/({max_value}-{min_value})*255, 0, 0]"
    color_exp = f"[R, G, B]"

    geojson = pdk.Layer(
        "GeoJsonLayer",
        gdf,
        pickable=True,
        opacity=0.5,
        stroked=True,
        filled=True,
        extruded=show_3d,
        wireframe=True,
        get_elevation=f"{selected_col}",
        elevation_scale=elev_scale,
        # get_fill_color="color",
        get_fill_color=color_exp,
        get_line_color=[0, 0, 0],
        get_line_width=2,
        line_width_min_pixels=1,
    )

    geojson_null = pdk.Layer(
        "GeoJsonLayer",
        gdf_null,
        pickable=True,
        opacity=0.2,
        stroked=True,
        filled=True,
        extruded=False,
        wireframe=True,
        # get_elevation="properties.ALAND/100000",
        # get_fill_color="color",
        get_fill_color=[200, 200, 200],
        get_line_color=[0, 0, 0],
        get_line_width=2,
        line_width_min_pixels=1,
    )

    # tooltip = {"text": "Name: {NAME}"}

    tooltip = {
        "html": "<b>Name:</b> "+selected_col+"<br><b>Value:</b> {"+selected_col+"}<br>",
        "style": {"backgroundColor": "steelblue", "color": "white"},
    }

    layers = [geojson]

    r = pdk.Deck(
        layers=layers,
        initial_view_state=initial_view_state,
        map_style="light",
        tooltip=tooltip,
    )

    row3_col1, row3_col2 = st.columns([6, 1])

    with row3_col1:
        st.pydeck_chart(r)
    
    with row3_col2:
        st.write(
            cm.create_colormap(
                palette,
                label=selected_col.replace("_", " ").title(),
                width=0.2,
                height=3,
                orientation="vertical",
                vmin=min_value,
                vmax=max_value,
                font_size=9,
            )
        )
    row4_col1, row4_col2, row4_col3 = st.columns([1, 2, 3])
    with row4_col3:
        show_colormaps = st.checkbox("Preview all color palettes")
        if show_colormaps:
            st.write(cm.plot_colormaps(return_fig=True))

app()
