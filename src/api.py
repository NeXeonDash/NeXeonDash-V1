import os
import json
import requests
from dotenv import load_dotenv
import random  # Added to select a random allocation ID

load_dotenv()

PTERO_API_KEY = os.getenv('PTERO_API_KEY', 'API_KEY')
PTERO_DOMAIN = os.getenv('PTERO_DOMAIN', 'https://panel.example.com')

def create_pterodactyl_user(username, email, password):
    """
    Creates a user in the Pterodactyl panel using the application API.
    """
    headers = {
        'Authorization': f'Bearer {PTERO_API_KEY}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        "email": email,
        "username": username,
        "first_name": username,
        "last_name": "User",
        "root_admin": False,
        "password": password,
        "language": "en"
    }

    try:
        response = requests.post(f'{PTERO_DOMAIN}/api/application/users', headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("DEBUG: Failed creating user in Pterodactyl:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("DEBUG: Response content =>", e.response.text)
        return None

def update_pterodactyl_user_info(user_id, new_username=None, new_email=None, new_password=None):
    """
    Updates a user's username, email, or password in the Pterodactyl panel using the application API.
    Only fields that are not None will be updated.
    """
    headers = {
        'Authorization': f'Bearer {PTERO_API_KEY}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Fetch existing user data
    try:
        get_resp = requests.get(f'{PTERO_DOMAIN}/api/application/users/{user_id}', headers=headers)
        get_resp.raise_for_status()
        existing_data = get_resp.json().get('attributes', {})
    except requests.exceptions.RequestException as e:
        print("DEBUG: Error fetching existing user before update:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("DEBUG: Response content =>", e.response.text)
        return None

    current_username = existing_data.get('username', '')
    current_email = existing_data.get('email', '')
    current_first_name = existing_data.get('first_name', '')
    current_last_name = existing_data.get('last_name', 'User')

    data = {}
    # Update username if needed
    if new_username and new_username != current_username:
        data["username"] = new_username
        data["first_name"] = new_username
    else:
        data["username"] = current_username
        data["first_name"] = current_first_name or current_username

    # Update email if needed
    if new_email and new_email != current_email:
        data["email"] = new_email
    else:
        data["email"] = current_email

    # Update password if needed
    if new_password:
        data["password"] = new_password

    # If last_name is unavailable or empty, fallback to 'User'
    if not current_last_name:
        current_last_name = "User"
    data["last_name"] = current_last_name

    data["language"] = "en"

    try:
        response = requests.patch(f'{PTERO_DOMAIN}/api/application/users/{user_id}', headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("DEBUG: Pterodactyl user info update encountered an exception:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("DEBUG: Pterodactyl response content =>", e.response.text)
        return None

def delete_pterodactyl_user(user_id):
    """
    Deletes a user from the Pterodactyl panel using the application API.
    """
    headers = {
        'Authorization': f'Bearer {PTERO_API_KEY}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.delete(f'{PTERO_DOMAIN}/api/application/users/{user_id}', headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print("DEBUG: Failed deleting user in Pterodactyl:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("DEBUG: Response content =>", e.response.text)
        return False

def delete_pterodactyl_server(server_id):
    """
    Deletes a server from the Pterodactyl panel using the application API.
    """
    # Ensure server_id is an integer
    server_id = int(server_id)
    
    headers = {
        'Authorization': f'Bearer {PTERO_API_KEY}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    print("DEBUG: Pterodactyl delete URL =>", f'{PTERO_DOMAIN}/api/application/servers/{server_id}')
    print("DEBUG: Using API key =>", PTERO_API_KEY[:5] + '...')

    try:
        response = requests.delete(f'{PTERO_DOMAIN}/api/application/servers/{server_id}', headers=headers)
        print("DEBUG: Pterodactyl delete response status =>", response.status_code)
        print("DEBUG: Pterodactyl delete response =>", response.text)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print("DEBUG: Failed deleting server in Pterodactyl:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("DEBUG: Response content =>", e.response.text)
            print("DEBUG: Response status code =>", e.response.status_code)
        return False

def create_pterodactyl_server(owner_id, server_name, egg_id, memory=None, cpu=None, disk=None, backups=None, databases=None, version="latest"):
    """
    Creates a server in the Pterodactyl panel under a specific user (owner).
    Reads default resource limits from server_limits.json.
    """
    headers = {
        'Authorization': f'Bearer {PTERO_API_KEY}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Load default values from server_limits.json
    with open('server_limits.json', 'r') as f:
        server_limits = json.load(f)
    default_values = server_limits.get('default_values', {})
    default_memory = default_values.get('memory', 1024)  # in MB
    default_cpu = default_values.get('cpu', 100)  # in %
    default_disk = default_values.get('disk', 10240)  # in MB
    default_databases = default_values.get('databases', 0)
    default_backups = default_values.get('backups', 3)

    # Use provided values or defaults
    memory = memory if memory is not None else default_memory
    cpu = cpu if cpu is not None else default_cpu
    disk = disk if disk is not None else default_disk
    backups = backups if backups is not None else default_backups
    databases = databases if databases is not None else default_databases

    # Default (Paper)
    nest_id = 1
    numeric_egg_id = 1
    docker_image = "ghcr.io/pterodactyl/yolks:java_21"
    startup_cmd = "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar paper.jar"
    environment_vars = {
        "SERVER_JARFILE": "paper.jar",
        "MINECRAFT_VERSION": version,
        "BUILD_NUMBER": version
    }

    # If user wants vanilla
    if egg_id == "vanilla":
        numeric_egg_id = 5  # or the actual ID referencing a vanilla egg
        nest_id = 1         # assume a nest that corresponds to vanilla
        docker_image = "ghcr.io/pterodactyl/yolks:java_21"
        startup_cmd = "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar server.jar"
        environment_vars = {
            "SERVER_JARFILE": "server.jar",
            "VANILLA_VERSION": version,
            "BUILD_NUMBER": version
        }

    # Use the node ID provided (assumed to be 1)
    node_id = 1  # Node ID where servers should be created

    # Fetch available allocations
    try:
        allocations_response = requests.get(f"{PTERO_DOMAIN}/api/application/nodes/{node_id}/allocations", headers=headers)
        allocations_response.raise_for_status()
        allocations_data = allocations_response.json()
        available_allocations = [
            alloc['attributes']['id']
            for alloc in allocations_data['data']
            if not alloc['attributes']['assigned']
        ]
        if not available_allocations:
            print("No available allocations found")
            return None
        selected_allocation = random.choice(available_allocations)
    except requests.exceptions.RequestException as e:
        print("DEBUG: Failed fetching allocations:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("DEBUG: Response content =>", e.response.text)
        return None

    data = {
        "name": server_name,
        "user": owner_id,
        "egg": numeric_egg_id,
        "nest": nest_id,
        "docker_image": docker_image,
        "startup": startup_cmd,
        "environment": environment_vars,
        "limits": {
            "memory": memory,
            "swap": -1,
            "disk": disk,
            "io": 500,
            "cpu": cpu
        },
        "feature_limits": {
            "databases": databases,
            "backups": backups
        },
        "allocation": {
            "default": selected_allocation  # Use the randomly selected allocation ID
        }
    }

    try:
        response = requests.post(f"{PTERO_DOMAIN}/api/application/servers", headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("DEBUG: Failed creating server in Pterodactyl:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("DEBUG: Response content =>", e.response.text)
        return None
