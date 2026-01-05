# auto_ssh_setup.py
#!/usr/bin/env python3
import paramiko
import time
import threading
import os

USERNAME = "INSERT_USERNAME"
PASSWORD = "INSERT_PASSWORD"

GIT_USERNAME = "INSERT USER"
GIT_PASSWORD = "INSERT TOKEN"

DEFAULT_SSH_PORT = 22
print_lock = threading.Lock()

def get_ssh_client(ip, username=USERNAME, password=PASSWORD, port=None, timeout=30):
    if port is None:
        port = DEFAULT_SSH_PORT
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=username, password=password, port=port, timeout=timeout)
    return client

def read_ips(filename="ssh_hosts.txt"):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def execute_commands(client, commands):
    for label, cmd in commands:
        with print_lock:
            print(f">> {label}")
        try:
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    with print_lock:
                        print(stdout.channel.recv(1024).decode(), end="")
                if stderr.channel.recv_stderr_ready():
                    with print_lock:
                        print(stderr.channel.recv_stderr(1024).decode(), end="")
                time.sleep(0.1)

            output = stdout.read().decode()
            error = stderr.read().decode()
            if output:
                with print_lock:
                    print(output, end="")
            if error:
                with print_lock:
                    print(error, end="")

        except Exception as e:
            with print_lock:
                print(f"Error running '{label}': {e}")

def ssh_and_setup(ip, label, username=USERNAME, password=PASSWORD, port=None):
    if port is None:
        port = DEFAULT_SSH_PORT

    with print_lock:
        print(f"Connecting to {label} ({ip})")

    try:
        client = get_ssh_client(ip, username=username, password=password, port=port, timeout=10)

        # Check if Peregrine is already installed
        check_install_cmd = "test -f ~/peregrine/peregrine_test.py && test -d ~/peregrine/.venv && test -f ~/peregrine/requirements.txt"
        stdin, stdout, stderr = client.exec_command(check_install_cmd)
        install_ok = stdout.channel.recv_exit_status() == 0

        reinstall = False
        if install_ok:
            with print_lock:
                user_input = input(f"{label}: Peregrine already exists. Reinstall? (y/n): ").strip().lower()
                if user_input == "y":
                    reinstall = True
                else:
                    print(f"{label}: Skipping reinstall.")
        else:
            reinstall = True

        # Run installation script if needed
        if reinstall:
            with print_lock:
                print(f"Uploading Peregrine install script to {label}...")

            # Read local install script
            local_script_path = "install_peregrine.sh"
            if not os.path.exists(local_script_path):
                print(f"Missing {local_script_path}. Please make sure it exists.")
                return

            with open(local_script_path, "r") as f:
                script_content = f.read()

            remote_path = f"/home/{username}/install_peregrine.sh"
            sftp = client.open_sftp()
            with sftp.file(remote_path, "w") as remote_file:
                remote_file.write(script_content)
            sftp.chmod(remote_path, 0o755)

            # Run the script
            execute_commands(client, [
                ("Running Peregrine install script", f"bash {remote_path}")
            ])

        client.close()
        time.sleep(2)
        with print_lock:
            print(f"{label} setup complete.\n")

    except Exception as e:
        with print_lock:
            print(f"Failed to connect to {label} ({ip}): {e}")

def main():
    ips = read_ips()
    ip_map = {f"D{i+1}": ip for i, ip in enumerate(ips)}
    for label, ip in ip_map.items():
        ssh_and_setup(ip, label)

if __name__ == "__main__":
    main()
