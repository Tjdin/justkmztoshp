import os
import tempfile
import zipfile
import geopandas as gpd
import streamlit as st

st.set_page_config(
    page_title="GA KML/KMZ to Shapefile Converter", page_icon="🌍"
)

st.title("I literally just want this kmz to reference in the right place")
st.markdown(
    "Convert Google Earth files (`.kml`/`.kmz`) into **GA State Plane (NAD83,"
    " US Survey Feet)** shapefiles optimized for MicroStation and OpenRoads with"
    " official GDOT level standards mapping."
)

# Comprehensive dictionary mapping GA counties to their NAD83 State Plane Zone EPSG codes
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

detected_zone = None
detected_epsg = None

if uploaded_file is not None:
  with tempfile.TemporaryDirectory() as tmpdir:
    input_path = os.path.join(tmpdir, uploaded_file.name)
    with open(input_path, "wb") as f:
      f.write(uploaded_file.getbuffer())

    if uploaded_file.name.endswith(".kmz"):
      with zipfile.ZipFile(input_path, "r") as zip_ref:
        zip_ref.extractall(tmpdir)
      kml_files = [f for f in os.listdir(tmpdir) if f.endswith(".kml")]
      read_path = os.path.join(tmpdir, kml_files[0]) if kml_files else None
    else:
      read_path = input_path

    if read_path:
      try:
        temp_gdf = gpd.read_file(read_path)
        if not temp_gdf.empty:
          if temp_gdf.crs is None:
            temp_gdf.set_crs(epsg=4326, inplace=True)
          else:
            temp_gdf = temp_gdf.to_crs(epsg=4326)
          centroid = temp_gdf.unary_union.centroid
          # Automatic East/West Zone boundary judgment based on longitude
          if centroid.x >= -83.25:
            detected_zone = "East"
            detected_epsg = 2239
          else:
            detected_zone = "West"
            detected_epsg = 2240
      except Exception:
        pass

st.markdown("### ⚙️ County & Zone Options")

multi_county = st.checkbox("My data crosses multiple counties")
sorted_counties = sorted(list(GA_COUNTY_ZONES.keys()))
target_epsgs = []

if multi_county:
  selected_counties = st.multiselect(
      "Select all counties your project crosses:",
      sorted_counties,
      default=[],
      placeholder="Search and select counties...",
  )
  if selected_counties:
    target_epsgs = list(
        set(GA_COUNTY_ZONES[county] for county in selected_counties)
    )
    zones_display = ", ".join(
        [
            "East Zone (2239)" if z == 2239 else "West Zone (2240)"
            for z in target_epsgs
        ]
    )
    st.info(
        f"Selected counties cover: **{zones_display}**."
        " If both zones are represented, the app will automatically split and"
        " export separate East and West zip bundles."
    )
  else:
    st.warning("Please select at least one county for your multi-county run.")
else:
  selected_county = st.selectbox(
      "Georgia County (Optional):",
      sorted_counties,
      index=None,
      placeholder="Click to type or select a county...",
  )

  if selected_county:
    county_epsg = GA_COUNTY_ZONES[selected_county]
    zone_name = (
        "Georgia East (EPSG: 2239)"
        if county_epsg == 2239
        else "Georgia West (EPSG: 2240)"
    )
    st.success(
        f"📍 **{selected_county} County** selected -> **{zone_name}** (US Survey"
        " Feet)"
    )

  zone_override = st.selectbox(
      "Coordinate System Zone (Override):",
      [
          "Auto-Detect / Match File Location",
          "Georgia East Zone (EPSG: 2239 - US Ft)",
          "Georgia West Zone (EPSG: 2240 - US Ft)",
      ],
  )

  if selected_county:
    target_epsgs = [GA_COUNTY_ZONES[selected_county]]
  elif zone_override == "Georgia East Zone (EPSG: 2239 - US Ft)":
    target_epsgs = [2239]
  elif zone_override == "Georgia West Zone (EPSG: 2240 - US Ft)":
    target_epsgs = [2240]
  elif detected_epsg is not None:
    target_epsgs = [detected_epsg]
  else:
    target_epsgs = [2240]

  if (
      detected_epsg is not None
      and zone_override != "Auto-Detect / Match File Location"
  ):
    chosen_epsg = target_epsgs[0]
    user_chosen_zone = "East" if chosen_epsg == 2239 else "West"
    if user_chosen_zone != detected_zone:
      st.warning(
          f"⚠️ **GDOT Compliance Warning:** Your uploaded file geometry maps"
          f" to the **{detected_zone} Zone**, but you manually selected the"
          f" **{user_chosen_zone} Zone**. Per the [GDOT MicroStation CAD and"
          " WMS Imagery Services Manual (Page 4"
          " Map)](https://www.dot.ga.gov/PartnerSmart/DesignManuals/ElectronicData/GDOT_MicroStation-Cad-WMS-Imagery-Services.pdf),"
          " using a zone contrary to your geographic location will introduce"
          " linear distortions and alignment shifts in OpenRoads."
      )

feature_selection = st.selectbox(
    "Optional Export Level",
    options=[
        "PROP_E_PAR-PL-Line - existing property line",
        "TOPO_E_TEAP-Line - edge of asphalt pavement",
        "PROP_E_ACL-Line - existing centerline",
    ],
    index=None,
    placeholder="optional export level",
    accept_new_options=True,
    label_visibility="collapsed",
)

if uploaded_file is not None and st.button("Convert to Shapefile (.zip)"):
  if multi_county and not selected_counties:
    st.error("Please select at least one county.")
    st.stop()

  with st.spinner("Processing coordinate conversion and level mapping..."):
    with tempfile.TemporaryDirectory() as tmpdir:
      input_path = os.path.join(tmpdir, uploaded_file.name)
      with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

      if uploaded_file.name.endswith(".kmz"):
        with zipfile.ZipFile(input_path, "r") as zip_ref:
          zip_ref.extractall(tmpdir)
        kml_files = [f for f in os.listdir(tmpdir) if f.endswith(".kml")]
        read_path = os.path.join(tmpdir, kml_files[0]) if kml_files else None
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

        if feature_selection:
          if " - " in feature_selection:
            final_level_value = feature_selection.split(" - ")[0].strip()
          else:
            final_level_value = feature_selection.strip()

          gdf["Level"] = final_level_value
          gdf["Feature"] = final_level_value
          gdf["Name"] = final_level_value
          gdf["GDOT_Lvl"] = final_level_value

        if multi_county and set(target_epsgs) == {2239, 2240}:
          st.write(
              "✂️ Selected counties span both East and West zones. Splitting"
              " dataset across zones..."
          )
          centroids = gdf.geometry.centroid
          east_gdf = gdf[centroids.x >= -83.25].copy()
          west_gdf = gdf[centroids.x < -83.25].copy()

          if not east_gdf.empty:
            east_gdf = east_gdf.to_crs(epsg=2239)
            east_shp = os.path.join(tmpdir, "East_Zone_features.shp")
            east_gdf.to_file(east_shp, driver="ESRI Shapefile")

            east_zip = os.path.join(tmpdir, "GA_East_Zone_Shapefiles.zip")
            with zipfile.ZipFile(east_zip, "w") as zip_out:
              for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                part = os.path.join(tmpdir, f"East_Zone_features{ext}")
                if os.path.exists(part):
                  zip_out.write(part, arcname=f"GA_East_Zone_features{ext}")

            with open(east_zip, "rb") as f:
              east_bytes = f.read()

            st.success("✅ East Zone dataset created successfully!")
            st.download_button(
                label=(
                    "📥 Download East Zone Shapefiles (.zip) [EPSG:2239 - US"
                    " Ft]"
                ),
                data=east_bytes,
                file_name="GA_East_Zone_OpenRoads.zip",
                mime="application/zip",
            )
          else:
            st.info(
                "No features matched the Eastern zone geographic footprint."
            )

          if not west_gdf.empty:
            west_gdf = west_gdf.to_crs(epsg=2240)
            west_shp = os.path.join(tmpdir, "West_Zone_features.shp")
            west_gdf.to_file(west_shp, driver="ESRI Shapefile")

            west_zip = os.path.join(tmpdir, "GA_West_Zone_Shapefiles.zip")
            with zipfile.ZipFile(west_zip, "w") as zip_out:
              for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                part = os.path.join(tmpdir, f"West_Zone_features{ext}")
                if os.path.exists(part):
                  zip_out.write(part, arcname=f"GA_West_Zone_features{ext}")

            with open(west_zip, "rb") as f:
              west_bytes = f.read()

            st.success("✅ West Zone dataset created successfully!")
            st.download_button(
                label=(
                    "📥 Download West Zone Shapefiles (.zip) [EPSG:2240 - US"
                    " Ft]"
                ),
                data=west_bytes,
                file_name="GA_West_Zone_OpenRoads.zip",
                mime="application/zip",
            )
          else:
            st.info(
                "No features matched the Western zone geographic footprint."
            )

        else:
          single_epsg = target_epsgs[0]
          gdf = gdf.to_crs(epsg=single_epsg)

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

          zone_label = (
              "Georgia East (EPSG:2239)"
              if single_epsg == 2239
              else "Georgia West (EPSG:2240)"
          )
          st.success(f"Conversion successful using **{zone_label}**!")

          st.download_button(
              label="📥 Download Zipped Shapefiles (.zip)",
              data=zip_bytes,
              file_name="GA_OpenRoads_Shapefiles.zip",
              mime="application/zip",
          )

      except Exception as e:
        st.error(f"An error occurred during conversion: {e}")

# --- How Does This Work Section ---
st.markdown("---")
st.markdown("### 📖 How Does This Work?")

tab_eli5, tab_tech = st.tabs(
    ["Explain Like I'm 5", "Technical Deep Dive"]
)

with tab_eli5:
  st.markdown("""
    Imagine you draw a picture on a flat piece of paper (Google Earth global coordinates), but your engineering software needs that same picture wrapped precisely over a 3D model of Georgia using measuring tapes marked in feet. 
    
    1. **Unpacking the Box:** If your file is a `.kmz`, it's like a zipped toy box. We open it up to find the drawing inside (`.kml`).
    2. **Finding Where You Are:** We look at where your drawing sits on the map. If it's on the right side of Georgia, we prep it for the **East Zone**. If it's on the left, we prep it for the **West Zone**.
    3. **Changing the Units:** We take your drawing's global GPS coordinates and recalculate every single point into precise **US Survey Feet** so your engineering design software doesn't get confused.
    4. **Packing It Up:** We package your freshly converted drawing into a tidy little zip folder containing all the special files engineering software needs to read it smoothly!
    """)

with tab_tech:
  st.markdown("""
    Under the hood, the application processes spatial vector geometries through a secure, containerized Python runtime environment using geospatial libraries:
    
    * **File Decompression & Parsing:** KMZ archives are unpacked via Python's built-in `zipfile` module to extract raw XML-based KML payloads, which are ingested via `geopandas`.
    * **Spatial Centroid Calculation & Zone Auto-Detection:** The engine computes the global bounding box centroid (`unary_union.centroid`) of the imported geometries in latitude/longitude (EPSG:4326). It evaluates longitude against Georgia's state-plane demarcation meridian (~ -83.25° W) to automatically classify features into **Georgia East Zone (EPSG:2239)** or **Georgia West Zone (EPSG:2240)**.
    * **Coordinate Reference System (CRS) Transformation:** Geometries are mathematically re-projected from global geodetic coordinates to NAD83 State Plane coordinates measured in **US Survey Feet**, preserving engineering-grade linear accuracy required by GDOT specifications.
    * **Attribute Mapping & Serialization:** Optional level designations populate standardized schema headers (`Level`, `Feature`, `Name`, `GDOT_Lvl`). Features are serialized into ESRI Shapefile format components (`.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`) and bundled into an in-memory ZIP stream for direct user retrieval.
    """)