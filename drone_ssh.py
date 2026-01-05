# drone_ssh.py
#!/usr/bin/env python3
import time
import queue
import threading
from config_ui import update_camera_test_configs
from auto_ssh_setup import ssh_and_setup, get_ssh_client, DEFAULT_SSH_PORT


def read_ips(filename="ssh_hosts.txt"):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]


def ssh_into_drones(ip_map, username="USERNAME", password="PASSWORD", port=DEFAULT_SSH_PORT, do_setup=True):
    results = []
    threads = []

    def connect_and_setup(label, ip):
        try:
            client = get_ssh_client(ip, username=username, password=password, port=port)
            client.close()

            if do_setup:
                print(f"Running setup on {label} ({ip})...")
                ssh_and_setup(ip, label, username=username, password=password, port=port)

            results.append({"label": label, "ip": ip, "status": "success"})
        except Exception as e:
            print(f"Error - {label}: {e}")
            results.append({"label": label, "ip": ip, "status": "error", "error": str(e)})

    for label, ip in ip_map.items():
        connect_and_setup(label, ip)

    return results


def handle_camera_session(drone, port, input_queue):
    label = drone["label"]
    ip = drone["ip"]
    print(f"\nStarting camera test on {label} (port {port})...")

    try:
        client = get_ssh_client(ip, username="USERNAME", password="PASSWORD", port=DEFAULT_SSH_PORT)
        channel = client.invoke_shell()
        channel.send("cd ~/peregrine\n")
        channel.send(".venv/bin/python3 camera_pipeline_test.py raspi_default 2>&1\n")

        print(f"{label}: Camera session started.")

        while True:
            if channel.recv_ready():
                output = channel.recv(1024).decode("utf-8", errors="ignore")
                print(f"[{label}] {output}", end="")

            try:
                command = input_queue.get_nowait()
                channel.send(command)
            except queue.Empty:
                pass

            time.sleep(0.05)

    except Exception as e:
        print(f"Error - {label}: Error during camera test: {e}")
    finally:
        try:
            channel.close()
            client.close()
        except:
            pass

        try:
            kill_client = get_ssh_client(ip, username="USERNAME", password="PASSWORD", port=DEFAULT_SSH_PORT)
            kill_channel = kill_client.get_transport().open_session()
            kill_channel.exec_command("pkill -f camera_pipeline_test.py")
            kill_channel.close()
            kill_client.close()
            print(f"{label}: Kill signal sent.")
        except Exception as e:
            print(f"Warning - {label}: Failed to send kill signal: {e}")


def run_camera_tests(drone_list):
    update_camera_test_configs(drone_list)

    clients = []
    channels = []

    for idx, drone in enumerate(drone_list):
        label = drone["label"]
        ip = drone["ip"]
        port = 5600 + idx
        print(f"\nStarting camera test on {label} (port {port})...")

        try:
            client = get_ssh_client(ip, username="USERNAME", password="PASSWORD", port=DEFAULT_SSH_PORT)
            channel = client.invoke_shell()
            channel.send("cd ~/peregrine\n")
            channel.send(".venv/bin/python3 camera_pipeline_test.py raspi_default 2>&1\n")

            clients.append((label, client))
            channels.append((label, channel))

        except Exception as e:
            print(f"Error - {label}: Failed to start camera session: {e}")

    print("\nType commands (e.g., 1, 8, 9) and press Enter to send to ALL drones. Ctrl+C to exit.\n")
    try:
        while True:
            user_input = input().strip()
            if not user_input:
                continue

            if user_input.startswith("@"):  # Targeted input
                try:
                    targets_str, command = user_input[1:].split(" ", 1)
                    targets = [t.strip().upper() for t in targets_str.split(",")]
                except ValueError:
                    print("Invalid format. Use: @D1,D2 command")
                    continue
            else:
                targets = [label for label, _ in channels]
                command = user_input

            for label, chan in channels:
                if label in targets:
                    try:
                        chan.send(command + "\n")
                        time.sleep(0.05)
                    except Exception:
                        print(f"Warning - {label}: Failed to send input.")
    except KeyboardInterrupt:
        print("\nInterrupted. Shutting down drones...")
    finally:
        for label, client in clients:
            try:
                kill = client.get_transport().open_session()
                kill.exec_command("pkill -f camera_pipeline_test.py")
                kill.close()
                client.close()
                print(f"{label}: Camera process stopped.")
            except Exception as e:
                print(f"Warning - {label}: Cleanup error: {e}")


def main():
    ips = read_ips()
    ip_map = {f"D{i+1}": ip for i, ip in enumerate(ips)}

    if not ip_map:
        print("Error: No devices found.")
        return

    if len(ip_map) == 1:
        label, ip = next(iter(ip_map.items()))
        print(f"One Pi found: {label} -> {ip}")
        do_setup = input("Run full setup on the drone? (y/n): ").strip().lower() == 'y'
        results = ssh_into_drones({label: ip}, do_setup=do_setup)
        success = [res for res in results if res["status"] == "success"]

        if success:
            update_camera_test_configs(success)
            if input("Run camera test? (y/n): ").strip().lower() == 'y':
                run_camera_tests(success)
        return

    print("Multiple Pis found:")
    for label, ip in ip_map.items():
        print(f"{label} -> {ip}")

    selection = input("Enter device labels to connect (comma separated): ").split(',')
    selected_map = {label.strip(): ip_map[label.strip()] for label in selection if label.strip() in ip_map}

    do_setup = input("Run full setup on each drone? (y/n): ").strip().lower() == 'y'
    results = ssh_into_drones(selected_map, do_setup=do_setup)
    print("\nSSH Results:")
    for res in results:
        print(res)

    successful = [res for res in results if res["status"] == "success"]
    if not successful:
        print("Error: No successful SSH connections.")
        return

    print("\n")
    time.sleep(1)  # Reduce prompt overlap
    update_camera_test_configs(successful)

    if input("Run camera test on these drones? (y/n): ").strip().lower() == 'y':
        selected = input("Enter drone labels to run camera test on (comma separated): ").split(",")
        filtered = [res for res in successful if res["label"] in [s.strip() for s in selected]]
        run_camera_tests(filtered)

if __name__ == "__main__":
    main()
