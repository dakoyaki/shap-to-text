import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

st.sidebar.title("Contact")
st.sidebar.info(
    """
    Dakota McCarty: <https://dakotamccarty.com>
    """
)

# Customize page title
st.title("Dakota's Streamlit Playground")

st.markdown(
    """
    A playground! \nThe left hand panel shows the available apps here to view. 
    """
)
