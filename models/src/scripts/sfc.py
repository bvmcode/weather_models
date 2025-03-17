import os
from datetime import datetime

import matplotlib.lines as mlines
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature

import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage import gaussian_filter, maximum_filter, minimum_filter
from .utils import create_directory, write_to_s3

SIGMA = 1.5
LON_MIN = -160
LON_MAX = -40
LAT_MIN = 5
LAT_MAX = 75


def get_data(file_path, field, level_type=None, step_type=None):
    filter_by_keys = {"shortName": field}
    if level_type:
        filter_by_keys["typeOfLevel"] = level_type
    if step_type:
        filter_by_keys["stepType"] = step_type
    ds = xr.open_dataset(file_path, engine='cfgrib', filter_by_keys=filter_by_keys)
    # Ensure longitude is in the range 0 to 360 if needed
    if ds.longitude.max() > 180:
        ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360 - 180))
    return ds.sel(latitude=slice(LAT_MAX, LAT_MIN), longitude=slice(LON_MIN, LON_MAX))

def get_times(file_path):
    ds = get_data(file_path, field="prmsl")
    run_time = pd.to_datetime(str(ds.time.values)).strftime('%Y-%m-%d: %HZ')
    forecast_hour = ds.step.values.astype('timedelta64[h]').astype(int)
    return run_time, forecast_hour

# def get_temperature_data(file_path):
#     """Retrieve 2m and 850mb temperature data"""
#     ds_temp = get_data(file_path, field="2t", step_type="instant")  # 2m temperature
#     ds_temp850 = get_data(file_path, field="t", level_type="isobaricInhPa")
#     t2m = ds_temp["t2m"] - 273.15  # Convert to Celsius
#     t850 = ds_temp850.sel(isobaricInhPa=850)["t"] - 273.15  # Convert to Celsius
#     return t2m, t850

def get_thickness_data(file_path):
    ds_geopotential = get_data(file_path, field="gh", level_type="isobaricInhPa")
    geopotential_1000mb = ds_geopotential['gh'].sel(isobaricInhPa=1000)
    geopotential_500mb = ds_geopotential['gh'].sel(isobaricInhPa=500)
    thickness = geopotential_500mb - geopotential_1000mb
    return thickness, gaussian_filter(thickness, sigma=SIGMA)


def get_mslp(file_path, sigma):
    ds_mslp = get_data(file_path, field="prmsl")
    mslp = ds_mslp['prmsl'] / 100  # Convert from Pa to hPa
    return mslp, gaussian_filter(mslp, sigma=sigma)


def get_precip(file_path):
    ds_precip = get_data(file_path, field="prate", step_type="instant")
    prate = ds_precip['prate']
    return prate



def get_data_times(file_path, model_run):
    ds = get_data(file_path, field="gh", level_type="isobaricInhPa")
    timestamp = pd.to_datetime(ds.time.values)
    valid_time = timestamp.strftime("%Y-%m-%d %HZ")
    return valid_time, model_run


def create_mslp_contours(ax, field, field_smooth, colors, fontsize=8, linestyle="-", linewidth=1, contour_interval=6):
    """ Create contours with proper spacing """
    contour_levels = np.arange(field.min(), field.max(), contour_interval)
    contour = ax.contour(field.longitude, field.latitude, field_smooth,
                         levels=contour_levels, colors=colors, linewidths=linewidth, linestyles=linestyle, transform=ccrs.PlateCarree())
    ax.clabel(contour, fmt='%d', colors=colors, fontsize=fontsize)
    return contour

def create_thickness_contours(ax, field, field_smooth, fontsize=8, linestyle="-", linewidth=1, contour_interval=6):
    """ Create contours with different colors for specific values (e.g., 540 dm in blue) """
    contour_levels = np.arange(field.min(), field.max(), contour_interval)

    # Define a color mapping function
    def get_color(level):
        return "blue" if level <= 5400 else "red"

    # Plot each contour level separately
    for level in contour_levels:
        contour = ax.contour(field.longitude, field.latitude, field_smooth,
                             levels=[level], colors=get_color(level),
                             linewidths=linewidth, linestyles=linestyle,
                             transform=ccrs.PlateCarree())
        ax.clabel(contour, fmt='%d', colors=get_color(level), fontsize=fontsize)
    
    return contour


def create_precip_rate_colormap(ax, field, levels=25):
    """ Create precipitation shading """
    radar_cmap = plt.get_cmap('gist_ncar', 50)  # Use 'gist_ncar' for smooth shading
    colors = radar_cmap(np.linspace(0, 1, radar_cmap.N))
    colors[0] = [1, 1, 1, 0]  # Transparent for lowest value
    custom_cmap = ListedColormap(colors)
    levels_rng = np.linspace(.0001, field.values.max(), levels)
    contourf = ax.contourf(field.longitude, field.latitude, field.values,alpha=.5,
                           levels=levels_rng, cmap=custom_cmap, transform=ccrs.PlateCarree())
    return contourf


def set_geography(ax):
    """ Set map boundaries and overlays """
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.STATES, linewidth=0.5)


def add_legend(ax, color_fields, color_labels, contour_labels, contour_label_colors):
    """ Add legend for precipitation, thickness, and MSLP """
    for field, label in zip(color_fields, color_labels):
        cbar = plt.colorbar(field, ax=ax, orientation='horizontal', pad=0.1, aspect=50)
        cbar.set_label(label, fontsize=10)
    handles = []
    for label, color in zip(contour_labels, contour_label_colors):
        handle = mlines.Line2D([], [], color=color, label=label)
        handles.append(handle)
    ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.12), ncol=len(contour_labels), fontsize=10)



def add_mslp_systems(ax, lons, lats, data, size, system):
    """ Adds Highs (H) and Lows (L) to the plot without placing them too close to the edges. """
    
    if system == 'H':
        data_ext = maximum_filter(data, size, mode='nearest')
        color = 'b'
    else:
        data_ext = minimum_filter(data, size, mode='nearest')
        color = 'r'

    mxy, mxx = np.where(data_ext == data)

    # Define boundary limits for placing labels (avoid edges)
    lon_min, lon_max = LON_MIN + 2, LON_MAX - 2  # Adjust these values if needed
    lat_min, lat_max = LAT_MIN + 2, LAT_MAX - 2

    for i in range(len(mxy)):    
        lon_value = lons[mxx[i]]
        lat_value = lats[mxy[i]]

        # Ensure labels are placed within safe bounds
        if lon_min <= lon_value <= lon_max and lat_min <= lat_value <= lat_max:
            ax.text(lon_value, lat_value, system, color=color, size=24,
                    clip_on=True, horizontalalignment='center', verticalalignment='center',
                    transform=ccrs.PlateCarree())
            ax.text(lon_value, lat_value,
                    '\n' + str(np.int64(data[mxy[i], mxx[i]])),
                    color=color, size=12, clip_on=True, fontweight='bold',
                    horizontalalignment='center', verticalalignment='top', transform=ccrs.PlateCarree())


def generate_surface_image(hour, grib_file, today, model_run, local_run):
    """ Generate MSLP, Thickness, and Precipitation images """
    thickness_1000_500mb, thickness_smooth = get_thickness_data(grib_file)
    mslp, mslp_smooth = get_mslp(grib_file, 1.5)
    _, mslp_smooth_high_low = get_mslp(grib_file, .8)
    precip_rate = get_precip(grib_file)

    fig, ax = plt.subplots(figsize=(18, 12), subplot_kw={'projection': ccrs.PlateCarree()})
    set_geography(ax)

    create_thickness_contours(ax, thickness_1000_500mb, thickness_smooth, linestyle="dashed", contour_interval=60)
    create_mslp_contours(ax, mslp, mslp_smooth, colors="black", linewidth=.8, contour_interval=2)
    precip_contourf = create_precip_rate_colormap(ax, precip_rate)
    
    add_mslp_systems(ax, mslp.longitude, mslp.latitude, mslp_smooth_high_low, 50, 'H')
    add_mslp_systems(ax, mslp.longitude, mslp.latitude, mslp_smooth_high_low, 50, 'L')

    run_time, forecast_hour = get_times(grib_file)
    cbar = fig.colorbar(precip_contourf,  orientation='horizontal', pad=0.05, aspect=50)
    cbar.set_label("Precipitation Rate (mm/hr)", fontsize=12)

    plt.title(f"GFS 1000-500mb Thickness, Precip Rate, MSLP \nRun: {run_time} | Forecast Hour: {forecast_hour}h", fontsize=14)
    filepath = f"{os.getcwd()}/images/surface/{datetime.now().strftime('%Y%m%d')}/{model_run}/{hour}_hour.png"
    create_directory(filepath)
    
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close()

    if local_run is False:
        write_to_s3(filepath, today, model_run, "sfc", "mslp_thickness_precip")
