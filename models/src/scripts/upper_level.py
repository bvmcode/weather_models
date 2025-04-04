from .utils import (
    get_dataset,
    get_filtered_data,
    get_lat_lons,
    get_plot,
    plot_title,
    write_model_image,
    plot_wind_barbs,
    height_plot,
    plot_wind_contours,
)

def generate_height_and_wind_images(hour, grib_file, today, model_run, lat_rng, lon_rng, local_run):
    ds = get_dataset(grib_file)
    for level in ["200", "300", "500", "700", "850"]:
        h = get_filtered_data(ds, level, "gh", lat_rng, lon_rng)
        lats, lons = get_lat_lons(h)
        u, v = get_filtered_data(ds, level, "wind", lat_rng, lon_rng)
        _, ax = get_plot(lat_rng, lon_rng)
        height_plot(h, lats, lons, ax)
        plot_wind_contours(u, v, lats, lons, ax)
        plot_wind_barbs(u, v, lats, lons, ax)
        plot_title(ds, f"{level} mb Heights, Wind Speed & Wind Barbs")
        write_model_image(today, model_run, hour, local_run, f"{level}mb", "height_wind")
