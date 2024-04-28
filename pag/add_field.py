# add_field.py
import utils
import os
import folium
import pandas as pd
import streamlit as st
import geopandas as gpd
from folium.plugins import Draw
from shapely.geometry import Polygon
from streamlit_folium import st_folium
from authentication import greeting, check_password
import geopy
from pyproj import  Transformer
from shapely.ops import transform
from geopy.geocoders import Nominatim
from shapely.ops import transform
from geopy.geocoders import Nominatim

def check_authentication():
    if not check_password():
        st.stop()



# Function to get coordinates from a location name
def get_location_coordinates(location_name,geolocator):
    try:
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except:
        return None, None

def display_existing_fields(current_user):
    with st.expander("Existing Fields", expanded=False):
        if os.path.exists(f"fields_{current_user}.parquet"):
            gdf = gpd.read_parquet(f"fields_{current_user}.parquet")
            st.table(gdf.name.tolist())
            mm = gdf.explore()
            st_folium(mm)
        else:
            st.info("No Fields Added Yet!")

def add_existing_fields_to_map(field_map, current_user):
    if os.path.exists(f"fields_{current_user}.parquet"):
        fg = folium.FeatureGroup(name="Existing Fields", control=True).add_to(field_map)
        gdf = gpd.read_parquet(f"fields_{current_user}.parquet")
        for i, row in gdf.iterrows():
            edges = row['geometry'].exterior.coords.xy
            edges = [[i[1], i[0]] for i in zip(*edges)]
            folium.Polygon(edges, color='blue', fill=True, fill_color='blue', fill_opacity=0.6).add_to(fg)
    return field_map

def get_center_of_existing_fields(current_user):
    location_name = st.text_input('Enter a location to search:')
    if location_name:
        geolocator = Nominatim(user_agent=current_user)
        geopy.geocoders.options.default_user_agent = current_user

        lat, lon = get_location_coordinates(location_name,geolocator)
        if lat is not None and lon is not None:
            return [lat, lon]
        else:
            st.error('Location not found. Please try again.')
    if os.path.exists(f"fields_{current_user}.parquet"):
        gdf = gpd.read_parquet(f"fields_{current_user}.parquet")
        edges = gdf['geometry'][0].exterior.coords.xy
        edges = [[i[1], i[0]] for i in zip(*edges)]
        edges_center = [sum([i[0] for i in edges]) / len(edges), sum([i[1] for i in edges]) / len(edges)]

        return edges_center
    return [15.572363674301132, 32.69167103104079]

def display_map_and_drawing_controls(field_map, center_start):
    zoom_start = 13
    if st.session_state['active_drawing'] is None:
        st.info("IMPORTANT: Click on the drawing to confirm the drawn field", icon="🚨")
        sat_basemap = utils.basemaps['Google Satellite Hybrid']  # Change this line to use 'Google Satellite Hybrid'
        sat_basemap.add_to(field_map)
        folium.plugins.Geocoder().add_to(field_map)
        folium.LayerControl().add_to(field_map)
        output = st_folium(field_map, center=center_start, zoom=zoom_start, key="new", width=900)
        active_drawing = output['last_active_drawing']
        st.session_state['active_drawing'] = active_drawing
        return False
    else:
        st.info("Drawing Captured! Click on the button below to Clear Drawing and Draw Again")
        active_drawing = st.session_state['active_drawing']
        new_map = folium.Map(location=center_start, zoom_start=8)
        edges = [[i[1], i[0]] for i in active_drawing['geometry']['coordinates'][0]]
        edges_center = [sum([i[0] for i in edges]) / len(edges), sum([i[1] for i in edges]) / len(edges)]
        folium.Polygon(edges, color='green', fill=True, fill_color='green', fill_opacity=0.6, name="New Field").add_to(new_map)
        sat_basemap = utils.basemaps['Google Satellite']
        sat_basemap.add_to(new_map)
        folium.LayerControl().add_to(new_map)
        st_folium(new_map, center=edges_center, zoom=zoom_start, key="drawn", width=900)
        return True

def handle_user_actions(active_drawing, current_user, intersects, within_area):
    draw_again_col, add_field_info_col = st.columns([1, 1])
    with draw_again_col:
        draw_again = st.button("Draw Again", key="draw_again", help="Click to Clear Drawing and Draw Again",
                               type="primary", use_container_width=True, disabled=st.session_state['active_drawing'] is None)
        if draw_again:
            st.session_state['active_drawing'] = None
            st.rerun()
    with add_field_info_col:
        if st.session_state['active_drawing'] is None:
            st.info("Drawing not captured yet!")
        else:
            field_name = st.text_input("Field Name*", help="Enter a distinct name for the field", key="field_name")
            if field_name == "":
                st.warning("Field Name cannot be empty!")
            if os.path.exists(f"fields_{current_user}.parquet"):
                gdf = gpd.read_parquet(f"fields_{current_user}.parquet")
                if field_name in gdf['name'].tolist():
                    st.warning("Field Name already exists. Please enter a different name!")
            submit = st.button("Submit", key="submit", help="Click to Submit Field Information", type="primary",
                               use_container_width=True,disabled=(st.session_state['active_drawing'] is None or field_name == "") or intersects or not within_area)
            if submit:
                save_field_information(active_drawing, field_name, current_user)
                st.success("Field Information Submitted Successfully!")
                st.session_state['active_drawing'] = None
                st.rerun()

def save_field_information(active_drawing, field_name, current_user):
    edges = [[i[0], i[1]] for i in active_drawing['geometry']['coordinates'][0]]
    geom = Polygon(edges)
    field_dict = {
        "name": field_name,
        "geometry": geom
    }
    gdf = gpd.GeoDataFrame([field_dict], geometry='geometry')
    gdf.crs = "EPSG:4326"
    if os.path.exists(f"fields_{current_user}.parquet"):
        old_gdf = gpd.read_parquet(f"fields_{current_user}.parquet")
        gdf = gpd.GeoDataFrame(pd.concat([old_gdf, gdf], ignore_index=True), crs="EPSG:4326")
    gdf.to_parquet(f"fields_{current_user}.parquet")

def initialize_active_drawing_state():
    if 'active_drawing' not in st.session_state:
        st.session_state['active_drawing'] = None
    if 'current_user' not in st.session_state:
        st.session_state['current_user'] = None
    


def check_intersection_with_existing_fields(active_drawing, current_user):
    if active_drawing is None:
        return False
    if os.path.exists(f"fields_{current_user}.parquet"):
        gdf = gpd.read_parquet(f"fields_{current_user}.parquet")
        edges = [[i[0], i[1]] for i in active_drawing['geometry']['coordinates'][0]]
        geom = Polygon(edges)
        geom = gpd.GeoSeries([geom]*len(gdf), crs="EPSG:4326")
        geom1 = geom.to_crs(gdf.crs)
        geom2 = gdf.geometry.to_crs(gdf.crs)
        if geom1.overlaps(geom2).any():
            st.warning("Field intersects with existing fields. Please draw again!")
            with st.expander("Intersecting Fields", expanded=False):
                field_map = geom1.explore(name= "New Field", color="red")
                field_map = gdf.explore(m=field_map, name="Existing Fields", color="blue")
                st_folium(field_map)
            return True
    return False



def check_polygon_area_within_range(active_drawing, min_area_km2=1, max_area_km2=10):
    if active_drawing is None:
        return
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)

    edges = [[i[0], i[1]] for i in active_drawing['geometry']['coordinates'][0]]
    geom = Polygon(edges)
    transformed_geom = transform(transformer.transform, geom)


    area_km2 = transformed_geom.area / 10**6

    if area_km2 < min_area_km2:
        st.warning(f"Field area {area_km2 :.2f} is less than {min_area_km2} km². Please draw again!")
        return False
    if area_km2 > max_area_km2:
        st.warning(f"Field area {area_km2 :.2f} is more than {max_area_km2} km². Please draw again!")
        return False
    st.success(f"Field area is {area_km2 :.2f} km², now give it a unique name {st.session_state['current_user']}!")
    return True


def add_drawing():
    initialize_active_drawing_state()
    current_user = greeting("Drag and Zoom and draw your fields on the map, make sure to name them uniquely")
    current_user = st.session_state['current_user']
    display_existing_fields(current_user)
    center_start = get_center_of_existing_fields(current_user)
    zoom_start = 13
    field_map = folium.Map(location=center_start, zoom_start=zoom_start)


    draw_options = {'polyline': False, 'polygon': True, 'rectangle': True, 'circle': False, 'marker': False, 'circlemarker': False}
    Draw(export=True, draw_options=draw_options).add_to(field_map)
    field_map = add_existing_fields_to_map(field_map, current_user)



    captured = display_map_and_drawing_controls(field_map, center_start)
    if captured:
        intersects = check_intersection_with_existing_fields(st.session_state['active_drawing'], current_user)
        within_area = check_polygon_area_within_range(st.session_state['active_drawing'])
        handle_user_actions(st.session_state['active_drawing'], current_user, intersects, within_area)
    

if __name__ == '__main__':
    check_authentication()

    add_drawing()