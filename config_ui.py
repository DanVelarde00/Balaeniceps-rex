import json
import traceback
import os
from auto_ssh_setup import get_ssh_client, DEFAULT_SSH_PORT
from concurrent.futures import ThreadPoolExecutor

def edit_named_config(config_data, config_name):
    """
    Edits the given config block's state_manager and host.
    Returns True if changes were made.
    """
    changed = False

    conf = config_data.get("configurations", {}).get(config_name)
    if not conf:
        print(f"Warning: No '{config_name}' block found.")
        return False

    gst_settings = conf.get("vision_pipeline_settings", {}).get("gst_settings", {})
    current_state = conf.get("state_manager", "UNKNOWN")
    current_host = gst_settings.get("host", "0.0.0.0")

    print(f"\nModify '{config_name}' settings:")
    new_state = input(f"> Enter new state_manager (current: {current_state}): ").strip()
    new_host = input(f"> Enter new host IP (current: {current_host}): ").strip()

    if new_state and new_state != current_state:
        conf["state_manager"] = new_state
        changed = True

    if new_host and new_host != current_host:
        gst_settings["host"] = new_host
        changed = True

    if config_data.get("default_config") != config_name:
        print(f"> Setting '{config_name}' as the new default_config.")
        config_data["default_config"] = config_name
        changed = True

    if not changed:
        print("No changes made to config block.")

    return changed

def update_camera_test_configs(successful_drones, username="USERNAME", password="PASSWORD", port=None):
    choice = "raspi_default"
    template_path = "config.json"

    try:
        with open(template_path, "r") as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to read local config: {e}")
        return

    # Ask if user wants to edit config
    manual_edit = input("Do you want to manually edit a config block? (y/n): ").strip().lower() == 'y'
    if manual_edit:
        if not edit_named_config(config_data, choice):
            print("No manual config changes made.")

    # Now push per-drone config with unique ports
    def push_to_drone(drone, idx):
        label = drone["label"]
        ip = drone["ip"]
        print(f"\nUploading to {label} ({ip})...")

        config_to_push = json.loads(json.dumps(config_data))  # deep copy

        # Always assign a unique port
        try:
            raspi_conf = config_to_push["configurations"][choice]
            gst_settings = raspi_conf["vision_pipeline_settings"]["gst_settings"]
            gst_settings["port"] = 5600 + idx
        except Exception as e:
            print(f"Warning - {label}: Failed to set unique port: {e}")

        temp_path = f"temp_config_to_push_{label}.json"
        with open(temp_path, "w") as f:
            json.dump(config_to_push, f, indent=4)

        try:
            client = get_ssh_client(ip, username=username, password=password, port=port or DEFAULT_SSH_PORT)
            sftp = client.open_sftp()
            remote_path = "/home/dan/peregrine/configurations/config.json"
            sftp.put(temp_path, remote_path)
            sftp.chmod(remote_path, 0o644)
            sftp.close()
            client.close()
            print(f"{label}: Config pushed.")
        except Exception as e:
            print(f"Error - {label}: Failed to upload config: {e}")
            traceback.print_exc()
        finally:
            os.remove(temp_path)

    # Push in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(lambda args: push_to_drone(*args), [(drone, idx) for idx, drone in enumerate(successful_drones)])
