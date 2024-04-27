import os
import utils
import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium, folium_static
from authentication import greeting, check_password
import folium
from senHub import SenHub
from datetime import datetime
from sentinelhub import  SHConfig, MimeType
import requests
import process
import joblib
from zipfile import ZipFile
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pydeck as pdk
import pandas as pd
import plotly.express as px

def check_authentication():
    if not check_password():
        st.stop()



config = SHConfig()
config.instance_id       = '6c220beb-90c4-4131-b658-10cddd8d97b9'
config.sh_client_id      = '17e7c154-7f2d-4139-b1af-cef762385079'
config.sh_client_secret  = 'KvbQMKZB85ZWEgWuxqiWIVEvTAQEfoF9'


def select_field(gdf):
    st.markdown("""
            <style>
            .stSelectbox > div > div {cursor: pointer;}
            </style>
            """, unsafe_allow_html=True)
    names = gdf['name'].tolist()
    names.append("Select Field")
    field_name = st.selectbox("Select Field", options=names, key="field_name_monitor", help="Select the field to edit", index=len(names)-1)
    return field_name


def calculate_bbox(df, field):
    bbox = df.loc[df['name'] == field].bounds
    r = bbox.iloc[0]
    return [r.minx, r.miny, r.maxx, r.maxy]

def get_available_dates_for_field(df, field, year, start_date='', end_date=''):
    bbox = calculate_bbox(df, field)
    token = SenHub(config).token
    headers = utils.get_bearer_token_headers(token)
    if start_date == '' or end_date == '':
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
    data = f'{{ "collections": [ "sentinel-2-l2a" ], "datetime": "{start_date}T00:00:00Z/{end_date}T23:59:59Z", "bbox": {bbox}, "limit": 100, "distinct": "date" }}'
    response = requests.post('https://services.sentinel-hub.com/api/v1/catalog/search', headers=headers, data=data)
    try:
        features = response.json()['features']
    except:
        print(response.json())
        features = []
    return features

@st.cache_data
def get_and_cache_available_dates(_df, field, year, start_date, end_date):
    dates = get_available_dates_for_field(_df, field, year, start_date, end_date)
    print(f'Caching Dates for {field}')
    return dates




def get_cuarted_df_for_field(df, field, date, metric, clientName):
    curated_date_path =  utils.get_curated_location_img_path(clientName, metric, date, field)
    if curated_date_path is not None:
        curated_df = gpd.read_file(curated_date_path)
    else:
        process.Download_image_in_given_date(clientName, metric, df, field, date)
        process.mask_downladed_image(clientName, metric, df, field, date)
        process.convert_maske_image_to_geodataframe(clientName, metric, df, field, date, df.crs)
        curated_date_path =  utils.get_curated_location_img_path(clientName, metric, date, field)
        curated_df = gpd.read_file(curated_date_path)
    return curated_df


def track(metric, field_name, src_df, client_name):

    dates = []
    date = -1
    if 'dates' not in st.session_state:
        st.session_state['dates'] = dates
    else:
        dates = st.session_state['dates']
    if 'date' not in st.session_state:
        st.session_state['date'] = date
    else:
        date = st.session_state['date']

    if True:
        start_date = '2024-01-01'
        today = datetime.today()
        end_date = today.strftime('%Y-%m-%d')
        year = '2024'

        dates = get_and_cache_available_dates(src_df, field_name, year, start_date, end_date)
        # Add None to the end of the list to be used as a default value
        #sort the dates from earliest to today
        dates = sorted(dates)

        #Add the dates to the session state
        st.session_state['dates'] = dates

    # Display the dropdown menu
    if len(dates) > 0:
        st.markdown("""
            <style>
            .stSelectbox > div > div {cursor: pointer;}
            </style>
            """, unsafe_allow_html=True)
        date = st.selectbox('Select Observation Date: ', dates, index=len(dates)-1, key=f'Select Date Dropdown Menu - {metric}')
        if date != -1:
            st.write('You selected:', date)
            #Add the date to the session state
            st.session_state['date'] = date
        else:
            st.write('Please Select A Date')
    else:
        st.info('No dates available for the selected field and dates range, select a different range or click the button to fetch the dates again')


    st.markdown('---')
    st.header('Show Field Data')

    # If a field and a date are selected, display the field data
    if date != -1:   

        # Get the field data at the selected date
        with st.spinner('Loading Field Data...'):
            # Get the metric data and cloud cover data for the selected field and date
            metric_data = get_cuarted_df_for_field(src_df, field_name, date, metric, client_name)
            cloud_cover_data = get_cuarted_df_for_field(src_df, field_name, date, 'CLP', client_name)
            
            #Merge the metric and cloud cover data on the geometry column
            field_data = metric_data.merge(cloud_cover_data, on='geometry')

        # Display the field data
        st.write(f'Field Data for {field_name} (Field ID: {field_name}) on {date}')
        st.write(field_data.head(2))

        #Get Avarage Cloud Cover
        avg_clp = field_data[f'CLP_{date}'].mean() *100

        # If the avarage cloud cover is greater than 80%, display a warning message
        if avg_clp > 80:
            st.warning(f'⚠️ The Avarage Cloud Cover is {avg_clp}%')
            st.info('Please Select A Different Date')

        ## Generate the field data Map ##

        #Title, Colormap and Legend
        title = f'{metric} for selected field {field_name} (Field ID: {field_name}) in {date}'
        cmap = 'RdYlGn'

        # Create a map of the field data
        # field_data_map  = field_data.explore(
        #     column=f'{metric}_{date}',
        #     cmap=cmap,
        #     legend=True,
        #     vmin=0,
        #     vmax=1,
        #     marker_type='circle', marker_kwds={'radius':5.3, 'fill':True})
        
        # Add Google Satellite as a base map
        # google_map = utils.basemaps['Google Satellite']
        # google_map.add_to(field_data_map)

        # # Display the map
        # st_folium(field_data_map, width = 725, key=f'Field Data Map - {metric}')
        df = field_data.copy()
        df['latitude'] = df['geometry'].y
        df['longitude'] = df['geometry'].x

        # Create a scatter plot
        fig = px.scatter_mapbox(
            df, 
            lat='latitude', 
            lon='longitude', 
            color=f'{metric}_{date}',
            color_continuous_scale='RdYlGn',
            range_color=(0, 1),
            size_max=15,
            zoom=13,
        )

        # Add the base map
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig)

        #Dwonload Links

        # If the field data is not empty, display the download links
        if len(field_data) > 0:
            # Create two columns for the download links
            download_as_shp_col, download_as_tiff_col = st.columns(2)

            # Create a shapefile of the field data and add a download link
            with download_as_shp_col:

                #Set the shapefile name and path based on the field id, metric and date
                extension = 'shp'
                shapefilename = f"{field_name}_{metric}_{date}.{extension}"
                path = f'./shapefiles/{field_name}/{metric}/{extension}'

                # Create the target directory if it doesn't exist
                os.makedirs(path, exist_ok=True)
                
                # Save the field data as a shapefile
                field_data.to_file(f'{path}/{shapefilename}')

                # Create a zip file of the shapefile
                files = []
                for i in os.listdir(path):
                    if os.path.isfile(os.path.join(path,i)):
                        if i[0:len(shapefilename)] == shapefilename:
                            files.append(os.path.join(path,i))
                zipFileName = f'{path}/{field_name}_{metric}_{date}.zip'
                zipObj = ZipFile(zipFileName, 'w')
                for file in files:
                    zipObj.write(file)
                zipObj.close()

                # Add a download link for the zip file
                with open(zipFileName, 'rb') as f:
                    st.download_button('Download as ShapeFile', f,file_name=zipFileName)

            # Get the tiff file path and create a download link
            with download_as_tiff_col:
                #get the tiff file path
                tiff_path = utils.get_masked_location_img_path(client_name, metric, date, field_name)
                # Add a download link for the tiff file
                donwnload_filename = f'{metric}_{field_name}_{date}.tiff'
                with open(tiff_path, 'rb') as f:
                    st.download_button('Download as Tiff File', f,file_name=donwnload_filename)

    else:
        st.info('Please Select A Field and A Date')
           

def monitor_fields():
    current_user = greeting("Let's take a look how these fields are doing")
    if os.path.exists(f"fields_{current_user}.parquet"):
        gdf = gpd.read_parquet(f"fields_{current_user}.parquet")
    else:
        st.info("No Fields Added Yet!")
        return

    
    with st.expander("Existing Fields List", expanded=False):
        st.write(gdf)

    field_name = select_field(gdf)
    if field_name == "Select Field":
        st.info("No Field Selected Yet!")
    
    else:
        with st.expander("Metrics Explanation", expanded=False):
            st.write("NDVI: Normalized Difference Vegetation Index, Mainly used to monitor the health of vegetation")
            st.write("LAI: Leaf Area Index, Mainly used to monitor the productivity of vegetation")
            st.write("CAB: Chlorophyll Absorption in the Blue band, Mainly used to monitor the chlorophyll content in vegetation")
            # st.write("NDMI: Normalized Difference Moisture Index, Mainly used to monitor the moisture content in vegetation")
        st.success("More metrics and analysis features will be added soon")
        metric = st.radio("Select Metric to Monitor", ["NDVI", "LAI", "CAB"], key="metric", index=0, help="Select the metric to monitor")
        st.write(f"Monitoring {metric} for {field_name}")

        track(metric, field_name, gdf, current_user)

        


if __name__ == '__main__':
    check_authentication()
    monitor_fields()