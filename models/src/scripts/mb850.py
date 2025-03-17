import os
from datetime import datetime
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap, Normalize
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import pandas as pd
from scipy.ndimage import zoom  # For wind barb interpolation
from .utils import create_directory, write_to_s3


def generate_dew_point_image(hour, grib_file, today, model_run, local_run):
    
    # Open the GRIB2 file
    ds = xr.open_dataset(grib_file, engine="cfgrib", filter_by_keys={'typeOfLevel': 'isobaricInhPa'})
    
    # Convert longitudes if necessary
    if ds.longitude.max() > 180:
        ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360 - 180))
        ds = ds.sortby("longitude")

    # Extract 850mb data
    ds_850 = ds.sel(isobaricInhPa=850)
    ds_850 = ds_850.where(
        (ds_850.latitude >= 5) & (ds_850.latitude <= 75) &
        (ds_850.longitude >= -160) & (ds_850.longitude <= -40), 
        drop=True
    )

    # ✅ Compute Dew Point Temperature Since 'd' is Missing
    T = ds_850["t"]  # Temperature (K)
    q = ds_850["q"]  # Specific Humidity (kg/kg)

    # ✅ Compute Vapor Pressure (hPa)
    P = 850  # 850 mb pressure level in hPa
    e = (q * P) / (0.622 + q)

    # ✅ Compute Dew Point (Celsius)
    dpt850 = (243.5 * (np.log(e) - np.log(6.112))) / (17.67 - (np.log(e) - np.log(6.112)))

    # Convert Winds to Knots
    u850 = ds_850["u"] * 1.94384  # ✅ Convert U-wind to knots
    v850 = ds_850["v"] * 1.94384  # ✅ Convert V-wind to knots

    # Compute wind speed in knots
    wind_speed_knots = np.sqrt(u850**2 + v850**2)

    # Get model run date and forecast hour
    run_time = pd.to_datetime(str(ds.time.values)).strftime('%Y-%m-%d: %HZ')
    forecast_hour = ds.step.values.astype('timedelta64[h]').astype(int)
    
    print(f"Model Run: {run_time}, Forecast Hour: {forecast_hour}")

    # Define figure
    fig = plt.figure(figsize=(14, 9))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-160, -40, 5, 75], crs=ccrs.PlateCarree())

    # Add map features (improved visibility)
    ax.add_feature(cfeature.COASTLINE, edgecolor="black", linewidth=1.2, zorder=10)
    ax.add_feature(cfeature.BORDERS, edgecolor="black", linewidth=1.0, zorder=10)
    ax.add_feature(cfeature.STATES, edgecolor="gray", linestyle="--", linewidth=0.8, zorder=10)

    # Ensure coordinates are in correct format
    dpt850 = dpt850.sortby("longitude")
    u850 = u850.sortby("longitude")
    v850 = v850.sortby("longitude")

    # Subset the variables
    lons = dpt850.longitude.values
    lats = dpt850.latitude.values
    dpt850_sub = dpt850.values  # Convert to NumPy array

    # ✅ Define Colormap for Dew Point (blue/green for moisture)
    cmap_dpt = mcolors.LinearSegmentedColormap.from_list("dpt_cmap", [
        (0.0, "#8B4513"),   # Dry (Brown) - Lowest
        (0.3, "#A9A9A9"),   # Mid-range (Gray)
        (0.5, "#2E8B57"),   # Humid (Green)
        (0.7, "#00BFFF"),   # Very Humid (Light Blue)
        (1.0, "#0000FF")    # Tropical Air (Deep Blue) - Highest
    ], N=256)

    # Dew Point shading
    dpt_levels = np.linspace(-30, 25, 50)  # 50 levels for smooth shading
    dpt_plot = ax.contourf(lons, lats, dpt850_sub, levels=dpt_levels, cmap=cmap_dpt, extend="both", transform=ccrs.PlateCarree())

    # ✅ Reduce Wind Barb Density (Interpolation Method)
    barb_density = 0.15  # ✅ Same density as RH version
    interp_u = zoom(u850.values, barb_density)
    interp_v = zoom(v850.values, barb_density)
    interp_lons = zoom(lons, barb_density)
    interp_lats = zoom(lats, barb_density)

    # ✅ Remove Very Weak Winds (<5 knots) to Avoid Circles
    mask = np.sqrt(interp_u**2 + interp_v**2) > 5  # ✅ Wind speeds in knots
    interp_u = np.where(mask, interp_u, np.nan)
    interp_v = np.where(mask, interp_v, np.nan)

    # ✅ Wind Barbs
    ax.barbs(interp_lons, interp_lats, interp_u, interp_v, 
                length=5, linewidth=0.7, color="black", transform=ccrs.PlateCarree())  # ✅ Smaller barbs

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
    gl.top_labels = False

    # Add color bar
    cbar = plt.colorbar(dpt_plot, orientation="horizontal", pad=0.05, aspect=50)
    cbar.set_label("850mb Dew Point (°C)")

    # Add title
    plt.title(f"GFS 850 mb Dew Point & Wind Barbs\nRun: {run_time} | Forecast Hour: {forecast_hour}h", fontsize=14)

    # Save image
    filepath = f"{os.getcwd()}/images/850mb/dewpoint/{today}/{model_run}/{hour}_hour.png"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close()
    if local_run is False:
        write_to_s3(filepath, today, model_run, "850mb", "dewpoint")



def generate_rh_image(hour, grib_file, today, model_run, local_run):
    
    # Open the GRIB2 file
    ds = xr.open_dataset(grib_file, engine="cfgrib", filter_by_keys={'typeOfLevel': 'isobaricInhPa'})
    
    # Convert longitudes if necessary
    if ds.longitude.max() > 180:
        ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360 - 180))
        ds = ds.sortby("longitude")

    # Extract 850mb data
    ds_850 = ds.sel(isobaricInhPa=850)
    ds_850 = ds_850.where(
        (ds_850.latitude >= 5) & (ds_850.latitude <= 75) &
        (ds_850.longitude >= -160) & (ds_850.longitude <= -40), 
        drop=True
    )

    # Extract variables
    rh850 = ds_850["r"]  # Relative Humidity (%)
    u850 = ds_850["u"]   # U-wind (m/s)
    v850 = ds_850["v"]   # V-wind (m/s)

    # Convert wind speed to knots
    wind_speed_knots = np.sqrt(u850**2 + v850**2) * 1.94384  # Convert m/s to knots ✅

    # Get model run date and forecast hour
    run_time = pd.to_datetime(str(ds.time.values)).strftime('%Y-%m-%d: %HZ')
    forecast_hour = ds.step.values.astype('timedelta64[h]').astype(int)
    
    print(f"Model Run: {run_time}, Forecast Hour: {forecast_hour}")

    # Define figure
    fig = plt.figure(figsize=(14, 9))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-160, -40, 5, 75], crs=ccrs.PlateCarree())

    # ✅ Improved borders for better visibility
    ax.add_feature(cfeature.COASTLINE, edgecolor="black", linewidth=1.2, zorder=10)
    ax.add_feature(cfeature.BORDERS, edgecolor="black", linewidth=1.0, zorder=10)
    ax.add_feature(cfeature.STATES, edgecolor="black", linestyle="--", linewidth=1, zorder=10)


    # Ensure coordinates are in correct format
    rh850 = rh850.sortby("longitude")
    u850 = u850.sortby("longitude")
    v850 = v850.sortby("longitude")

    # Subset the variables
    lons = rh850.longitude.values
    lats = rh850.latitude.values
    rh850_sub = rh850.values  # Convert to NumPy array

    # Define colormap for RH shading (matching Pivotal Weather)
    cmap_rh = mcolors.LinearSegmentedColormap.from_list("rh_cmap", [
        (0.0, "#8B4513"),  # Brown for dry air
        (0.5, "#A9A9A9"),  # Gray for mid-range RH
        (1.0, "#006400")   # Dark green for very moist air
    ], N=256)

    # RH shading
    rh_levels = np.linspace(0, 100, 50)  # 50 levels for smooth shading
    rh_plot = ax.contourf(lons, lats, rh850_sub, levels=rh_levels, cmap=cmap_rh, extend="both", transform=ccrs.PlateCarree())

    # Reduce wind barb density (interpolation method)
    barb_density = 0.10  # ✅ Further reduce number of barbs
    interp_u = zoom(u850.values * 1.94384, barb_density)  # Convert to knots ✅
    interp_v = zoom(v850.values * 1.94384, barb_density)  # Convert to knots ✅

    interp_lons = zoom(lons, barb_density)
    interp_lats = zoom(lats, barb_density)

    # Remove very weak winds (<5 knots) to avoid circles
    mask = np.sqrt(interp_u**2 + interp_v**2) * 1.94384 > 5  # ✅ Wind speeds in knots
    interp_u = np.where(mask, interp_u, np.nan)
    interp_v = np.where(mask, interp_v, np.nan)

    # Wind barbs
    ax.barbs(interp_lons, interp_lats, interp_u, interp_v, 
                length=5, linewidth=0.7, color="black", transform=ccrs.PlateCarree())  # ✅ Smaller barbs

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
    gl.top_labels = False

    # Add color bar
    cbar = plt.colorbar(rh_plot, orientation="horizontal", pad=0.05, aspect=50)
    cbar.set_label("850mb Relative Humidity (%)")

    # Add title
    plt.title(f"GFS 850 mb Relative Humidity & Wind (Knots)\nRun: {run_time} | Forecast Hour: {forecast_hour}h", fontsize=14)

    # Save image
    filepath = f"{os.getcwd()}/images/850mb/rh_wind/{today}/{model_run}/{hour}_hour.png"
    create_directory(filepath)
    # os.makedirs(os.path.dirname(filepath), exist_ok=True)
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close()
    if local_run is False:
        write_to_s3(filepath, today, model_run, "850mb", "rh_wind")
