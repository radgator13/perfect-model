import streamlit as st
import urllib.parse

st.set_page_config(page_title="Pitcher Param Test", layout="wide")

st.markdown("## 🧪 Query Param Test")

# Read param directly from the URL
params = st.query_params

if "pitcher" in params:
    raw_value = params["pitcher"][0]
    decoded_name = urllib.parse.unquote(raw_value)

    st.markdown(f"**Raw param:** `{raw_value}`")
    st.markdown(f"**Decoded name:** `{decoded_name}`")
else:
    st.info("No pitcher param found in URL.")

# Example link
example_name = "Tarik Skubal"
encoded = urllib.parse.quote(example_name)
st.markdown(f"➡️ [Test link for {example_name}](?pitcher={encoded})")
