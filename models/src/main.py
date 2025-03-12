from datetime import datetime
import os
import sys

from scripts.utils import get_file
from scripts import mb500, sfc


def main(model_run, hour, local_run):
    today = datetime.now().strftime("%Y%m%d")
    filepath = get_file(model_run, today, hour)
    sfc.generate_surface_image(hour, filepath, today, model_run, local_run)
    mb500.generate_height_and_vorticity_image(hour, filepath, today, model_run, local_run)


if __name__ == "__main__":
    hour = os.getenv("HOUR")
    model_run = os.getenv("MODEL_RUN")
    local_run = False
    try:
        if sys.argv[1]=="local":
            local_run = True
    except:
        pass
    main(model_run, hour, local_run)
