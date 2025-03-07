import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize

from .utils import convert_lat_lon, filter_ds, save_plot


def generate_height_and_wind_images(levels, hours, grib_files, model_run, extent):
    for level in levels:
        for i, (hour, grib_file) in enumerate(zip(hours, grib_files)):
            ds = xr.open_dataset(grib_file, engine="cfgrib", filter_by_keys={'typeOfLevel': 'isobaricInhPa'})
            ds = convert_lat_lon(ds)
            ds = filter_ds(ds, level, extent)

            h = ds["gh"]
            u = ds["u"]
            v = ds["v"]

            # Wind speed magnitude (kt)
            wspd = np.sqrt(u**2 + v**2)

            # Dynamically adjust wind scale from 50 to dataset max
            wspd_max = float(wspd.max())  
            wspd_min = 20  # Start shading at 50 knots

            _, ax = plt.subplots(figsize=(14, 9), subplot_kw={'projection': ccrs.PlateCarree()})

            ax.set_extent(extent, crs=ccrs.PlateCarree())

            ax.add_feature(cfeature.COASTLINE, linewidth=1)
            ax.add_feature(cfeature.BORDERS, linestyle=":")
            ax.add_feature(cfeature.STATES, linestyle="--", edgecolor="gray")

            # Reduce resolution slightly for performance
            h_sub = h[::2, ::2]
            wspd_sub = wspd[::2, ::2]

            # Reduce wind barbs density (plot every 10th point)
            u_sub = u[::15, ::15]  
            v_sub = v[::15, ::15]

            lons_sub = h_sub.longitude.values
            lats_sub = h_sub.latitude.values
            barb_lons = u_sub.longitude.values
            barb_lats = u_sub.latitude.values

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

            # Contour Levels for Better Clarity (60m spacing)
            contour_levels = np.arange(h_sub.min(), h_sub.max(), 60)  # Every 60m

            # Wind Shading (More Color Levels for Smoother Gradients)
            wind_plot = plt.contourf(lons_sub, lats_sub, wspd_sub,
                                    levels=np.linspace(wspd_min, wspd_max, 100),  # **100 levels for smoother transition**
                                    cmap=cmap_wind, norm=norm, extend="both",
                                    transform=ccrs.PlateCarree())

            # PLOT 300mb HEIGHTS (With Fewer Contours)
            contour = plt.contour(lons_sub, lats_sub, h_sub,
                                levels=contour_levels, colors="black", linewidths=1,
                                transform=ccrs.PlateCarree())

            plt.clabel(contour, fmt="%d", inline=True, fontsize=8)

            # add wind barbs
            ax.barbs(barb_lons, barb_lats, u_sub.values, v_sub.values, 
                    length=5, linewidth=0.7, color="black", transform=ccrs.PlateCarree())

            # Add color bar
            cbar = plt.colorbar(wind_plot, orientation="horizontal", pad=0.05, aspect=50, alpha=.5)
            cbar.set_label("Wind Speed (kt)")

            run_time = pd.to_datetime(str(ds.time.values)).strftime('%Y-%m-%d: %HZ')
            forecast_hour = ds.step.values.astype('timedelta64[h]').astype(int)
            plt.title(f"GFS {level} mb Heights, Wind Speed & Wind Barbs\nRun: {run_time} | Forecast Hour: {forecast_hour}h", fontsize=14)

            save_plot(plt, model_run, i, hour, level=f"{level}mb", plot_type="height_wind")
