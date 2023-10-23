import requests
import json
import shutil
import os
import traceback
from PIL import Image
from typing import Any, Dict, List


def get_scerenshot_folder(self, app_folder_name):
    current_directory = os.getcwd()
    screenshot_folderpath = os.path.join(current_directory, "screenshots", app_folder_name)
    cropped_screenshot_folderpath = os.path.join(current_directory, "cropped_screenshots", app_folder_name)
    if not os.path.exists(screenshot_folderpath):
        os.makedirs(screenshot_folderpath)
    if not os.path.exists(cropped_screenshot_folderpath):
        os.makedirs(cropped_screenshot_folderpath)
    return screenshot_folderpath, cropped_screenshot_folderpath

def execute(self):
    file_ext = "png"
    utils.info(f"Downloading Screenshot for app: {state.app_name}")
    try:
        pre_personal_folder = self.get_personal_folder()
        app_folder_id = self.get_app_folder_id(state.app_name, pre_personal_folder)
        if not app_folder_id:
            utils.warn(f"{state.app_name} folder does not exists please install it.")
            return
        all_content = self.get_all_content(app_folder_id)
        v2_dashboards = self.get_v2_dashboards(all_content)
        v2_dashboard_contendIds = [dashboard['id'] for dashboard in v2_dashboards]
        v2_dashboards = self.get_dashboards_by_contentId(v2_dashboard_contendIds)
        screenshot_folderpath, cropped_screenshot_folderpath = self.get_scerenshot_folder(utils.slugify_text(state.app_name))
        for dashboard in v2_dashboards:
            dashboard_name = dashboard.get("title")
            variables = dashboard.get("variables")
            utils.debug(f"fetching screenshot for {dashboard_name}")
            dashboard_screenshot_image_name = "%s.%s" % (utils.slugify_text(dashboard_name), file_ext)
            downloaded_screenshot_image_path = os.path.join(screenshot_folderpath, dashboard_screenshot_image_name)
            cropped_screenshot_image_path = os.path.join(cropped_screenshot_folderpath, dashboard_screenshot_image_name)
            self.take_dashboard_screenshot(dashboard['id'], variables, downloaded_screenshot_image_path)
            self.__crop_dashboard_screenshot(downloaded_screenshot_image_path, cropped_screenshot_image_path)
    except Exception as e:
        utils.error(f"Error occurred in downloading screenshots for app {state.app_name} Error: {e} Traceback: {traceback.format_exc()}")

def get_v2_dashboards(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [item for item in content_list if item['itemType'] == 'Dashboard']

def __take_dashboard_screenshot(self, dashboard_id, variables, image_filepath):
    auth = utils.auth(self.deployment)
    if auth is None:
        utils.warn(f"No auth found for {self.deployment}. Skipping it.")
        self.apps_by_deployment[self.deployment] = None
    else:
        download_endpoint = f"{utils.get_endpoint(self.deployment)}/v2/dashboards/reportJobs"
        payload = {
            "action": {
                "actionType": "DirectDownloadReportAction"
            },
            "exportFormat": "Png",
            "timezone": "America/Los_Angeles",
            "template": {
                "templateType": "DashboardTemplate",
                "id": dashboard_id,
                "timeRange": {
                    "type": "BeginBoundedTimeRange",
                    "from": {
                        "type": "RelativeTimeRangeBoundary",
                        "relativeTime": "-24h"
                    }
                }
            }
        }
        if variables:
            payload["template"]["variableValues"] = {
                "data": {variable.get("name"): [variable.get("defaultValue", "*")] for variable in variables}
            }

        response = requests.post(
            url=download_endpoint,
            auth=auth,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        if response.ok:
            job_id = json.loads(response.content)['id']

            self._wait_for_job_completion(download_endpoint, job_id)

            # downloading actual raw image file
            download_result_endpoint = f"{download_endpoint}/{job_id}/result"
            response = requests.get(
                url=download_result_endpoint,
                auth=auth,
                headers={'Content-Type': 'application/json'},
                stream=True
            )
            if response.ok:
                with open(image_filepath, 'wb') as fout:
                    shutil.copyfileobj(response.raw, fout)
            else:
                raise Exception(f"Error in dashboards/reportJobs/result api: {response.content}")
        else:
            raise Exception(f"Error in dashboards/reportJobs api: {response.content}")

def __crop_dashboard_screenshot(self, source_imagepath, target_imagepath):

    image = Image.open(source_imagepath)
    utils.info(f"Original Dimensions of {source_imagepath}: {image.getbbox()}")
    # background color for dark themed screenshots
    bg_color = (16, 24, 39, 255)
    img_copy = image.copy()
    for y in range(img_copy.size[1]):
        for x in range(img_copy.size[0]):
            if img_copy.getpixel((x, y)) == bg_color:
                img_copy.putpixel((x, y), (0, 0, 0, 0))

    # img_copy.save('%s' % source_imagepath.replace(".png","_colored.png"))
    (topLeftX, topLeftY, bottomRightX, bottomRightY) = img_copy.getbbox()
    utils.info(f"Cropping {source_imagepath}: {(0, 0, bottomRightX, bottomRightY)}")
    cropped = image.crop((0, 0, bottomRightX, bottomRightY))
    cropped.save(target_imagepath)

