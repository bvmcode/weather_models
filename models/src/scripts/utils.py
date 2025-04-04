import os
from datetime import datetime
import requests
import boto3
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
import numpy as np
from scipy.ndimage import zoom
from matplotlib.colors import LinearSegmentedColormap, Normalize


def create_directory(filepath):
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_file(model_run, date, hour):
    url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date}/{model_run}/atmos/gfs.t{model_run}z.pgrb2.0p25.f{hour}"
    filepath = f"{ os.getcwd()}/data/{date}/{model_run}/gfs_{hour}.grib2"
    create_directory(filepath)
    data = requests.get(url)
    with open(filepath, 'wb') as f:
        f.write(data.content)
    return filepath


def write_to_s3(filepath, today, model_run, level, plot_type):
    s3_client = boto3.client("s3")
    bucket_name = os.getenv("BUCKET_NAME")
    filename = os.path.basename(filepath)
    s3_key = f"gfs_images/{today}/{model_run}/{level}/{plot_type}/{filename}"
    s3_client.upload_file(filepath, bucket_name, s3_key)


def save_plot(plt, model_run, hour, level, plot_type):
    today = datetime.now().strftime("%Y%m%d")
    filepath = f"{os.getcwd()}/images/{level}/{plot_type}/{today}/{model_run}/{hour}_hour.png"
    create_directory(filepath)
    plt.savefig(filepath, dpi=200, bbox_inches="tight")
    plt.close()
    return filepath


def convert_lat_lon(ds):
    # Convert longitudes from 0-360 to -180 to 180 if needed
    if ds.longitude.max() > 180:
        ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360 - 180))
        ds = ds.sortby("longitude")
    return ds


def filter_ds(ds, level, extent):
    ds = ds.sel(isobaricInhPa=level)
    return ds.where((ds.latitude >= extent[2]) & (ds.latitude <= extent[3]) &
                    (ds.longitude >= extent[0]) & (ds.longitude <= extent[1]), drop=True)


def get_dataset(grib_file):
    ds = xr.open_dataset(grib_file, engine="cfgrib", filter_by_keys={"typeOfLevel":"isobaricInhPa"})
    if ds.longitude.max() > 180:
        ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360 - 180))
        ds = ds.sortby("longitude")
    return ds


def get_filtered_data(ds, level, field, lat_rng, lon_rng, multiplier=1):
    ds = ds.sel(isobaricInhPa=level).where((ds.latitude>=lat_rng[0]) & (ds.latitude<=lat_rng[1]) &
                                             (ds.longitude>=lon_rng[0]) & (ds.longitude<=lon_rng[1]), drop=True)
    if field == "dew_point":
        T = ds["t"]  # Temperature (K)
        q = ds["q"]  # Specific Humidity (kg/kg)
        e = (q * level) / (0.622 + q) # Compute Vapor Pressure (hPa)
        # Compute Dew Point (Celsius)
        dpt = (243.5 * (np.log(e) - np.log(6.112))) / (17.67 - (np.log(e) - np.log(6.112)))
        return dpt[::2, ::2]
    if field == "wind":
        u = ds["u"] * 1.94384  # Convert U-wind to knots
        v = ds["v"] * 1.94384  # Convert V-wind to knots
        return u[::2, ::2], v[::2, ::2]
    data = ds[field]*multiplier
    data = data.sel(latitude=slice(lat_rng[1], lon_rng[0]), longitude=slice(lon_rng[0], lon_rng[1]))
    return data[::2, ::2]
    

def get_plot(lat_rng, lon_rng):
    fig = plt.figure(figsize=(14, 9))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([lon_rng[0], lon_rng[1], lat_rng[0], lat_rng[1]], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, lw=1)
    ax.add_feature(cfeature.BORDERS, ls=":")
    ax.add_feature(cfeature.STATES, ls="--")
    return fig, ax

def get_lat_lons(field):
    lons = field.longitude.values
    lats = field.latitude.values
    return lats, lons

def vorticity_plot(vort, lats, lons, ax):
    vort = np.clip(vort, -5, 55)
    # Define Custom Colormap to Match Reference Image
    cmap_colors = [
        # (-40, (0.4, 0.4, 0.4)),  # Dark gray
        (0.6, 0.6, 0.6),  # Medium gray
        (0.8, 0.8, 0.8),  # Light gray
        (1.0, 1.0, 1.0),   # White (neutral)
        (1.0, 0.9, 0.5),    # Light yellow
        (1.0, 0.6, 0.2),   # Orange
        (0.9, 0.1, 0.1),   # Red
        (0.6, 0.0, 0.6)    # Purple
    ]
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_vort", cmap_colors, N=512)

    # Define color levels for smooth transitions
    vort_levels = np.linspace(-5, 55, 20)  # Adjust minimum threshold to 5 instead of -40
    
    # Define color breakpoints (must match the values in cmap_colors)
    vort_boundaries = [-5, 0, 10, 20, 35, 55]
    
    # Create a colormap and a norm that maps values to color intervals
    cmap = mcolors.ListedColormap(cmap_colors, name="custom_vort")
    norm = mcolors.BoundaryNorm(boundaries=vort_boundaries, ncolors=cmap.N, extend="both")

    vort_plot = plt.contourf(
        lons, lats, vort,
        levels=vort_boundaries,
        cmap=cmap,
        norm=norm,
        extend="both",
        transform=ccrs.PlateCarree(),
        alpha=0.8
    )
    cbar = plt.colorbar(vort_plot, orientation="horizontal", pad=0.05, aspect=50)
    cbar.set_label("Absolute Vorticity (10⁻⁵ s⁻¹)")


    
def height_plot(gh, lats, lons, ax):
    #contour_levels = np.arange(h500_min, h500_max + 60, 60)
    contour_levels = np.arange(gh.min(), gh.max(), 60)

    # Contour plot for 500 mb Heights
    contour = ax.contour(lons, lats, gh, 
                        levels=contour_levels, colors="black", linewidths=1, transform=ccrs.PlateCarree())
    
    ax.clabel(contour, fmt="%d", inline=True, fontsize=8)
    
    # Add Gridlines
    gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
    gl.top_labels = False  # Hide top labels for cleaner look

    
def write_model_image(today, model_run, hour, local_run, level, plot_type):
    filepath = f"{os.getcwd()}/images/{level}/{plot_type}/{today}/{model_run}/{hour}_hour.png"
    create_directory(filepath)
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close()
    if local_run is False:
        write_to_s3(filepath, today, model_run, level, plot_type)

def plot_title(ds, desc):
    run_time = pd.to_datetime(str(ds.time.values)).strftime('%Y-%m-%d: %HZ')# Model initialization time
    forecast_hour = ds.step.values.astype('timedelta64[h]').astype(int)  # Convert to hours
    title = f"GFS {desc}\nRun: {run_time} | Forecast Hour: {forecast_hour}h"
    plt.title(title, fontsize=14)


def plot_wind_barbs(u, v, lats, lons, ax):
    # Reduce Wind Barb Density (Interpolation Method)
    barb_density = 0.15  # Same density as RH version
    interp_u = zoom(u.values, barb_density)
    interp_v = zoom(v.values, barb_density)
    interp_lons = zoom(lons, barb_density)
    interp_lats = zoom(lats, barb_density)

    # Remove Very Weak Winds (<5 knots) to Avoid Circles
    mask = np.sqrt(interp_u**2 + interp_v**2) > 5  # Wind speeds in knots
    interp_u = np.where(mask, interp_u, np.nan)
    interp_v = np.where(mask, interp_v, np.nan)

    ax.barbs(interp_lons, interp_lats, interp_u, interp_v, 
                length=5, linewidth=0.7, color="black", transform=ccrs.PlateCarree())

def plot_dew_point(level, dpt, lons, lats, ax):
    # Define Colormap for Dew Point (blue/green for moisture)
    cmap_dpt = mcolors.LinearSegmentedColormap.from_list("dpt_cmap", [
        (0.0, "#8B4513"),   # Dry (Brown) - Lowest
        (0.3, "#A9A9A9"),   # Mid-range (Gray)
        (0.5, "#2E8B57"),   # Humid (Green)
        (0.7, "#00BFFF"),   # Very Humid (Light Blue)
        (1.0, "#0000FF")    # Tropical Air (Deep Blue) - Highest
    ], N=256)

    # Dew Point shading
    dpt_levels = np.linspace(-30, 25, 50)  # 50 levels for smooth shading
    dpt_plot = ax.contourf(lons, lats, dpt, levels=dpt_levels,
                           cmap=cmap_dpt, extend="both", transform=ccrs.PlateCarree())

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
    gl.top_labels = False

    # Add color bar
    cbar = plt.colorbar(dpt_plot, orientation="horizontal", pad=0.05, aspect=50)
    cbar.set_label(f"{level} Dew Point (°C)")


def plot_rh(level, rh, lons, lats, ax):
    # Define colormap for RH shading (matching Pivotal Weather)
    cmap_rh = mcolors.LinearSegmentedColormap.from_list("rh_cmap", [
        (0.0, "#8B4513"),  # Brown for dry air
        (0.5, "#A9A9A9"),  # Gray for mid-range RH
        (1.0, "#006400")   # Dark green for very moist air
    ], N=256)

    # RH shading
    rh_levels = np.linspace(0, 100, 50)  # 50 levels for smooth shading
    rh_plot = ax.contourf(lons, lats, rh, levels=rh_levels,
                          cmap=cmap_rh, extend="both", transform=ccrs.PlateCarree())

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
    gl.top_labels = False

    # Add color bar
    cbar = plt.colorbar(rh_plot, orientation="horizontal", pad=0.05, aspect=50)
    cbar.set_label(f"{level} Relative Humidity (%)")


def plot_wind_contours(u, v, lats, lons, ax):
    # Wind speed magnitude (kt)
    wspd = np.sqrt(u**2 + v**2)
    # Dynamically adjust wind scale from 50 to dataset max
    wspd_max = float(wspd.max())  
    wspd_min = 20  # Start shading at 50 knots
    # Wind Speed Colormap (Better Match to Reference Image)
    cmap_wind = LinearSegmentedColormap.from_list("wind_cmap", [
        (0.0, "white"),      # 50 knots - Light winds
        (0.15, "lightblue"),  # 80 knots
        (0.30, "deepskyblue"),  # 100 knots
        (0.50, "blue"),       # 120 knots
        (0.65, "purple"),     # 140 knots
        (0.80, "red"),        # 160 knots
        (0.90, "orange"),     # 180 knots
        (1.0, "yellow")       # Max wind - Strongest jet streaks
    ])

    # Normalize wind speeds **from 50 to dataset max**
    norm = Normalize(vmin=wspd_min, vmax=wspd_max)

    # Wind Shading (More Color Levels for Smoother Gradients)
    wind_plot = plt.contourf(lons, lats, wspd,
                            levels=np.linspace(wspd_min, wspd_max, 100),  # **100 levels for smoother transition**
                            cmap=cmap_wind, norm=norm, extend="both",
                            transform=ccrs.PlateCarree())

    # Add color bar
    cbar = plt.colorbar(wind_plot, orientation="horizontal", pad=0.05, aspect=50, alpha=.5)
    cbar.set_label("Wind Speed (kt)")