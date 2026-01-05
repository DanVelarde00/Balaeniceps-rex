#!/usr/bin/env python3
import subprocess
import re

RASPBERRY_PI_PREFIX = ["b8-27-eb", "dc-a6-32", "e4-5f-01", "28-cd-c1", "2c-cf-67", "d8-3a-dd"]
SUBNET = "192.168.148.0/24"

def ask_user_if_connected():
    answer = input("Have you connected all drones in the area? (yes/no): ").strip().lower()
    return answer in ["yes", "y"]

def run_nmap_scan(subnet):
    print(f"Scanning network with nmap on {subnet}...")
    try:
        subprocess.run(["nmap", "-sn", subnet], check=True)
        print("Nmap scan complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: Nmap scan failed: {e}")
        return False

def get_windows_arp_table():
    try:
        output = subprocess.check_output(
            ["powershell.exe", "arp -a"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error running arp -a via PowerShell: {e}")
        return ""

def extract_raspberry_pi_ips(arp_output):
    raspberry_pi_ips = []
    pattern = re.compile(r"\s+([\d.]+)\s+([0-9a-fA-F:-]{17})\s+dynamic", re.IGNORECASE)

    for match in pattern.finditer(arp_output):
        ip = match.group(1)
        mac = match.group(2).lower().replace(":", "-")
        if mac.startswith(tuple(RASPBERRY_PI_PREFIX)):
            raspberry_pi_ips.append(ip)

    return raspberry_pi_ips

def save_to_file(ips, filename="ssh_hosts.txt"):
    with open(filename, "w") as f:
        for ip in ips:
            f.write(f"{ip}\n")
    print(f"Saved {len(ips)} Raspberry Pi IP(s) to {filename}")

def main():
    nmap_ran = False

    if not ask_user_if_connected():
        nmap_ran = run_nmap_scan(SUBNET)

    print("Fetching ARP table from Windows via PowerShell...")
    arp_output = get_windows_arp_table()
    pi_ips = extract_raspberry_pi_ips(arp_output)

    if pi_ips:
        for ip in pi_ips:
            print(f"Raspberry Pi -> {ip}")
        save_to_file(pi_ips)
    else:
        if not nmap_ran:
            print("Warning: No Raspberry Pis found. Try scanning the network first.")
            rerun = input("Would you like to run a scan now? (yes/no): ").strip().lower()
            if rerun in ["yes", "y"]:
                run_nmap_scan(SUBNET)
                print("Re-checking ARP table...")
                arp_output = get_windows_arp_table()
                pi_ips = extract_raspberry_pi_ips(arp_output)
                if pi_ips:
                    for ip in pi_ips:
                        print(f"Raspberry Pi -> {ip}")
                    save_to_file(pi_ips)
                    return
        print("Error: No Raspberry Pi devices found.")

if __name__ == "__main__":
    main()
