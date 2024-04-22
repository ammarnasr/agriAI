# main.py
import streamlit as st
import authentication 
import streamlit as st
from pag import add_field, edit, moniter
 
# from pages import add_field, edit, moniter
def authenticate_user():
    st.title("Welcome to :orange[Field Monitoring App]")
    st.markdown("""
            <style>
            .stSelectbox > div > div {cursor: pointer;}
            </style>
            """, unsafe_allow_html=True)
    if not st.session_state.authenticated:
        choice = st.selectbox("Interested? Sign up or log in if you have an account",options=["Home","Login","SignUp"])

        if choice == "Home":
          st.write("App Description")

        elif choice == "Login":
            authentication.login()
        elif choice == "SignUp":
            authentication.signup()

    return False

def main():
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        st.sidebar.title("Navigation")
        options = st.sidebar.radio("Choose an option:", 
                                   ("Add Field", "Edit", "Monitor"))
        
        if options == "Add Field":
            st.title("Welcome to :orange[Field Monitoring App]")

            add_field.add_drawing()
            
        elif options == "Edit":
            st.title("Welcome to :orange[Field Monitoring App]")
            edit.edit_fields()
        elif options == "Monitor":
            st.title("Welcome to :orange[Field Monitoring App]")
            moniter.monitor_fields()
    else:
        authenticate_user()
if __name__ == "__main__":
    main()
