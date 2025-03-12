import os
from datetime import datetime
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
import numpy as np

from .utils import create_directory, write_to_s3



def generate_height_and_vorticity_image(hour, grib_file, today, model_run, local_run):
    
    # Open the GRIB2 file
    ds = xr.open_dataset(grib_file, engine="cfgrib", filter_by_keys={'typeOfLevel': 'isobaricInhPa'})
    
    # Convert longitudes from 0-360 to -180 to 180 if needed
    if ds.longitude.max() > 180:
        ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360 - 180))
        ds = ds.sortby("longitude")
    
    # Select correct lat/lon range for full North America coverage
    ds_500 = ds.sel(isobaricInhPa=500)
    ds_500 = ds_500.where((ds_500.latitude >= 5) & (ds_500.latitude <= 75) &
                        (ds_500.longitude >= -160) & (ds_500.longitude <= -40), drop=True)
    
    # Extract height and vorticity after proper subsetting
    h500 = ds_500["gh"]
    vort500 = ds_500["absv"] * 1e5  # Convert vorticity to 1e5 s⁻¹
    
    
    # Get model run date and forecast hour
    run_time = pd.to_datetime(str(ds.time.values)).strftime('%Y-%m-%d: %HZ')# Model initialization time
    forecast_hour = ds.step.values.astype('timedelta64[h]').astype(int)  # Convert to hours
    
    print(f"Model Run: {run_time}, Forecast Hour: {forecast_hour}")  # Debugging


    # Define the figure with improved size for clarity
    fig = plt.figure(figsize=(14, 9))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Set agreed extent to fully cover North America
    ax.set_extent([-160, -40, 5, 75], crs=ccrs.PlateCarree())
    
    # Add map features
    ax.add_feature(cfeature.COASTLINE, linewidth=1)
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.add_feature(cfeature.STATES, linestyle="--", edgecolor="gray")
    
    # Ensure longitude is in the correct format (convert 0–360 to -180–180 if needed)
    if h500.longitude.max() > 180:
        h500 = h500.assign_coords(longitude=((h500.longitude + 180) % 360 - 180))
        vort500 = vort500.assign_coords(longitude=((vort500.longitude + 180) % 360 - 180))
        h500 = h500.sortby("longitude")
        vort500 = vort500.sortby("longitude")

    # Select only the North America region
    h500_sub = h500.sel(latitude=slice(75, 5), longitude=slice(-160, -40))
    vort500_sub = vort500.sel(latitude=slice(75, 5), longitude=slice(-160, -40))
    
    # Reduce resolution slightly for better performance
    h500_sub = h500_sub[::2, ::2]  
    vort500_sub = vort500_sub[::2, ::2]
    lons_sub = h500_sub.longitude.values
    lats_sub = h500_sub.latitude.values
    
    # Clip vorticity values to match reference image
    vort500_clipped = np.clip(vort500_sub, -40, 55)
    
    # Define Custom Colormap to Match Reference Image
    cmap_colors = [
        (-40, (0.4, 0.4, 0.4)),  # Dark gray
        (-30, (0.6, 0.6, 0.6)),  # Medium gray
        (-20, (0.8, 0.8, 0.8)),  # Light gray
        (-5, (1.0, 1.0, 1.0)),   # White (neutral)
        (5, (1.0, 0.9, 0.5)),    # Light yellow
        (20, (1.0, 0.6, 0.2)),   # Orange
        (35, (0.9, 0.1, 0.1)),   # Red
        (55, (0.6, 0.0, 0.6))    # Purple
    ]
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_vort", [c[1] for c in cmap_colors], N=512)
    
    # Define color levels for smooth transitions
    vort_levels = np.linspace(-32, 55, 20)  # Adjust minimum threshold to 5 instead of -40

    
    #contour_levels = np.arange(h500_min, h500_max + 60, 60)
    contour_levels = np.arange(h500.min(), h500.max(), 60)
    
    # Contour plot for 500 mb Heights
    contour = plt.contour(lons_sub, lats_sub, h500_sub, 
                        levels=contour_levels, colors="black", linewidths=1, transform=ccrs.PlateCarree())
    
    plt.clabel(contour, fmt="%d", inline=True, fontsize=8)
    
    # Contour fill for vorticity with the fixed colormap
    vort_plot = plt.contourf(lons_sub, lats_sub, vort500_clipped, 
                            levels=vort_levels, cmap=cmap, extend="both", transform=ccrs.PlateCarree(), alpha=.8)
    
    # Add Gridlines
    gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
    gl.top_labels = False  # Hide top labels for cleaner look
    
    # Add Color Bar
    cbar = plt.colorbar(vort_plot, orientation="horizontal", pad=0.05, aspect=50)
    cbar.set_label("Absolute Vorticity (10⁻⁵ s⁻¹)")
    
    # Add Title
    plt.title(f"GFS 500 mb Heights & Vorticity\nRun: {run_time} | Forecast Hour: {forecast_hour}h", fontsize=14)
    
    filepath = f"{os.getcwd()}/images/500mb/height_vorticity/{today}/{model_run}/{hour}_hour.png"
    create_directory(filepath)
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close()
    if local_run is False:
        write_to_s3(filepath, today, model_run, "500mb")
