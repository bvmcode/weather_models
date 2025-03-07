import os
from datetime import datetime
import requests
import boto3


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


def write_to_s3(filepath, today, model_run, cat):
    s3_client = boto3.client("s3")
    bucket_name = "bvm-wx-models"
    filename = os.path.basename(filepath)
    s3_key = f"gfs_images/{today}/{model_run}/{cat}/{filename}"
    s3_client.upload_file(filepath, bucket_name, s3_key)


def save_plot(plt, model_run, i, hour, level, plot_type):
    today = datetime.now().strftime("%Y%m%d")
    filepath = f"{os.getcwd()}/images/{level}/{plot_type}/{today}/{model_run}/{i}_hour_{hour}.png"
    create_directory(filepath)
    plt.savefig(filepath, dpi=200, bbox_inches="tight")
    plt.close()


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
