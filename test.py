import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Your App Title",
    page_icon=":shark:",
    layout="wide",  # Use "wide" for expanded layout
    initial_sidebar_state="expanded",
)

# def local_css(file_name):
#     with open(file_name) "r") as f:
#         st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Write CSS to apply styles
def custom_css():
    st.markdown("""
        <style>
            html, body, [data-testid="stAppViewContainer"] {
                background-color: #000000;  /* Black background */
                color: #FFFFFF;  /* White text color */
            }
            .stTextInput > label, .stSelectbox > label, .stRadio > label, .stCheckbox > label {
                color: #CCCCCC;  /* Lighter text for better contrast */
            }
            /* Additional styling can be added here */
        </style>
        """, unsafe_allow_html=True)

# Load CSS file (if you have a CSS file you prefer to use)
# local_css("styles.css")

# Apply custom CSS
custom_css()

# Your app code
st.title("Your Streamlit App")
st.write("This is a sample app with a black background.")

# Example of other components
st.text_input("Enter some text")
st.selectbox("Choose an option", ["Option 1", "Option 2", "Option 3"])
st.checkbox("Check me out")
