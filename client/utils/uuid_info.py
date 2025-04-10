import platform
import subprocess

def get_system_uuid_linux():
    try:
        result = subprocess.check_output(['sudo', 'dmidecode', '-s', 'system-uuid']).decode().strip()
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving system UUID on Linux: {e.output.decode()}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_system_uuid_windows():
    try:
        result = subprocess.check_output(
            ['powershell', '-Command', '(Get-WmiObject -Class Win32_ComputerSystemProduct).UUID']
        ).decode().strip()
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving system UUID on Windows: {e.output.decode()}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_system_uuid_mac():
    try:
        result = subprocess.check_output(
            "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID",
            shell=True).decode()
        uuid = result.split('"')[-2]
        return uuid
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving system UUID on MacOS: {e.output.decode()}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def normalize_uuid(uuid):
    """Normalize a UUID to contain only numbers and lowercase letters."""
    # return re.sub(r'[^a-z0-9]', '', uuid.lower())
    return uuid.lower()

def get_system_uuid():
    os_name = platform.system()

    if os_name == "Linux":
        uuid = get_system_uuid_linux()
    elif os_name == "Windows":
        uuid = get_system_uuid_windows()
    elif os_name == "Darwin":  # MacOS
        uuid = get_system_uuid_mac()
    else:
        print(f"Unsupported OS: {os_name}")
        return None

    # Normalize the UUID
    return normalize_uuid(uuid)