import json

def load_role_data(json_path="role_mapping.json"):
    with open(json_path, "r") as f:
        return json.load(f)

def get_role_details(role, role_data):
    return role_data.get(role, f"No data found for role: {role}")
