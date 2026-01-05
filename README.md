# Balaeniceps-rex

A toolkit for managing, configuring, and testing multiple Raspberry Pi drones over SSH from a WSL environment, specifically designed to interact with Peregrine.

---

## Developer Notes

- **Pi Discovery:** The `find_pis.py` script searches for physical addresses matching `RASPBERRY_PI_PREFIX`. If unable to locate a Pi that is confirmed to be on and connected to the same network, identify the physical address manually and add it to the variable.

- **Port Forwarding:** If using port forwarding, update `DEFAULT_SSH_PORT` in `auto_ssh_setup.py`:
  ```python
  DEFAULT_SSH_PORT = 1022  # Set to 22 if not using port forwarding
  ```

- **Video Streaming:** Automatic port assignment only works with Pis using the `raspi_default` configuration. Multi-stream video will not function if this configuration is not used.

---

## Features

- **Automatic Pi Discovery:**
  Find Raspberry Pis on your network using ARP table scanning (`find_pis.py`).

- **SSH Management:**
  Connect to one or more Pis, run setup scripts, and manage connections (`drone_ssh.py`).

- **Automated Setup:**
  Install dependencies, clone repositories, and prepare the environment on each Pi (`auto_ssh_setup.py`).

- **Camera Pipeline Testing:**
  Launch and interact with camera pipelines on multiple Pis, send commands, and monitor output.

- **Configuration Management:**
  Update and synchronize configuration files across all drones (`config_ui.py`).

---

## Prerequisites

- **Windows Subsystem for Linux (WSL):**
  Download and install WSL from the Microsoft Store.

- **Raspberry Pi 5:**
  All Pis should be Raspberry Pi 5 units. Other versions may work but have not been tested.

- **Required Packages:**
  ```bash
  sudo apt update && sudo apt install -y python3 python3-pip python3-venv openssh-client
  ```

---

## Installation

### 1. Clone the Repository

This project should be saved in your WSL environment (may work on native Ubuntu but untested).

```bash
cd ~/Projects
git clone https://github.com/DanVelarde00/Balaeniceps-rex-wsl.git
cd Balaeniceps-rex-wsl
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Flash Raspberry Pi Firmware

Use the Raspberry Pi Imager to flash your Pis with the latest Raspberry Pi OS image.

**Important:** Configure custom settings during the flashing process:
- Set username and password (see configuration section below)
- Connect all Pis to the same network
- Ensure the camera module is connected and powered

To set your credentials, update the following in `auto_ssh_setup.py`:
```python
USERNAME = "your_username"
PASSWORD = "your_password"
```

You will also need to update the git pull line in `install_peregrine.sh`.

### 5. Configure Git Credentials

Update `auto_ssh_setup.py` with your Peregrine repository credentials:
```python
GIT_USERNAME = "your.git.username"
GIT_PASSWORD = "your_access_token"
```

> **Note:** Access tokens have expiration dates. Ensure your token is valid before running setup scripts.

### 6. Configure `config_ui.py`

Update the username and password to match your Pi credentials:

```python
client.connect(ip, username="your_username", password="your_password", timeout=30)
```

Update the configuration paths as needed:
```python
config_path = "/home/your_username/peregrine/configurations/config.json"
temp_path = "/home/your_username/config_temp.json"
```

**Configuration File Setup:**
- Pre-load the configuration file on each Pi before running the main script
- Update the IP address to point to your desired data stream destination
- Set the last configuration line to `raspi_default`
- Consult your team lead for specific configuration parameters

### 7. Discover Pis on the Network

Run the discovery script to find all Pis on your network and save their IPs to `ssh_hosts.txt`:

```bash
python3 find_pis.py
```

This only needs to be run once per session and is useful for troubleshooting.

### 8. Run the SSH Management Script

```bash
python3 drone_ssh.py
```

**Important:** Run this from a standalone terminal window, not from an IDE's integrated terminal, as input forwarding to drones may not work correctly in embedded terminals.

**Camera Test Commands:**
- Send `1`, `2`, `3`, or other Peregrine commands to broadcast to all drones
- Use `@D1 1` or `@D2 2` to send commands to specific drones
- Use `@D1,D2,D3` to target multiple specific drones

### 9. Set Up the Receiving Stream

Run the following command on an Ubuntu system to receive streaming data (note: this does not work on WSL):

```bash
gst-launch-1.0 -v udpsrc port=5600 caps="application/x-rtp, media=(string)video, \
clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! rtph264depay ! \
avdec_h264 ! videoconvert ! autovideosink
```

Open a new terminal instance for each drone, incrementing the port number (5600, 5601, 5602, etc.).

Alternatively, use the `automated_streamer_terminals.py` script to automate this process.

---

## Troubleshooting

- **Connection Issues:** If you cannot connect to the Pis, try power cycling them.
- **Streaming Problems:** If video output is inconsistent, restart the Pis and retry.
- **Camera Test Failures:** If the camera test produces no video output, SSH into the Pi directly and run the test. If library or installation errors occur, re-run the full setup.

---

## Support

For issues or questions, please open an issue in this repository.
