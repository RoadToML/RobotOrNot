from django.shortcuts import render

from datetime import datetime
from dateutil import parser

import random
from . import utils

# Create your views here.
def index(request):
    # utils.get_list_of_images_s3()
    if request.method == "GET":
        time_start = datetime.now()
        request.session["time_start"] = str(time_start)

    img_src = (
        f"https://neural-puzzle-turdle.s3.amazonaws.com/{utils.get_latest_image_path()}"
    )

    if utils.saved_image_over_24h():
        if random.randint(0, 1) == 0:
            utils.get_image_from_SD_api(prompt=utils.get_prompt())
        else:
            success = utils.get_human_image()
            if not success:
                utils.get_image_from_SD_api(prompt=utils.get_prompt())

    if request.method == "POST":
        time_start = parser.parse(request.session["time_start"])
        time_finish = datetime.now()

        time_delta = time_finish - time_start
        difference = divmod(time_delta.total_seconds(), 60)
        diff = {"min": round(difference[0], 0), "sec": round(difference[1], 2)}

        selection = request.POST.get("option")
        y_true = img_src.split("/")[-1].split("_")[-2]

        context = {
            "img_src": img_src,
            "diff": diff,
            "option": selection,
            "y_true": y_true,
        }
        return render(request, "base/results.html", context)

    context = {"img_src": img_src}
    return render(request, "base/home.html", context)
