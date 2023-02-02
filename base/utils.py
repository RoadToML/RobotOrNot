import base64
from PIL import Image
from datetime import datetime
import os
import io
import random
import json
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import boto3
import requests
import shutil

with open(".env", "r") as f:
    config = json.loads(f.read())
    STABILITY_HOST = config["STABILITY_HOST"]
    STABILITY_KEY = config["STABILITY_KEY"]
    AWS_SECRET_KEY = config["AWS_SECRET_KEY"]
    AWS_ACCESS_KEY_ID = config["AWS_ACCESS_KEY_ID"]


def get_image_from_SD_api(prompt: str):
    session = boto3.Session()
    s3 = boto3.client(
        "s3", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY
    )

    stability_api = authenticate_stability_api()
    answers = stability_api.generate(prompt=prompt, seed=69420, width=512, height=512)

    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                # change prompt
                get_image_from_SD_api(prompt=prompt)
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = io.BytesIO(artifact.binary)

                s3.put_object(
                    Body=img,
                    Bucket="neural-puzzle-turdle",
                    Key=f"static/images/{str(int(datetime.now().timestamp())) + '_ai_.png'}",
                )

                # img.save(
                #     os.path.join(
                #         "static",
                #         "images",
                #         f"{int(datetime.now().timestamp())}" + "_ai_.png",
                #     )
                # )  # Save our generated images with their seed number as the filename.


def authenticate_stability_api():
    stability_api = client.StabilityInference(
        key=STABILITY_KEY,  # API Key reference.
        verbose=True,  # Print debug messages.
        engine="stable-diffusion-512-v2-0",  # Set the engine to use for generation.
        # Available engines: stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
        # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-inpainting-v1-0 stable-inpainting-512-v2-0
    )

    return stability_api


def saved_image_over_24h():
    img_files = get_list_of_images_s3()
    img_files.sort(reverse=True)
    return int(img_files[0].split("_")[0]) + 86400 < datetime.now().timestamp()


def get_latest_image_path():
    images = get_list_of_images_s3()
    images.sort(reverse=True)
    return f"static/images/{images[0]}"


def get_list_of_images_s3():
    s3 = boto3.client(
        "s3", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY
    )
    my_bucket = s3.list_objects_v2(
        Bucket="neural-puzzle-turdle", Prefix="static/images/"
    )
    image_names = []
    for my_bucket_object in my_bucket["Contents"]:
        file_key = my_bucket_object["Key"].split("/")
        if len(file_key) == 3:
            image_names.append(file_key[-1])

    return image_names


def get_prompt():
    with open(os.path.join("base", "prompts.txt"), "r") as f:
        all_prompts = f.readlines()
        len_prompts = len(all_prompts)

    random_idx = random.randint(0, len_prompts - 1)
    prompt = all_prompts.pop(random_idx).strip()

    with open(os.path.join("base", "prompts.txt"), "w") as f:
        for line in all_prompts:
            f.write(line)

    return prompt


def get_human_image():
    with open(".env", "r") as f:
        config = json.loads(f.read())
        api_key = config["API_NINJA"]

    api_url = "https://api.api-ninjas.com/v1/randomimage"
    response = requests.get(
        api_url, headers={"X-Api-Key": api_key, "Accept": "image/jpg"}, stream=True
    )
    print(response.status_code, requests.codes.ok)
    if response.status_code == requests.codes.ok:
        filename = f"{int(datetime.now().timestamp())}" + "_human_.png"
        with open(filename, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)

        session = boto3.Session()
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_KEY,
        )

        with open(filename, "rb") as img_byte_arr:
            s3.put_object(
                Body=bytearray(img_byte_arr.read()),
                Bucket="neural-puzzle-turdle",
                Key=f"static/images/{str(int(datetime.now().timestamp())) + '_human_.png'}",
            )

        os.remove(filename)

        return 200
    else:
        return None
