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
    " US Survey Feet)** shapefile packages optimized for MicroStation and"
    " OpenRoads."
)

# 1. File Uploader widget
uploaded_file = st.file_uploader("Choose a KML or KMZ file", type=["kml", "kmz"])

st.markdown("### ⚙️ Coordinate System Settings")

# Selection mode options
selection_method = st.radio(
    "Choose how to define the coordinate system:",
    [
        "Select Coordinate Zone (East / West)",
        "Select by Region / Major County Hub",
        "Auto-Detect Zone from Data Location",
    ],
)

target_epsg = 2239  # Default placeholder

if selection_method == "Select Coordinate Zone (East / West)":
  zone_choice = st.selectbox(
      "Select Georgia NAD83 Zone (US Feet):",
      [
          "Georgia East Zone (EPSG: 2239)",
          "Georgia West Zone (EPSG: 2240)",
      ],
  )
  target_epsg = 2239 if "East" in zone_choice else 2240

elif selection_method == "Select by Region / Major County Hub":
  hub_choice = st.selectbox(
      "Select Regional Hub:",
      [
          (
              "East GA Hub (Savannah, Augusta, Brunswick, Statesboro -> East"
              " Zone EPSG:2239)"
          ),
          (
              "West/Central GA Hub (Atlanta, Macon, Columbus, Athens -> West"
              " Zone EPSG:2240)"
          ),
      ],
  )
  target_epsg = 2239 if "East GA Hub" in hub_choice else 2240

else:
  st.info(
      "🤖 **Auto-Detect Enabled:** The app will read your KML geometry"
      " coordinates and automatically apply East (2239) or West (2240) based"
      " on its geographic position."
  )
  target_epsg = None  # Triggers dynamic calculation

if uploaded_file is not None and st.button("Convert to Shapefile (.zip)"):
  with st.spinner("Processing spatial conversion..."):
    with tempfile.TemporaryDirectory() as tmpdir:
      input_path = os.path.join(tmpdir, uploaded_file.name)
      with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

      # Handle KMZ archives
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
          st.error("The uploaded file contains no valid spatial data.")
          st.stop()

        # Standardize initial read to WGS84 (KML default)
        if gdf.crs is None:
          gdf.set_crs(epsg=4326, inplace=True)
        else:
          gdf = gdf.to_crs(epsg=4326)

        # Handle auto-detection calculation if selected
        if target_epsg is None:
          centroid = gdf.unary_union.centroid
          lon = centroid.x
          # Splitting longitude line dividing GA East and West zones (~ -83.25°)
          if lon >= -83.25:
            target_epsg = 2239
            st.write(
                "📍 Auto-detected region: **Eastern Georgia** (Assigned"
                " EPSG:2239 - US Ft)"
            )
          else:
            target_epsg = 2240
            st.write(
                "📍 Auto-detected region: **Western Georgia** (Assigned"
                " EPSG:2240 - US Ft)"
            )

        # Reproject data to the selected Georgia State Plane zone
        gdf = gdf.to_crs(epsg=target_epsg)

        # Export to ESRI Shapefile format
        shp_name = "converted_features.shp"
        shp_path = os.path.join(tmpdir, shp_name)
        gdf.to_file(shp_path, driver="ESRI Shapefile")

        # Package components (.shp, .shx, .dbf, .prj) into a zip file
        zip_output_path = os.path.join(tmpdir, "shapefiles.zip")
        with zipfile.ZipFile(zip_output_path, "w") as zip_out:
          for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            part_file = os.path.join(tmpdir, f"converted_features{ext}")
            if os.path.exists(part_file):
              zip_out.write(part_file, arcname=f"converted_features{ext}")

        with open(zip_output_path, "rb") as fp:
          zip_bytes = fp.read()

        zone_label = (
            "Georgia East (EPSG:2239)"
            if target_epsg == 2239
            else "Georgia West (EPSG:2240)"
        )
        st.success(f"Successfully converted using **{zone_label}**!")

        st.download_button(
            label="Download Zipped Shapefiles (.zip)",
            data=zip_bytes,
            file_name="GA_OpenRoads_Shapefiles.zip",
            mime="application/zip",
        )

      except Exception as e:
        st.error(f"An error occurred during conversion: {e}")