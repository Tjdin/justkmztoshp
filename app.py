import os
import tempfile
import zipfile
import geopandas as gpd
import streamlit as st

st.set_page_config(
    page_title="GA KML/KMZ to Shapefile Converter", page_icon="🗺️"
)

st.title("Georgia KML/KMZ to Shapefile Converter")
st.markdown(
    "Convert Google Earth files (`.kml`/`.kmz`) into **GA State Plane (NAD83,"
    " US Survey Feet)** shapefiles optimized for MicroStation and OpenRoads."
)

# Comprehensive dictionary mapping GA counties to their NAD83 State Plane Zone EPSG codes
# East Zone = 2239, West Zone = 2240 (US Survey Feet)
GA_COUNTY_ZONES = {
    # East Zone (EPSG: 2239)
    "Appling": 2239,
    "Atkinson": 2239,
    "Bacon": 2239,
    "Baldwin": 2239,
    "Brantley": 2239,
    "Bryan": 2239,
    "Bulloch": 2239,
    "Burke": 2239,
    "Camden": 2239,
    "Candler": 2239,
    "Charlton": 2239,
    "Chatham": 2239,
    "Clinch": 2239,
    "Coffee": 2239,
    "Columbia": 2239,
    "Dodge": 2239,
    "Echols": 2239,
    "Effingham": 2239,
    "Elbert": 2239,
    "Emanuel": 2239,
    "Evans": 2239,
    "Franklin": 2239,
    "Glascock": 2239,
    "Glynn": 2239,
    "Greene": 2239,
    "Hancock": 2239,
    "Hart": 2239,
    "Jeff Davis": 2239,
    "Jefferson": 2239,
    "Jenkins": 2239,
    "Johnson": 2239,
    "Laurens": 2239,
    "Liberty": 2239,
    "Lincoln": 2239,
    "Long": 2239,
    "Madison": 2239,
    "McDuffie": 2239,
    "McIntosh": 2239,
    "Montgomery": 2239,
    "Pierce": 2239,
    "Richmond": 2239,
    "Screven": 2239,
    "Taliaferro": 2239,
    "Tattnall": 2239,
    "Telfair": 2239,
    "Toombs": 2239,
    "Treutlen": 2239,
    "Ware": 2239,
    "Warren": 2239,
    "Washington": 2239,
    "Wayne": 2239,
    "Wheeler": 2239,
    "Wilkes": 2239,
    "Wilkinson": 2239,
    # West Zone (EPSG: 2240)
    "Baker": 2240,
    "Banks": 2240,
    "Barrow": 2240,
    "Bartow": 2240,
    "Ben Hill": 2240,
    "Berrien": 2240,
    "Bibb": 2240,
    "Bleckley": 2240,
    "Brooks": 2240,
    "Butts": 2240,
    "Calhoun": 2240,
    "Carroll": 2240,
    "Catoosa": 2240,
    "Chattahoochee": 2240,
    "Chattooga": 2240,
    "Cherokee": 2240,
    "Clarke": 2240,
    "Clay": 2240,
    "Clayton": 2240,
    "Cobb": 2240,
    "Colquitt": 2240,
    "Cook": 2240,
    "Coweta": 2240,
    "Crawford": 2240,
    "Crisp": 2240,
    "Dade": 2240,
    "Dawson": 2240,
    "Decatur": 2240,
    "DeKalb": 2240,
    "Dooly": 2240,
    "Dougherty": 2240,
    "Douglas": 2240,
    "Early": 2240,
    "Fannin": 2240,
    "Fayette": 2240,
    "Floyd": 2240,
    "Forsyth": 2240,
    "Fulton": 2240,
    "Gilmer": 2240,
    "Gordon": 2240,
    "Grady": 2240,
    "Gwinnett": 2240,
    "Habersham": 2240,
    "Hall": 2240,
    "Haralson": 2240,
    "Harris": 2240,
    "Heard": 2240,
    "Henry": 2240,
    "Houston": 2240,
    "Irwin": 2240,
    "Jackson": 2240,
    "Jasper": 2240,
    "Jones": 2240,
    "Lamar": 2240,
    "Lanier": 2240,
    "Lee": 2240,
    "Lumpkin": 2240,
    "Macon": 2240,
    "Marion": 2240,
    "Meriwether": 2240,
    "Miller": 2240,
    "Mitchell": 2240,
    "Monroe": 2240,
    "Morgan": 2240,
    "Murray": 2240,
    "Muscogee": 2240,
    "Newton": 2240,
    "Oconee": 2240,
    "Oglethorpe": 2240,
    "Paulding": 2240,
    "Peach": 2240,
    "Pickens": 2240,
    "Pike": 2240,
    "Polk": 2240,
    "Pulaski": 2240,
    "Putnam": 2240,
    "Quitman": 2240,
    "Rabun": 2240,
    "Randolph": 2240,
    "Rockdale": 2240,
    "Schley": 2240,
    "Seminole": 2240,
    "Spalding": 2240,
    "Stephens": 2240,
    "Stewart": 2240,
    "Sumter": 2240,
    "Talbot": 2240,
    "Taylor": 2240,
    "Terrell": 2240,
    "Thomas": 2240,
    "Tift": 2240,
    "Towns": 2240,
    "Troup": 2240,
    "Turner": 2240,
    "Twiggs": 2240,
    "Union": 2240,
    "Upson": 2240,
    "Walker": 2240,
    "Walton": 2240,
    "Webster": 2240,
    "White": 2240,
    "Whitfield": 2240,
    "Wilcox": 2240,
    "Worth": 2240,
}

uploaded_file = st.file_uploader("Choose a KML or KMZ file", type=["kml", "kmz"])

st.markdown("### ⚙️ Coordinate Selection")

mode = st.radio(
    "Choose selection mode:",
    [
        "Search GA County (Autocomplete)",
        "Manual Zone Selection (East / West)",
    ],
)

target_epsg = 2240  # Default value

if mode == "Search GA County (Autocomplete)":
  sorted_counties = sorted(list(GA_COUNTY_ZONES.keys()))
  default_idx = (
      sorted_counties.index("Fulton") if "Fulton" in sorted_counties else 0
  )

  # Streamlit selectbox functions as an autocomplete search field when typed into
  selected_county = st.selectbox(
      "Type or pick a Georgia County:", sorted_counties, index=default_idx
  )

  target_epsg = GA_COUNTY_ZONES[selected_county]
  zone_desc = (
      "Georgia East Zone (EPSG: 2239 - US Survey Feet)"
      if target_epsg == 2239
      else "Georgia West Zone (EPSG: 2240 - US Survey Feet)"
  )
  st.success(
      f"📍 **{selected_county} County** selected -> Automatically assigned to"
      f" **{zone_desc}**"
  )

else:
  zone_choice = st.selectbox(
      "Select Zone manually:",
      [
          "Georgia West Zone (EPSG: 2240)",
          "Georgia East Zone (EPSG: 2239)",
      ],
  )
  target_epsg = 2239 if "East" in zone_choice else 2240

if uploaded_file is not None and st.button("Convert to Shapefile (.zip)"):
  with st.spinner("Converting files..."):
    with tempfile.TemporaryDirectory() as tmpdir:
      input_path = os.path.join(tmpdir, uploaded_file.name)
      with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

      if uploaded_file.name.endswith(".kmz"):
        with zipfile.ZipFile(input_path, "r") as zip_ref:
          zip_ref.extractall(tmpdir)
        kml_files = [f for f in os.listdir(tmpdir) if f.endswith(".kml")]
        if kml_files:
          read_path = os.path.join(tmpdir, kml_files[0])
        else:
          st.error("No KML file found inside the KMZ archive.")
          st.stop()
      else:
        read_path = input_path

      try:
        gdf = gpd.read_file(read_path)
        if gdf.empty:
          st.error("The uploaded file contains no valid spatial features.")
          st.stop()

        if gdf.crs is None:
          gdf.set_crs(epsg=4326, inplace=True)
        else:
          gdf = gdf.to_crs(epsg=4326)

        # Reproject to selected zone coordinate system
        gdf = gdf.to_crs(epsg=target_epsg)

        shp_path = os.path.join(tmpdir, "converted_features.shp")
        gdf.to_file(shp_path, driver="ESRI Shapefile")

        zip_output_path = os.path.join(tmpdir, "shapefiles.zip")
        with zipfile.ZipFile(zip_output_path, "w") as zip_out:
          for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            part_file = os.path.join(tmpdir, f"converted_features{ext}")
            if os.path.exists(part_file):
              zip_out.write(part_file, arcname=f"converted_features{ext}")

        with open(zip_output_path, "rb") as fp:
          zip_bytes = fp.read()

        st.success("Conversion successful!")
        st.download_button(
            label="Download Zipped Shapefiles (.zip)",
            data=zip_bytes,
            file_name="GA_OpenRoads_Shapefiles.zip",
            mime="application/zip",
        )

      except Exception as e:
        st.error(f"Error during conversion: {e}")