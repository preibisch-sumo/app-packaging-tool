import platform
import subprocess

from app.app_content_manager import AppContentManager
from app.common import *
from app.state import State


class AppManager:
    def __init__(self, state: State, terraformer_path: str):
        self.state = state
        self.app_content_manager = AppContentManager(state, terraformer_path)

    def edit_manifest(self):
        self.open_text_file_in_editor(manifest_path(self.state.app_work_name))

    def edit_config(self):
        self.open_text_file_in_editor(config_path(self.state.app_work_name))

    def edit_readme(self):
        self.open_text_file_in_editor(readme_path(self.state.app_work_name))

    def edit_license(self):
        self.open_text_file_in_editor(license_path(self.state.app_work_name))

    def set_icon(self, src):
        shutil.copy(src, icon_path(self.state.app_work_name))

    def import_resources(self, resourceId):
        self.app_content_manager.import_content(format_hex(resourceId), app_root_path(self.state.app_work_name))

    def save_and_export(self):
        app_name = read_name_from_yaml(manifest_path(self.state.app_work_name))
        zip_folder(app_root_path(self.state.app_work_name), app_results_path(app_name))

    def create_new_app_package(self, app_name):
        # Remove the app package directory if it exists
        if os.path.exists(app_root_path(app_name)):
            shutil.rmtree(app_root_path(app_name))

        # Create the app package directory
        if not os.path.exists(APP_PACKAGE_WORK_DIR):
            os.mkdir(APP_PACKAGE_WORK_DIR)

        # Copy the app package template
        self.copy_and_rename_directory(
            APP_PACKAGE_TEMPLATE_PATH,
            APP_PACKAGE_WORK_DIR,
            app_name
        )

    def open_text_file_in_editor(self, filepath):
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", filepath])
        else:  # Linux and other UNIX-like systems
            subprocess.run(["xdg-open", filepath])

    def copy_and_rename_directory(self, src, dest, new_name):
        # Copy entire directory recursively
        shutil.copytree(src, os.path.join(dest, os.path.basename(src)))

        # Determine the old and new full paths
        old_dir_path = os.path.join(dest, os.path.basename(src))
        new_dir_path = os.path.join(dest, new_name)

        # Create new directory if it doesn't exist
        if not os.path.exists(new_dir_path):
            os.mkdir(new_dir_path)

        # Move each file in old directory to new directory
        for filename in os.listdir(old_dir_path):
            shutil.move(os.path.join(old_dir_path, filename), os.path.join(new_dir_path, filename))

        # Remove the old directory
        shutil.rmtree(old_dir_path)

    def zip_folder(self, folder_path, zip_dest_path):
        # Check if the folder exists
        if not os.path.exists(folder_path):
            print("Source folder does not exist.")
            return False

        # Create zip file
        try:
            shutil.make_archive(zip_dest_path, 'zip', folder_path)
        except Exception as e:
            print(f"Could not create zip file. Error: {e}")
            return False

        print("Folder successfully compressed.")
        return True


