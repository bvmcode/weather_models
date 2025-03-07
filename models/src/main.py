from datetime import datetime
import os

from scripts.utils import get_file
from scripts import mb500, sfc


def main(model_run, hour):
    today = datetime.now().strftime("%Y%m%d")
    filepath = get_file(model_run, today, hour)
    sfc.generate_surface_image(hour, filepath, today, model_run)
    mb500.generate_height_and_vorticity_image(hour, filepath, today, model_run)


if __name__ == "__main__":
    hour = os.getenv("HOUR")
    model_run = os.getenv("MODEL_RUN")
    main(model_run, hour)
