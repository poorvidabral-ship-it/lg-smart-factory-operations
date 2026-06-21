import streamlit as st

st.sidebar.title("Test Nav")
st.sidebar.radio("Menu", ["Home", "Page 2", "Page 3"])
st.write("Main content")