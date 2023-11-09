import json
import subprocess
import textwrap
import traceback
from typing import Dict, List

from PIL import Image

from app.common import *
from app.state import State


class AppContentManager:
    def __init__(self, state: State, terraformer_path: str):
        self.state = state
        self.terraformer_path = terraformer_path

    def import_content(self, app_folder_id, local_dest_path):
        folders_dict, content_dict = self.get_app_content_with_folders(app_folder_id)
        personal_folder_id = self.get_personal_folder()["id"]

        folders_tf = self.generate_folders_tf(folders_dict, app_folder_id, personal_folder_id)
        folders_tf_text = "".join(folders_tf.values())

        variables_tf_text = self.create_static_variables_tf()
        variables_tf_text += self.generate_variables_tf(folders_dict, app_folder_id)

        dashboard_content = self.filter_dashboards(content_dict)
        dashboard_content_ids = [dashboard["id"] for dashboard in dashboard_content]
        dashboards = self.get_dashboards(dashboard_content_ids)
        dashboard_ids = [dashboard["id"] for dashboard in dashboards]

        searches_tf_text = self.terraformize_saved_searches(folders_dict)

        output_path = APP_PACKAGE_WORK_DIR
        self.terraformize_dashboards(dashboard_ids, local_dest_path, output_path, folders_dict, app_folder_id)

        folders_tf_path = os.path.join(local_dest_path, "resources", "folders.tf")
        log_searches_tf_path = os.path.join(local_dest_path, "resources", "log-searches.tf")
        dashboards_tf_path = os.path.join(local_dest_path, "resources", "dashboards.tf")
        variables_tf_path = os.path.join(local_dest_path, "resources", "variables.tf")
        output_path_tf_path = os.path.join(local_dest_path, "resources", "output.tf")

        if folders_tf_text.strip():
            with open(folders_tf_path, 'w', encoding='utf-8') as file:
                file.write(folders_tf_text)

        if variables_tf_text.strip():
            with open(variables_tf_path, 'w', encoding='utf-8') as file:
                file.write(variables_tf_text)

        if searches_tf_text.strip():
            with open(log_searches_tf_path, 'w', encoding='utf-8') as file:
                file.write(searches_tf_text)

        output_tf_text = self.generate_output_tf(dashboards_tf_path, folders_tf_path, log_searches_tf_path)

        if output_tf_text.strip():
            with open(output_path_tf_path, 'w', encoding='utf-8') as file:
                file.write(output_tf_text)

        self.download_screenshots(app_folder_id)

    def filter_dashboards(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [item for item in content_list if item['itemType'] == 'Dashboard']

    def get_folder(self, folder_id) -> Dict[str, Any]:
        endpoint = get_folder_url(self.state.deployment, folder_id)
        response = requests.get(
            url=endpoint,
            auth=auth(self.state.access_key, self.state.access_id),
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get folder {folder_id}. Status code {response.status_code}: {response.text}")

        return json.loads(response.content)

    def get_personal_folder(self) -> Dict[str, Any]:
        return self.get_folder("personal")

    def get_app_content_with_folders(self, folder_id: str):
        folders = {}
        content = []
        folder = self.get_folder(folder_id)
        if folder["itemType"] == "Folder":
            folders[folder["id"]] = folder
            if "children" in folder:
                for child in folder["children"]:
                    if child["itemType"] == "Folder":
                        child_content = self.get_app_content_with_folders(child["id"])
                        folders.update(child_content[0])
                        content.extend(child_content[1])
                    else:
                        content.append(child)
        return [folders, content]

    def get_dashboards(self, dashboard_content_ids):
        def get_paginated_dashboards(url, headers, next_token=None):
            params = {'token': next_token} if next_token else {}
            response = requests.get(
                url, headers=headers, auth=auth(self.state.access_key, self.state.access_id), params=params)

            if response.status_code != 200:
                raise Exception(f"Failed to fetch dashboards with status code {response.status_code}: {response.text}")

            return response.json()

        url = get_dashboards_url(self.state.deployment)
        headers = {'Content-Type': 'application/json'}
        next_token = None
        all_dashboards = []
        expected_dashboard_count = len(dashboard_content_ids)
        while len(all_dashboards) < expected_dashboard_count:
            response_json = get_paginated_dashboards(url, headers, next_token)
            new_dashboards = [dashboard for dashboard in response_json['dashboards'] if
                              dashboard["contentId"] in dashboard_content_ids]
            all_dashboards.extend(new_dashboards)
            if response_json["next"] is not None:
                next_token = response_json["next"]
            else:
                break

        return all_dashboards

    def generate_variables_tf(self, folders: Dict[str, Dict[str, str]], app_folder_id) -> str:
        variables_text = ""

        for _, folder in folders.items():
            if folder["id"] == app_folder_id:
                continue
            folder_name = slugify(folder["name"], "_")
            variables_text += f'variable "{folder_name}_folder_name" {{\n'
            variables_text += '  type        = string\n'
            variables_text += f'  description = "{folder_name} folder name"\n'
            variables_text += f'  default     = "{folder["name"]}"\n'
            variables_text += '}\n\n'

            variables_text += f'variable "{folder_name}_folder_description" {{\n'
            variables_text += '  type        = string\n'
            variables_text += f'  description = "{folder_name} folder description"\n'
            variables_text += f'  default     = "{folder["description"]}"\n'
            variables_text += '}\n\n'

        return variables_text

    def create_static_variables_tf(self) -> str:
        content = '''
        variable "integration_root_dir" {
            type        = string
            description = "The folder in which app should be installed."
            default     = ""
        }

        variable "integration_name" {
            type        = string
            description = "The name of the integration"
            default     = ""
        }

        variable "integration_description" {
            type        = string
            description = "The description of the integration"
            default     = ""
        }
        '''

        if content.startswith("\n"):
            content = content[1:]

        return textwrap.dedent(content)

    def generate_folders_tf(self, folders: Dict[str, Dict[str, str]], root_folder_id: str,
                            root_parent_folder_id: str) -> Dict[str, str]:
        folders_tf = dict()

        for folder_id, folder in folders.items():
            folder_text = ""
            folder_name = slugify(folder["name"], "_")
            folder_var_name = f'var.{folder_name}_folder_name'
            folder_var_desc = f'var.{folder_name}_folder_description'
            # folders in the root folder
            if folder["parentId"] == root_folder_id:
                parent_id = 'sumologic_folder.integration_folder.id'
            # root folder - parent is personal folder
            elif folder["parentId"] == root_parent_folder_id:
                parent_id = "var.integration_root_dir"
                folder_name = "integration"
                folder_var_name = 'var.integration_name'
                folder_var_desc = 'var.integration_description'
            # child folders of the folders in app folder
            else:
                parent_id = f'sumologic_folder.{folders[folder["parentId"]]["name"]}_folder.id'

            folder_text += f'resource "sumologic_folder" "{folder_name}_folder" {{\n'
            folder_text += f'  name        = {folder_var_name}\n'
            folder_text += f'  description = {folder_var_desc}\n'
            folder_text += f'  parent_id   = {parent_id}\n'
            folder_text += '}\n\n'

            folders_tf[folder_id] = folder_text

        return folders_tf

    def terraformize_saved_searches(self, folders: Dict[str, Dict[str, Any]]) -> str:
        searches_tf = ""
        for folder in folders.values():
            if folder['children']:
                for child in folder['children']:
                    if child['itemType'] == "Search":
                        search_json = self.get_saved_search_json(child['id'])
                        searches_tf += self.json_to_terraform_resource(search_json, slugify(folder["name"], "_"))
                        searches_tf += "\n"

        return searches_tf

    def get_saved_search_json(self, search_content_id):
        url = export_content_url(self.state.deployment, search_content_id)

        response = requests.post(
            url=url,
            auth=auth(self.state.access_key, self.state.access_id),
        )

        if response.status_code != 200:
            raise Exception(f"Failed to create export saved search job for {search_content_id}."
                            f" Status code {response.status_code}: {response.text}")

        job_id = json.loads(response.content)['id']

        # Wait for the job to complete or for 30 seconds to elapse
        max_wait_time = 30
        start_time = time.time()
        while True:
            if time.time() - start_time > max_wait_time:
                # Time limit exceeded
                raise Exception(f"Exporting content id={search_content_id} timed out.")
            status_url = get_export_content_status_url(self.state.deployment, search_content_id, job_id)
            response = requests.get(
                url=status_url,
                auth=auth(self.state.access_key, self.state.access_id)
            )
            status = response.json()["status"]
            if status.lower() == "success":
                # Job is complete
                break
            elif status.lower() == "failed":
                # Job encountered an error
                raise Exception("Job encountered an error")

            # Wait for a short time before checking the status again
            time.sleep(1)

        result_url = get_export_content_result_url(self.state.deployment, search_content_id, job_id)

        response = requests.get(
            url=result_url,
            auth=auth(self.state.access_key, self.state.access_id),
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get saved search result. Status code {response.status_code}: {response.text}")

        return response.json()

    def json_to_terraform_resource(self, data: Dict[str, Any], parent_id_folder_name_tf: str) -> str:
        terraform_resource = f'''resource "sumologic_log_search" "{slugify(data.get('name', ''), '_')}" {{
        name = "{data.get('name', '')}"
        parent_id = sumologic_folder.{parent_id_folder_name_tf}_folder.id
        query_string = {json.dumps(data['search']['queryText'])}

        {f'description = "{data.get("description", "")}"' if data.get("description") else ""}
        {f'parsing_mode = "{data.get("search", {}).get("parsingMode", "")}"' if data.get("search", {}).get("parsingMode") else ""}
        {f'run_by_receipt_time = {str(data.get("search", {}).get("byReceiptTime", "")).lower()}' if data.get("search", {}).get("byReceiptTime") is not None else ""}

        time_range {{
            begin_bounded_time_range {{
                from {{
                    relative_time_range {{
                        relative_time = "{data.get("search", {}).get("defaultTimeRange", "")}"
                    }}
                }}
            }}
        }}'''

        if data.get('searchSchedule'):
            schedule = data['searchSchedule']
            terraform_resource += f'''
        schedule {{
            cron_expression = "{schedule.get('cronExpression', '')}"
            displayable_time_range = "{schedule.get('displayableTimeRange', '')}"
            time_zone = "{schedule.get('timeZone', '')}"

            {f'mute_error_emails = {str(schedule.get("muteErrorEmails", "")).lower()}' if schedule.get("muteErrorEmails") is not None else ""}
            {f'schedule_type = "{schedule.get("scheduleType", "")}"' if schedule.get("scheduleType") else ""}

            parseable_time_range {{
                begin_bounded_time_range {{
                    from {{
                        relative_time_range {{
                            relative_time = "{schedule.get("parseableTimeRange", {}).get("from", {}).get("relativeTime", "") if schedule.get("parseableTimeRange") and schedule.get("parseableTimeRange").get("from") else ""}"
                        }}
                    }}
                }}
            }}'''

            threshold = schedule.get("threshold", {})
            if threshold is not None:  # Checking for None before accessing further keys
                terraform_resource += f'''
            threshold {{
                count = {threshold.get("count", "")}
                operator = "{threshold.get("operator", "")}"
                threshold_type = "{threshold.get("thresholdType", "")}"
            }}'''

            notification = schedule.get("notification", {})
            if notification is not None:  # Checking for None before accessing further keys
                terraform_resource += f'''
            notification {{
                email_search_notification {{
                    include_csv_attachment = false
                    include_histogram = false
                    include_query = true
                    include_result_set = true
                    subject_template = "Search Alert: {{TriggerCondition}} found for {{SearchName}}"
                    to_list = [
                        "{notification.get("viewName", "")}",
                    ]
                }}
            }}'''

        terraform_resource += "\n}\n"

        return terraform_resource

    def terraformize_dashboards(self, dashboard_ids: List[str], local_dest_path: str,
                                output_path: str, folders_dict: Dict[str, Dict[str, Any]], app_folder_id: str) -> None:
        try:
            terraformer_flags = f"import sumologic -v --resources=dashboard --filter 'Name=id;Value={':'.join(dashboard_ids)}' -o '{output_path}'"

            # Print the exact command being run
            command_str = f"{self.terraformer_path} {terraformer_flags}"
            # Ensure that flags are passed correctly

            if self.state.deployment not in ["stag", "long"]:
                os.environ["SUMOLOGIC_ENVIRONMENT"] = self.state.deployment
            else:
                os.environ["SUMOLOGIC_BASE_URL"] = resolve_base_api_url(self.state.deployment)
            os.environ["SUMOLOGIC_ACCESS_ID"] = self.state.access_id
            os.environ["SUMOLOGIC_ACCESS_KEY"] = self.state.access_key

            print(f"Running command {command_str}")
            try:
                subprocess.run(command_str, text=True, shell=True, capture_output=True, env=os.environ)
            except subprocess.CalledProcessError as cpe:
                print(f"Error: Terraform process failed with return code {cpe.returncode}. Error message: {cpe.stderr}")

            # After successful translation, dashboards are saved in `output_path/sumologic/dashboard/dashboard.tf
            # this file should be moved to `output_path/resources/` folder and folder ids should be fixed
            dst_path = os.path.join(local_dest_path, "resources", "dashboards.tf")
            src_path = os.path.join(output_path, "sumologic", "dashboard", "dashboard.tf")
            generated_folder_path = os.path.join(output_path, "sumologic")
            shutil.move(src_path, dst_path)
            shutil.rmtree(generated_folder_path)
            self.replace_folder_id_in_file(folders_dict, dst_path, app_folder_id)
            self.fix_dashboards(dst_path)

        except Exception as e:
            print(f"Error: An unexpected error occurred: {e}")

    def replace_folder_id_in_file(self, folders_dict: Dict[str, Dict[str, Any]], file_path: str,
                                  app_folder_id: str) -> None:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Define a regex pattern to match the folder_id line
        pattern = r'(folder_id\s*=\s*)(")([0-9A-Za-z]+)(")'

        def replace_id(match):
            original_id = match.group(3)
            if original_id == app_folder_id:
                real_id = "sumologic_folder.integration_folder.id"
            else:
                real_id = f"sumologic_folder.{slugify(str(folders_dict[original_id]['name']), '_')}_folder.id"
            return f'{match.group(1)}{real_id}'

        # Replace the matched IDs using the re.sub() method
        updated_content = re.sub(pattern, replace_id, content)

        # Save the updated content to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

    def fix_dashboards(self, file_path: str) -> None:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            prefix = "title = "
            suffix_to_remove = " - New"
            processed_lines = []
            for line in lines:
                if 'resource "sumologic_dashboard"' in line:
                    line = re.sub(r'tfer--[a-zA-Z0-9-]*-_', '', line)
                    line = re.sub(r'-[a-zA-Z0-9]*(?=" {)', '', line)
                stripped_line = line.lstrip()
                if stripped_line.startswith(prefix) and suffix_to_remove in stripped_line:
                    line = line.replace(suffix_to_remove, "")
                processed_lines.append(line)

            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(processed_lines)
        except Exception as e:
            print(f"Error: An unexpected error occurred while fixing dashboard resource names: {e}")

    def generate_output_tf(self, dashboards_tf_path: str, folders_tf_path: str, searches_tf_path) -> str:
        def extract_resource_names(file_path, resource_type):
            resource_names = []

            # Regular expression to match the desired pattern
            pattern = re.compile(fr'resource "{resource_type}" "(.+)" {{')

            if os.path.exists(file_path):
                # Open the file and read its lines
                with open(file_path, 'r') as file:
                    for line in file.readlines():
                        # Search for the pattern in the current line
                        match = pattern.search(line)

                        # If a match is found, extract the resource name and add it to the list
                        if match:
                            resource_name = match.group(1)
                            resource_names.append(resource_name)

            return resource_names

        def generate_output_text(output_name, resource_type, object_names, name_attribute_name):
            output_text = f'output "{output_name}" {{\n'
            output_text += f'  description = "all the {output_name}"\n'
            output_text += '  value       = [\n'

            for name in object_names:
                output_text += f'    {{\n'
                output_text += f'      "id" = {resource_type}.{name}.id,\n'
                output_text += f'      "name" = {resource_type}.{name}.{name_attribute_name},\n'
                output_text += f'    }},\n'

            # Remove the extra comma and close the brackets
            output_text = output_text[:-2] + "\n"
            output_text += '  ]\n'
            output_text += '}\n\n'

            return output_text

        dashboard_resource_names = extract_resource_names(dashboards_tf_path, "sumologic_dashboard")
        folder_resource_names = extract_resource_names(folders_tf_path, "sumologic_folder")
        search_resource_names = extract_resource_names(searches_tf_path, "sumologic_log_search")

        output_tf = ""

        if dashboard_resource_names:
            output_tf += generate_output_text("dashboards", "sumologic_dashboard", dashboard_resource_names, "title")
        if folder_resource_names:
            output_tf += generate_output_text("folders", "sumologic_folder", folder_resource_names, "name")
        if search_resource_names:
            output_tf += generate_output_text("log_searches", "sumologic_log_search", search_resource_names, "name")

        return output_tf

    def get_screenshot_folder(self, app_folder_name):
        current_directory = os.getcwd()
        screenshot_folder_path = os.path.join(current_directory, "screenshots", app_folder_name)
        cropped_screenshot_folder_path = os.path.join(current_directory, "cropped_screenshots", app_folder_name)
        if not os.path.exists(screenshot_folder_path):
            os.makedirs(screenshot_folder_path)
        if not os.path.exists(cropped_screenshot_folder_path):
            os.makedirs(cropped_screenshot_folder_path)
        return screenshot_folder_path, cropped_screenshot_folder_path

    def download_screenshots(self, app_folder_id):
        file_ext = "png"
        try:
            _, content_dict = self.get_app_content_with_folders(app_folder_id)
            dashboard_content = self.filter_dashboards(content_dict)
            dashboard_content_ids = [dashboard["id"] for dashboard in dashboard_content]
            dashboards = self.get_dashboards(dashboard_content_ids)

            screenshot_folder_path, cropped_screenshot_folder_path = self.get_screenshot_folder(
                slugify_name(self.state.app_work_name))

            for dashboard in dashboards:
                dashboard_name = dashboard.get("title")
                variables = dashboard.get("variables")
                dashboard_screenshot_image_name = "%s.%s" % (slugify_name(dashboard_name), file_ext)
                downloaded_screenshot_image_path = os.path.join(screenshot_folder_path, dashboard_screenshot_image_name)
                cropped_screenshot_image_path = os.path.join(cropped_screenshot_folder_path,
                                                             dashboard_screenshot_image_name)
                preview_images_screenshot_path = os.path.join(preview_images_path(self.state.app_work_name), dashboard_screenshot_image_name)
                self.take_dashboard_screenshot(dashboard['id'], variables, downloaded_screenshot_image_path)
                self.crop_dashboard_screenshot(downloaded_screenshot_image_path, preview_images_screenshot_path)
                self.add_screenshot_reference_to_manifest(dashboard, preview_images_screenshot_path,
                                                          manifest_path(self.state.app_work_name))

        except Exception as e:
            print(f"Error occurred in downloading screenshots. Error: {e} Traceback: {traceback.format_exc()}")

    def take_dashboard_screenshot(self, dashboard_id, variables, image_filepath):
        download_endpoint = download_screenshot_endpoint(self.state.deployment)
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
            auth=auth(self.state.access_key, self.state.access_id),
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )

        if response.ok:
            job_id = json.loads(response.content)['id']
            status_endpoint = f"{download_endpoint}/{job_id}/status"

            wait_for_job_completion(
                get_status=lambda: requests.get(url=status_endpoint, auth=auth(self.state.access_key, self.state.access_id)),
                success_status="success",
                failure_status="failed",
                polling_interval=1,
                timeout=180
            )

            # downloading actual raw image file
            download_result_endpoint = f"{download_endpoint}/{job_id}/result"
            response = requests.get(
                url=download_result_endpoint,
                auth=auth(self.state.access_key, self.state.access_id),
                headers={
                    'Content-Type': 'application/json'
                },
                stream=True,
            )
            if response.ok:
                with open(image_filepath, 'wb') as fout:
                    shutil.copyfileobj(response.raw, fout)
            else:
                raise Exception(f"Error in dashboards/reportJobs/result api: {response.content}")
        else:
            raise Exception(f"Error in dashboards/reportJobs api: {response.content}")

    def crop_dashboard_screenshot(self, source_imagepath, target_imagepath):
        image = Image.open(source_imagepath)
        # background color for dark themed screenshots
        bg_color = (16, 24, 39, 255)
        img_copy = image.copy()
        for y in range(img_copy.size[1]):
            for x in range(img_copy.size[0]):
                if img_copy.getpixel((x, y)) == bg_color:
                    img_copy.putpixel((x, y), (0, 0, 0, 0))

        (topLeftX, topLeftY, bottomRightX, bottomRightY) = img_copy.getbbox()
        cropped = image.crop((0, 0, bottomRightX, bottomRightY))
        cropped.save(target_imagepath)

    def add_screenshot_reference_to_manifest(self, dashboard_data, screenshot_path, manifest_path):
        # Convert the screenshot path to a relative path
        relative_path = os.path.relpath(screenshot_path, start=os.path.dirname(manifest_path))
        relative_path = relative_path.replace('\\', '/')  # Convert to forward slashes for consistency
        if not relative_path.startswith('.'):
            relative_path = f"./{relative_path}"

        # Prepare the new appMedia entry with proper quoting and indentation
        new_media_entry = (
            f'  - title: "{dashboard_data["title"]}"\n'
            f'    description: "{dashboard_data["description"]}"\n'
            f'    type: "image"\n'
            f'    location: "{relative_path}"\n'
        )

        # Read in the file
        with open(manifest_path, 'r') as file:
            lines = file.readlines()

        # Locate the appMedia list and the insertion point
        app_media_index = None
        for i, line in enumerate(lines):
            if line.strip() == 'appMedia:':
                app_media_index = i
                break

        # If appMedia field not found, raise an error
        if app_media_index is None:
            raise ValueError("appMedia field not found in the manifest.")

        # Find the end of the appMedia list
        insert_index = app_media_index + 1
        while insert_index < len(lines):
            if lines[insert_index].strip().startswith('- title:'):
                insert_index += 1
            elif lines[insert_index].strip() == '':
                break
            else:
                insert_index += 1

        # Insert the new media entry at the correct index
        lines.insert(insert_index, new_media_entry)

        # Write everything back to the file
        with open(manifest_path, 'w') as file:
            file.writelines(lines)
