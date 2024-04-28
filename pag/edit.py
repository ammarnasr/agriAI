# edit.py
import os
import utils
import streamlit as st
import geopandas as gpd
from streamlit_folium import folium_static
import folium
import time
import pandas as pd

def add_properties(df, col_name, value, field_name):
    if col_name not in df.columns:
        df[col_name] = None
    df.loc[df['name'] == field_name, col_name] = value
    return df

def select_field(gdf):
    st.markdown("""
            <style>
            .stSelectbox > div > div {cursor: pointer;}
            </style>
            """, unsafe_allow_html=True)
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


def edit_fields(current_user):
    # current_user = greeting("Manage your fields")
    fields_file_path = f"fields_{current_user}.parquet"
    history_file_path = f"history_{current_user}.csv"
    
    # Load or initialize the GeoDataFrame for fields
    if os.path.exists(fields_file_path):
        gdf = gpd.read_parquet(fields_file_path)
    else:
        st.info("No fields added yet!")
        return
    
    # Load or initialize the DataFrame for field usage history
    if os.path.exists(history_file_path):
        history_df = pd.read_csv(history_file_path)
    else:
        history_df = pd.DataFrame(columns=['field_name', 'start_date', 'end_date', 'crop', 'irrigation_method'])

    st.info("Hover over the field to show the properties or check the Existing Fields List below")
    field_name = select_field(gdf)
    if field_name == "Select Field":
        fields_map = gdf.explore()
        sat_basemap = utils.basemaps['Google Satellite']
        sat_basemap.add_to(fields_map)
        folium.LayerControl().add_to(fields_map)
        folium_static(fields_map, height=300, width=400)
        st.info("No Field Selected Yet!")
    else:
        fields_map = gdf[gdf['name'] == field_name].explore()
        sat_basemap = utils.basemaps['Google Satellite']
        sat_basemap.add_to(fields_map)
        folium.LayerControl().add_to(fields_map)
        folium_static(fields_map, height=300, width=400)
        st.subheader(f":green[{field_name}]")
        option_menu = st.radio(f"Please add your {field_name} field information, historical data will help train our AI model", options=["View Field Info", "Add Field Information","Add Field Cultivation History", "Delete"], key="option_menu", help="Select the operation to perform")
        if option_menu == "View Field Info":
            field = gdf[gdf['name'] == field_name]
            st.write(field)
            # Deserialize the usage history for display
            if len(history_df)>0:
                st.write("Previous cultivation History:", history_df)
            else:
                st.subheader("No cultivation history added for this field.")

        elif option_menu == "Add Field Information":
         

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
                st.success("Field Information Updated Successfully!")
                st.info("Please Select View above to see the updated field information")

        elif option_menu == "Add Field Cultivation History":
            with st.form(key='history_form', clear_on_submit=True):
                start_date = st.date_input("Cultivation Start Date", key=f'start_date')
                end_date = st.date_input("Cultivation End Date", key=f'end_date')
                crop_planted = st.selectbox("Type of Crop Planted", [' ', 'Wheat', 'Corn', 'Rice',"other"], index=0)
               
                irrigation_method = st.selectbox("Irrigation Method Used", ['Rainfed', 'Irrigated', " "], index=2)
                submit_history = st.form_submit_button("Submit Crop Cycle")
                if submit_history:
                    # Check that the start date is before the end date
                    if start_date < end_date:
                        # Append new usage entry
                        new_history = {
                            'field_name': field_name,
                            'start_date': str(start_date),
                            'end_date': str(end_date),
                            'crop': crop_planted,
                            'irrigation_method': irrigation_method
                        }
                        # Use concat instead of append
                        history_df = pd.concat([history_df, pd.DataFrame([new_history])], ignore_index=True)
                        history_df.to_csv(history_file_path, index=False)
                        st.success("Field usage history updated successfully!, fill the form again to add another cultivation history" )

                    else:
                        st.write("check the entered dates")

        elif option_menu == "Delete":
            option = st.selectbox("What do you want to delete", options=[f'Delete {field_name} Field', 'Delete a historical entry from the field'])
        
            if option == f"Delete {field_name} Field" :
                delete = st.button("Delete Entire Field", key="delete_field", help="Click to Delete Field", type="primary", use_container_width=True)
                if delete:
                    if len(gdf) == 1 and (gdf['name'] == field_name).all():  # Check if this is the only field left
                        os.remove(fields_file_path)  # Delete the .parquet file if it's the last field
                        if os.path.exists(history_file_path):
                            os.remove(history_file_path)
                        st.success("All fields deleted. The data file has been removed.")
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        gdf = gdf[gdf['name'] != field_name]
                        history_df = history_df[history_df["field_name"] != field_name ]
                        gdf.to_parquet(fields_file_path)
                        history_df.to_csv(history_file_path, index=False)
                        st.success("Field Deleted Successfully!")
                        time.sleep(0.3)
                        st.rerun()
            elif option == "Delete a historical entry from the field":
            # Allow the user to select which historical entry to delete
                idx_history_to_delete = st.selectbox("Select a history to delete, select the index of the entry that you want to delete", options=history_df[history_df['field_name'] == field_name].index)
                if st.button("Confirm Delete Historical Entry", key="delete_history", help="Click to Delete Entry", type="primary", use_container_width=True):
                    history_df.drop(labels=0, axis=0, index=None, columns=None, level=None, inplace=True, errors='raise')
                    history_df.to_csv(history_file_path, index=False)

                    st.success("Entry Deleted Successfully!")
                    time.sleep(0.3)
                    st.rerun()


if __name__ == '__main__':

    edit_fields()