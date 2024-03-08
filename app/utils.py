import uuid
from pathlib import PurePath

import httpx
from PIL import Image
from pydantic import DirectoryPath

from app import settings


def gen_uuid(return_type: str = 'str') -> str | int:
    match return_type:
        case 'str':
            uid = str(uuid.uuid4())
        case "int":
            uid = uuid.uuid4().int
        case "hex":
            uid = uuid.uuid4().hex
        case _:
            uid = uuid.uuid4().hex

    return uid


def split_image(image_file):
    with Image.open(image_file) as im:
        # Get the width and height of the original image
        width, height = im.size
        # Calculate the middle points along the horizontal and vertical axes
        mid_x = width // 2
        mid_y = height // 2
        # Split the image into four equal parts
        top_left = im.crop((0, 0, mid_x, mid_y))
        top_right = im.crop((mid_x, 0, width, mid_y))
        bottom_left = im.crop((0, mid_y, mid_x, height))
        bottom_right = im.crop((mid_x, mid_y, width, height))

        return top_left, top_right, bottom_left, bottom_right


async def download_image(
        url: str,
        directory: DirectoryPath,
        filename: str,
        is_split: bool = False,
):
    response = httpx.get(url, timeout=settings.httpx_timeout, proxies={
        "http://": settings.proxy_url,
        "https://": settings.proxy_url
    })
    # response = requests.get(url, timeout=settings.httpx_timeout)
    response.raise_for_status()
    if response.status_code == 200:

        output_folder = directory.joinpath('assets', 'output')
        if not output_folder.exists():
            output_folder.mkdir(parents=True, exist_ok=True)
        input_folder = directory.joinpath('assets', 'input')
        if not input_folder.exists():
            input_folder.mkdir(parents=True, exist_ok=True)
        with open(directory.joinpath(input_folder, filename), "wb+") as f:
            f.write(response.content)
        print(f"Image downloaded: {filename}")

        input_file = directory.joinpath(input_folder, filename)

        # if "UPSCALED_" not in filename:
        if is_split:
            # file_prefix = os.path.splitext(filename)[0]
            file_prefix = PurePath(filename).stem
            file_suffix = PurePath(filename).suffix
            # Split the image
            top_left, top_right, bottom_left, bottom_right = split_image(input_file)
            # Save the output images with dynamic names in the output folder
            top_left.save(directory.joinpath(output_folder, f"{file_prefix}_top_left{file_suffix}"))
            top_right.save(directory.joinpath(output_folder, f"{file_prefix}_top_right{file_suffix}"))
            bottom_left.save(directory.joinpath(output_folder, f"{file_prefix}_bottom_left{file_suffix}"))
            bottom_right.save(directory.joinpath(output_folder, f"{file_prefix}_bottom_right{file_suffix}"))

        else:
            # Rename the input file
            ...
            # directory.joinpath(input_folder, filename).rename(directory.joinpath(output_folder, filename))
        # Delete the input file
        # directory.joinpath(input_folder, filename).unlink()


if __name__ == '__main__':
    print(gen_uuid(return_type="str"))
    print(gen_uuid(return_type="hex"))
    print(gen_uuid(return_type="int"))

    download_image(
        "https://cdn.discordapp.com/attachments/1076097007850111020/1215298059882463252/xhcyw2_test_da8197c7-b78c-4518-9daa-c48c42906925.png?ex=65fc3d84&is=65e9c884&hm=f7a3f4afd279dbcf87942424e347f0a3cf7a28aabcbefb44667bf91b7e9d14ab&",
        directory=settings.project_dir.joinpath('assets'),
        filename="xhcyw2_test_da8197c7-b78c-4518-9daa-c48c42906925.png"
    )
