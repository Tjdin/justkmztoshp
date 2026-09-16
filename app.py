import os
import shutil
import tempfile
import zipfile
import geopandas as gpd
import streamlit as st

st.title("KML/KMZ to GA Shapefile Converter")
st.write(
    "Upload a KML/KMZ file, select your Georgia coordinate system, and download "
    "the zipped shapefile ready for MicroStation/OpenRoads."
)

# 1. File Uploader widget
uploaded_file = st.file_uploader("Choose a KML or KMZ file", type=["kml", "kmz"])

# 2. Coordinate System Selector
zone_choice = st.selectbox(
    "Select Georgia Coordinate System:",
    [
        "Georgia East (NAD83, US Feet - EPSG:2239)",
        "Georgia West (NAD83, US Feet - EPSG:2240)",
    ],
)

# Map choice to EPSG codes
epsg_map = {
    "Georgia East (NAD83, US Feet - EPSG:2239)": 2239,
    "Georgia West (NAD83, US Feet - EPSG:2240)": 2240,
}

if uploaded_file is not None and st.button("Convert to Shapefile"):
  with st.spinner("Processing conversion..."):
    # Create a temporary directory to safely process files
    with tempfile.TemporaryDirectory() as tmpdir:
      input_path = os.path.join(tmpdir, uploaded_file.name)
      with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

      # Handle KMZ (which is just a zip file containing a kml)
      if uploaded_file.name.endswith(".kmz"):
        with zipfile.ZipFile(input_path, "r") as zip_ref:
          zip_ref.extractall(tmpdir)
        # Find the extracted kml file
        kml_files = [
            f for f in os.listdir(tmpdir) if f.endswith(".kml")
        ]
        if kml_files:
          read_path = os.path.join(tmpdir, kml_files[0])
        else:
          st.error("No KML file found inside the KMZ archive.")
          st.stop()
      else:
        read_path = input_path

      try:
        # Read KML using GeoPandas
        # Note: KML layers sometimes need specific handling, but default read_file works for basic geometries
        gdf = gpd.read_file(read_path)

        if gdf.empty:
          st.error("The uploaded file contains no valid spatial data.")
          st.stop()

        # Target EPSG code based on user selection
        target_epsg = epsg_map[zone_choice]

        # Reproject from WGS84 (KML default) to GA State Plane
        gdf = gdf.to_crs(epsg=target_epsg)

        # Define output shapefile paths
        shp_name = "converted_features.shp"
        shp_path = os.path.join(tmpdir, shp_name)

        # Export to shapefile
        gdf.to_file(shp_path, driver="ESRI Shapefile")

        # Zip all generated shapefile components together (.shp, .shx, .dbf, .prj)
        zip_output_path = os.path.join(tmpdir, "shapefiles.zip")
        with zipfile.ZipFile(zip_output_path, "w") as zip_out:
          for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            part_file = os.path.join(
                tmpdir, f"converted_features{ext}"
            )
            if os.path.exists(part_file):
              zip_out.write(part_file, arcname=f"converted_features{ext}")

        # Read the zip file back into memory to offer a download button
        with open(zip_output_path, "rb") as fp:
          zip_bytes = fp.read()

        st.success("Conversion successful!")
        st.download_button(
            label="Download Zipped Shapefiles",
            data=zip_bytes,
            file_name="GA_Shapefiles_For_OpenRoads.zip",
            mime="application/zip",
        )

      except Exception as e:
        st.error(f"An error occurred during conversion: {e}")