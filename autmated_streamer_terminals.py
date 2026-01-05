#automated_streamer_terminals.py
#!/usr/bin/env python3
import subprocess

def launch_gstreamer_viewers(num_drones, base_port=5600):
    for i in range(num_drones):
        port = base_port + i
        label = f"D{i+1}"
        gst_cmd = (
            f'gst-launch-1.0 -v udpsrc port={port} '
            'caps="application/x-rtp, media=(string)video, '
            'clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" '
            '! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink'
        )
        subprocess.Popen([
            "gnome-terminal",
            "--title", f"{label}_stream",
            "--", "bash", "-c", f"{gst_cmd}; exec bash"
        ])
        print(f"Opened terminal for {label} (port {port})")

def main():
    try:
        count = int(input("How many drones are streaming? ").strip())
        if count < 1:
            print("Error: Must be at least 1 drone.")
            return
        launch_gstreamer_viewers(count)
    except ValueError:
        print("Error: Invalid number entered.")

if __name__ == "__main__":
    main()
