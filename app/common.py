import time
import zipfile
from typing import Optional, Union
import re
import random
import os
import shutil
import string

import requests
import yaml
from requests.auth import HTTPBasicAuth

# Constants for various paths and directories
APP_PACKAGE_TEMPLATE_PATH = "templates/app-package-template"
APP_PACKAGE_WORK_DIR = "tmp"
APP_PACKAGE_RESULTS_DIR = "results"


def app_root_path(app_name: str) -> str:
    return os.path.join(APP_PACKAGE_WORK_DIR, app_name)


def app_results_path(app_name: str) -> str:
    return os.path.join(APP_PACKAGE_RESULTS_DIR, app_name)


def manifest_path(app_name: str) -> str:
    return os.path.join(app_root_path(app_name), "manifest.yaml")


def config_path(app_name: str) -> str:
    return os.path.join(app_root_path(app_name), "config.yaml")


def changelog_path(app_name: str) -> str:
    return os.path.join(app_root_path(app_name), "CHANGELOG.md")


def readme_path(app_name: str) -> str:
    return os.path.join(app_root_path(app_name), "README.md")


def license_path(app_name: str) -> str:
    return os.path.join(app_root_path(app_name), "LICENSE")


def icon_path(app_name: str) -> str:
    return os.path.join(app_root_path(app_name), "assets", "images", "preview_image.png")


def resolve_base_api_url(deployment: str) -> str:
    return f"https://{deployment}-api.sumologic.net/api/"


def get_folder_url(deployment: str, folder_id: str) -> str:
    return f"{resolve_base_api_url(deployment)}v2/content/folders/{folder_id}"


def get_dashboards_url(deployment: str) -> str:
    return f"{resolve_base_api_url(deployment)}v2/dashboards/"


def export_content_url(deployment: str, content_id: str) -> str:
    return f"{resolve_base_api_url(deployment)}v2/content/{content_id}/export"


def get_export_content_status_url(deployment: str, content_id: str, job_id: str) -> str:
    return f"{resolve_base_api_url(deployment)}v2/content/{content_id}/export/{job_id}/status"


def get_export_content_result_url(deployment: str, content_id: str, job_id: str) -> str:
    return f"{resolve_base_api_url(deployment)}v2/content/{content_id}/export/{job_id}/result"


def download_screenshot_endpoint(deployment: str) -> str:
    return f"{resolve_base_api_url(deployment)}v2/dashboards/reportJobs"


def download_screenshot_result_endpoint(deployment: str, job_id: str) -> str:
    return f"{resolve_base_api_url(deployment)}v2/dashboards/reportJobs/{job_id}/result"


def slugify(text: str, replace_char: str = "-") -> str:
    return re.sub('\W+', replace_char, text.strip().lower()).strip(replace_char)


def slugify_name(text):
    # replacing any contiguous sequence of non alphabet(spaces, "_" etc) with underscore `-`
    text = re.sub(r"[ @_!#$%^&*()<>?/\|}{~:`',\\]+", '-', text.strip())
    # replacing any contiguous - with single -
    text = re.sub(r"[-]+", '-', text.strip())

    # remove last -
    text = text.strip("-")
    return text


def auth(access_key: str, access_id: str) -> Optional[HTTPBasicAuth]:
    if access_id and access_key:
        return HTTPBasicAuth(access_id, access_key)
    return None


def random_string(length: int = 6) -> str:
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def format_hex(input_str: str) -> str:
    if len(input_str) == 16 and all(c in '0123456789ABCDEFabcdef' for c in input_str):
        return input_str.upper()
    try:
        num = int(input_str)
    except ValueError:
        return "Invalid input"
    hex_str = hex(num)[2:].upper()
    return hex_str.zfill(16)


def zip_folder(folder_path: str, zip_path: str) -> str:
    if not os.path.exists(folder_path):
        return "Folder does not exist"

    # Get the parent directory and the folder name of the folder to be zipped
    parent_dir, folder_name = os.path.split(folder_path)

    # Create the zip file containing only the root folder inside it
    shutil.make_archive(zip_path, 'zip', root_dir=parent_dir, base_dir=folder_name)

    return f"Folder zipped as {zip_path}.zip"


def read_name_from_yaml(file_path: str) -> Optional[str]:
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data.get("name", None)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def wait_for_job_completion(base_url: str, job_id: str, auth, timeout: int = 180) -> None:
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise Exception(f"Job timed out.")

        status_endpoint = f"{base_url}/{job_id}/status"
        response = None
        try:
            response = requests.get(url=status_endpoint, auth=auth)
            status = response.json()["status"]

            if status.lower() == "success":
                break
            elif status.lower() == "failed":
                raise Exception(f"Job encountered an error {response.content}")

            time.sleep(1)
        except Exception as e:
            raise Exception(
                f"Job {job_id} encountered an error {e} response: {response.content if response else response}")


def cleanup_temporary_folders():
    if os.path.exists(APP_PACKAGE_WORK_DIR):
        shutil.rmtree(APP_PACKAGE_WORK_DIR)
    if os.path.exists("cropped_screenshots"):
        shutil.rmtree("cropped_screenshots")
    if os.path.exists("screenshots"):
        shutil.rmtree("screenshots")
