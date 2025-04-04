from .utils import (
    get_dataset,
    get_filtered_data,
    get_lat_lons,
    get_plot,
    plot_title,
    write_model_image,
    plot_dew_point,
    plot_rh,
    plot_wind_barbs,
)


def generate_dew_point_image(hour, grib_file, today, model_run, lat_rng, lon_rng, local_run):
    ds = get_dataset(grib_file)
    dp850 = get_filtered_data(ds, 850, "dew_point", lat_rng, lon_rng)
    lats, lons = get_lat_lons(dp850)
    u850, v850 = get_filtered_data(ds, 850, "wind", lat_rng, lon_rng)
    _, ax = get_plot(lat_rng, lon_rng)
    plot_dew_point("850mb", dp850, lons, lats, ax)
    plot_wind_barbs(u850, v850, lats, lons, ax)
    plot_title(ds, "850 mb Dew Point & Wind Barbs")
    write_model_image(today, model_run, hour, local_run, "850mb", "dewpoint")


def generate_rh_image(hour, grib_file, today, model_run, lat_rng, lon_rng, local_run):
    ds = get_dataset(grib_file)
    rh850 = get_filtered_data(ds, 850, "r", lat_rng, lon_rng)
    lats, lons = get_lat_lons(rh850)
    u850, v850 = get_filtered_data(ds, 850, "wind", lat_rng, lon_rng)
    _, ax = get_plot(lat_rng, lon_rng)
    plot_rh("850mb", rh850, lons, lats, ax)
    plot_wind_barbs(u850, v850, lats, lons, ax)
    plot_title(ds, "850 mb Relative Humidity & Wind")
    write_model_image(today, model_run, hour, local_run, "850mb", "rh_wind")