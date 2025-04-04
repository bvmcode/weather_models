from .utils import (
    get_dataset,
    get_filtered_data,
    get_lat_lons,
    get_plot,
    plot_title,
    write_model_image,
    height_plot,
    vorticity_plot,
)

def generate_height_and_vorticity_image(
    hour, grib_file, today, model_run, lat_rng, lon_rng, local_run
):
    ds = get_dataset(grib_file)
    h500 = get_filtered_data(ds, 500, "gh", lat_rng, lon_rng)
    vort500 = get_filtered_data(ds, 500, "absv", lat_rng, lon_rng, multiplier=1e5)
    lats, lons = get_lat_lons(h500)
    _, ax = get_plot(lat_rng, lon_rng)
    height_plot(h500, lats, lons, ax)
    vorticity_plot(vort500, lats, lons, ax)
    plot_title(ds, "500 mb Heights & Vorticity")
    write_model_image(today, model_run, hour, local_run, "500mb", "height_vorticity")
