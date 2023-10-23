import tkinter as tk
import tkinter.ttk as ttk
import json
import os
from tkinter import filedialog

from common import random_string


class MainWindow(tk.Tk):
    def __init__(self, state, app_manager):
        super().__init__()
        self.state = state
        self.app_manager = app_manager
        self.user = None
        self.user_label = tk.Label(self)
        self.user_label.grid()  # Change pack to grid

        self.title("App Packaging Tool")  # Set the window title

        # Prevent the window from being resized
        self.resizable(False, False)

        self.initialize_frames()

        self.center_window()

    def initialize_main_frame(self):
        # Create the main view
        self.main_frame = tk.Frame(self)
        self.main_frame.grid()

        self.login_frame_button = tk.Button(self.main_frame, text="Log In", command=self.show_login_view)
        self.login_frame_button.grid(row=0, column=0)

        # Display the user's name if they're logged in
        self.user_label = tk.Label(self.main_frame, text="")
        self.user_label.grid(row=1, column=0)

        # Add "Create New App" button
        self.create_button = tk.Button(self.main_frame, text="Create New App", command=self.create_new_app)
        self.create_button.grid(row=2, column=0)

        # Add "Modify Existing App" button
        self.modify_button = tk.Button(self.main_frame, text="Modify Existing App", command=self.modify_existing_app)
        self.modify_button.grid(row=5, column=0)

        # Add field for choosing existing app
        self.existing_app_label = tk.Label(self.main_frame, text="Existing app folder")
        self.existing_app_label.grid(row=6, column=0)
        self.existing_app_entry = tk.Entry(self.main_frame)
        self.existing_app_entry.grid(row=7, column=0)

        # Hide the create and modify app buttons and their associated input boxes
        self.set_app_controls_visibility('hidden')

    def set_app_controls_visibility(self, state):
        controls = [self.create_button, self.modify_button, self.existing_app_label, self.existing_app_entry]
        for control in controls:
            control.grid_remove() if state == 'hidden' else control.grid()

    def initialize_create_app_frame(self):
        self.create_app_frame = tk.Frame(self)

        self.edit_manifest_button = tk.Button(self.create_app_frame, text="Edit manifest.yaml",
                                              command=self.edit_manifest)
        self.edit_manifest_button.grid(row=0, column=0)

        self.edit_config_button = tk.Button(self.create_app_frame, text="Edit config.yaml", command=self.edit_config)
        self.edit_config_button.grid(row=1, column=0)

        self.edit_readme_button = tk.Button(self.create_app_frame, text="Edit readme.md", command=self.edit_readme)
        self.edit_readme_button.grid(row=2, column=0)

        self.edit_license_button = tk.Button(self.create_app_frame, text="Edit license.md", command=self.edit_license)
        self.edit_license_button.grid(row=3, column=0)

        self.set_icon_button = tk.Button(self.create_app_frame, text="Set Icon", command=self.set_icon)
        self.set_icon_button.grid(row=4, column=0)

        self.import_resources_button = tk.Button(self.create_app_frame, text="Import Resources",
                                                 command=self.import_resources)
        self.import_resources_button.grid(row=5, column=0)

        # Added input box for resourceId next to the "Import Resources" button
        self.resource_id_label = tk.Label(self.create_app_frame, text="Resource ID:")
        self.resource_id_label.grid(row=5, column=1)
        self.resource_id_entry = tk.Entry(self.create_app_frame)
        self.resource_id_entry.grid(row=5, column=2)

        # Add "Save & Export" button
        self.save_and_export_button = tk.Button(self.create_app_frame, text="Save & Export",
                                                command=self.save_and_export, height=3, width=20)
        self.save_and_export_button.grid(row=8, column=0, sticky='nsew')

        # Add "Back to Main" button
        self.back_to_main_button = tk.Button(self.create_app_frame, text="Back to Main", command=self.show_main_frame)
        self.back_to_main_button.grid(row=9, column=0, sticky='nsew')

    def initialize_login_frame(self):
        # Create the login view (hidden by default)
        self.login_frame = tk.Frame(self)

        self.name_label = tk.Label(self.login_frame, text="Name")
        self.name_label.grid(row=0, column=0)

        # Load the account names from accounts.json
        with open('accounts.json', 'r') as f:
            self.accounts = json.load(f)
            self.names = [account['name'] for account in self.accounts]

        # Create a Combobox for the name
        self.name_combobox = ttk.Combobox(self.login_frame, values=self.names)
        self.name_combobox.grid(row=1, column=0)
        self.name_combobox.bind('<<ComboboxSelected>>', self.update_account_fields)

        self.access_key_label = tk.Label(self.login_frame, text="Access Key")
        self.access_key_label.grid(row=2, column=0)
        self.access_key_entry = tk.Entry(self.login_frame)
        self.access_key_entry.grid(row=3, column=0)

        self.access_id_label = tk.Label(self.login_frame, text="Access ID")
        self.access_id_label.grid(row=4, column=0)
        self.access_id_entry = tk.Entry(self.login_frame)
        self.access_id_entry.grid(row=5, column=0)

        self.deployment_label = tk.Label(self.login_frame, text="Deployment")
        self.deployment_label.grid(row=6, column=0)
        self.deployment_var = tk.StringVar(self.login_frame)
        self.deployment_var.set("stag")  # default value
        self.deployment_option = tk.OptionMenu(self.login_frame, self.deployment_var, "stag", "long", "prods")
        self.deployment_option.grid(row=7, column=0)

        self.save_button = tk.Button(self.login_frame, text="Save", command=self.save_account)
        self.save_button.grid(row=8, column=0)

        self.save_label = tk.Label(self.login_frame, text="")
        self.save_label.grid(row=9, column=0)

        # Add login and back buttons
        self.login_button = tk.Button(self.login_frame, text="Log In", command=self.login)
        self.login_button.grid(row=10, column=0)

        self.back_button = tk.Button(self.login_frame, text="Back", command=self.show_main_frame)
        self.back_button.grid(row=11, column=0)

    def modify_existing_app(self):
        # Code to modify an existing app
        pass

    def update_account_fields(self, event):
        # Find the account with the selected name
        for account in self.accounts:
            if account['name'] == self.name_combobox.get():
                # Update the access_key and access_id fields
                self.access_key_entry.delete(0, 'end')
                self.access_key_entry.insert(0, account['access_key'])
                self.access_id_entry.delete(0, 'end')
                self.access_id_entry.insert(0, account['access_id'])
                break

    def initialize_frames(self):
        self.initialize_main_frame()
        self.initialize_login_frame()
        self.initialize_create_app_frame()

    def login(self):
        # Log in the user and switch back to the main frame
        self.user = self.name_combobox.get()
        self.show_main_frame()
        self.state.log_in(self.user, self.deployment_var.get(), self.access_key_entry.get(), self.access_id_entry.get())

    def create_new_app(self):
        self.main_frame.grid_remove()
        self.create_app_frame.grid()
        self.state.app_work_name = f"new_app_{random_string(6)}"
        self.app_manager.create_new_app_package(self.state.app_work_name)

    def show_main_frame(self):
        # Update the user_label text and switch to the main frame
        if self.user:
            self.user_label.config(text=f"Logged in as {self.user}")
            self.login_frame_button.grid_remove()  # Remove the login button from the main frame
            # Show the create and modify app buttons and their associated input boxes
            self.set_app_controls_visibility('visible')
        else:
            self.user_label.config(text="Not logged in")
            self.login_button.grid()  # Show the login button if the user is not logged in
        self.login_frame.grid_remove()
        self.create_app_frame.grid_remove()
        self.main_frame.grid()

    def show_login_view(self):
        # Hide the main frame and show the login frame
        self.main_frame.grid_remove()  # Change pack_forget to grid_remove
        self.login_frame.grid()  # Change pack to grid

    def save_account(self):
        account = {
            "name": self.name_combobox.get(),
            "access_key": self.access_key_entry.get(),
            "access_id": self.access_id_entry.get(),
            "deployment": self.deployment_var.get()
        }

        if not os.path.exists('accounts.json'):
            with open('accounts.json', 'w') as f:
                json.dump([account], f)
            self.save_label.config(text="Account saved successfully!")
        else:
            with open('accounts.json', 'r+') as f:
                accounts = json.load(f)
                existing_names = {acc['name'] for acc in accounts}

                if account['name'] not in existing_names:
                    accounts.append(account)
                    f.seek(0)
                    f.truncate()  # Clear the file before rewriting
                    json.dump(accounts, f, indent=4, sort_keys=True, separators=(',', ': '))
                    self.save_label.config(text="Account saved successfully!")
                else:
                    self.save_label.config(text="Account already exists!")

    def center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = self.winfo_reqwidth()
        window_height = self.winfo_reqheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        self.geometry("+{}+{}".format(position_right, position_top))

    def edit_manifest(self):
        self.app_manager.edit_manifest()

    def edit_config(self):
        self.app_manager.edit_config()

    def edit_readme(self):
        self.app_manager.edit_readme()

    def edit_license(self):
        self.app_manager.edit_license()

    def set_icon(self):
        file_path = filedialog.askopenfilename(title="Select an Icon",
                                               filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:  # Check if a file was selected
            print(f"Selected file path: {file_path}")
            self.app_manager.set_icon(file_path)

    def import_resources(self):
        print("Importing resources...")
        self.app_manager.import_resources(self.resource_id_entry.get())
        print("Done importing resources")

    def save_and_export(self):
        self.app_manager.save_and_export()


