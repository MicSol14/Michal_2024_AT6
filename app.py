import streamlit as st
import pandas as pd

st.title("My Dashboard")

data = {
    "Year":[1990,2000,2010,2020],
    "Sightings":[100,300,700,1200]
}

df = pd.DataFrame(data)

st.line_chart(df.set_index("Year"))