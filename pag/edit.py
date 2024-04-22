import os
import utils
import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium, folium_static
from authentication import greeting, check_password
import folium
import time
def check_authentication():
    if not check_password():
        st.stop()


def add_properties(df, col_name, value, field_name):
    if col_name not in df.columns:
        df[col_name] = None
    df.loc[df['name'] == field_name, col_name] = value
    return df

def select_field(gdf):
    names = gdf['name'].tolist()
    names.append("Select Field")
    field_name = st.selectbox("Select Field", options=names, key="field_name_edit", help="Select the field to edit", index=len(names)-1)
    return field_name

def read_crop_type():
    crop_type = st.text_input("Field Crop*", help="Enter the crop type", key="field_crop", value='')
    return crop_type

def read_irrigation_type():
    irrigation_type = st.selectbox("Field Type*", options=["Rainfed", "Irrigated", ""], key="field_type", help="Select the field type", index=2)
    return irrigation_type

def read_custom_property():
    custom_property_name = st.text_input("Custom Property Name*", help="Enter the custom property name", key="custom_property_name", value='')
    custom_property_value = st.text_input("Custom Property Value*", help="Enter the custom property value", key="custom_property_value", value='', disabled=custom_property_name == "" or custom_property_name == "")
    return custom_property_name, custom_property_value





def edit_fields():
    current_user = greeting("Changed your mind? Edit , Add or Delete Fields easily")
    file_path = f"fields_{current_user}.parquet"
    if os.path.exists(file_path):
        gdf = gpd.read_parquet(file_path)
    else:
        st.info("No Fields Added Yet!")
        return
    st.info("Hover over the field to show the properties or check the Existing Fields List below")
    fields_map = gdf.explore()
    sat_basemap = utils.basemaps['Google Satellite']
    sat_basemap.add_to(fields_map)
    folium.LayerControl().add_to(fields_map)
    folium_static(fields_map, height=300, width=600)
    
    with st.expander("Existing Fields List", expanded=False):
        st.write(gdf)

    field_name = select_field(gdf)
    if field_name == "Select Field":
        st.info("No Field Selected Yet!")
    
    else:
        delete_edit = st.radio("Delete or Edit Field?", options=["View", "Edit", "Delete"], key="delete_edit", help="Select the operation to perform")
        if delete_edit == "View":
            field = gdf[gdf['name'] == field_name]
            st.write(field)
        elif delete_edit == "Delete":
            delete = st.button("Delete Field", key="delete", help="Click to Delete Field", type="primary", use_container_width=True)
            if delete:
                if len(gdf) == 1 and (gdf['name'] == field_name).all():  # Check if this is the only field left
                    os.remove(file_path)  # Delete the .parquet file if it's the last field
                    st.success("All fields deleted. The data file has been removed.")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    gdf = gdf[gdf['name'] != field_name]
                    gdf.to_parquet(file_path)
                    st.success("Field Deleted Successfully!")
                    time.sleep(0.3)
                    st.rerun()
        else:
            no_input = True
            crop_type = read_crop_type()
            irrigation_type = read_irrigation_type()
            custom_property_name, custom_property_value = read_custom_property()
            if crop_type != "" or irrigation_type != "" or custom_property_value != "":
                no_input = False

            submit = st.button("Submit", key="submitProperties", help="Click to Submit Field Information", type="primary",
                                use_container_width=True, disabled=no_input)
            if submit:
                if crop_type != "":
                    gdf = add_properties(gdf, "crop", crop_type, field_name)
                if irrigation_type != "":
                    gdf = add_properties(gdf, "irrigation", irrigation_type, field_name)
                if custom_property_name != "" and custom_property_value != "":
                    gdf = add_properties(gdf, custom_property_name, custom_property_value, field_name)
                gdf.to_parquet(f"fields_{current_user}.parquet")
                # st.rerun()
                st.success("Field Information Updated Successfully!")
                st.info("Please Select View above to see the updated field information")


if __name__ == '__main__':
    check_authentication()

    edit_fields()