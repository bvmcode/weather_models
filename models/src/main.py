import os
import sys

from scripts.utils import get_file
from scripts import mb500, sfc, mb850, upper_level


def main(model_run, hour, local_run, date):
    filepath = get_file(model_run, date, hour)
    lat_rng = [5, 75]
    lon_rng = [-160, -40]
    fncs = [
        mb500.generate_height_and_vorticity_image,
        sfc.generate_surface_image,
        mb850.generate_rh_image,
        mb850.generate_dew_point_image,
        upper_level.generate_height_and_wind_images,
    ]
    for fnc in fncs:
        fnc(hour, filepath, date, model_run, lat_rng, lon_rng, local_run)


if __name__ == "__main__":
    hour = os.getenv("MODEL_FORECAST_HOUR")
    model_run = os.getenv("MODEL_RUN")
    date = os.getenv("MODEL_RUN_DATE")
    local_run = False
    try:
        if sys.argv[1]=="local":
            local_run = True
    except:
        pass
    main(model_run, hour, local_run, date)
