from .utils import (
    get_dataset,
    get_lat_lons,
    get_plot,
    create_mslp_contours,
    create_thickness_contours,
    add_mslp_systems,
    create_precip_rate_colormap,
    get_thickness_data,
    get_mslp,
    get_precip_rate,
    plot_title,
    write_model_image
)


def generate_surface_image(hour, grib_file, today, model_run, lat_rng, lon_rng, local_run):
    """ Generate MSLP, Thickness, and Precipitation images """
    thickness = get_thickness_data(grib_file, lat_rng, lon_rng)
    mslp = get_mslp(grib_file, lat_rng, lon_rng)
    prate = get_precip_rate(grib_file, lat_rng, lon_rng)
    lats, lons = get_lat_lons(mslp)
    _, ax = get_plot(lat_rng, lon_rng)
    create_mslp_contours(ax, mslp)
    create_thickness_contours(ax, thickness)
    add_mslp_systems(ax, mslp, lats, lons, lat_rng, lon_rng)
    create_precip_rate_colormap(ax, prate)
    ds = get_dataset(grib_file)
    plot_title(ds, "1000-500mb Thickness, Precip Rate, MSLP")
    write_model_image(today, model_run, hour, local_run,  "surface", "mslp_thickness_precip")
