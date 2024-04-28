# main.py
import streamlit as st
import authentication 
from authentication import greeting
import streamlit as st
from pag import add_field, edit, monitor,contact_form
st. set_page_config(layout="wide")


def authenticate_user():
    st.markdown("""
            <style>
            .stSelectbox > div > div {cursor: pointer;}
            </style>
            """, unsafe_allow_html=True)
    if not st.session_state.authenticated:
        st.title("Welcome to :orange[Field Monitoring App]")
        row1_col1, row1_col2 = st.columns([2, 1])

        with row1_col1:
            choice = st.selectbox("Interested? Sign up or log in if you have an account",options=["Login","SignUp","Contact Us"])
            if choice == "SignUp":
                    authentication.signup()
            elif choice == "Login":
                st.title("Have an account? :orange[Sign In]")
                st.toast("Use your username and password to access our services", icon='😍')
                authentication.login()
            elif choice == "Contact Us":
                contact_form.main()
                 
                 
                 
        with row1_col2:
                st.title(":orange[App Description]")

                st.markdown("""
                Our application is designed to empower farmers and land managers with precise, up-to-date information about their fields. Leveraging the power of advanced satellite imagery analysis, our tool provides key metrics like the Normalized Difference Vegetation Index (NDVI) to assess plant health, moisture levels, and overall field conditions.

                #### :orange[Key Features]

                - **:orange[Real-time Field Data]**: Access the latest satellite data to monitor your fields in real-time.
                - **:orange[Field Health Analysis]**: Utilize NDVI and other indices to make informed decisions about crop health and management strategies.
                - **:orange[Interactive Map Views]**: Explore your fields with interactive maps, get detailed insights with just a click.
                - **:orange[Field History Tracking]**: Review historical data to track changes and adapt your farming practices accordingly.
                - **:orange[Data-Driven Insights]**: Make better decisions with insights driven by accurate, reliable data.

                We are committed to providing you with the tools you need to manage your fields more effectively and increase your yields. Get started by adding your fields and see the immediate benefits of precision agriculture.

                For any questions or assistance, feel free to reach out through our contact page.

                Happy Farming!
                """, unsafe_allow_html=True)


    return False


def main():
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False 

    if st.session_state.authenticated:
        st.sidebar.title("Navigation")
        row1_col1, row1_col2 = st.columns([2, 1])

        options = st.sidebar.radio("Choose an option:", 
                                    ("Add and Manage Fields", "Monitor Fields"))
        if options == "Add and Manage Fields":
            with  row1_col1:
                st.title("Welcome to :orange[Field Monitoring App]")
                add_field.add_drawing()
            with row1_col2:
                st.title(":orange[Field Management]")
                current_user = greeting("Manage your fields")

                edit.edit_fields(current_user)  

        elif options == "Monitor Fields":
            monitor.monitor_fields()
    else:
        authenticate_user()
if __name__ == "__main__":
    main()
