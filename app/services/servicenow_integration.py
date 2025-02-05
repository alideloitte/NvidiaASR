import requests
import json
import os
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv("config/.env")

workflow_sys_id = {
    "cleaning": "21330d38db35c510027550e4e2961982"
}

def call_servicenow(state):
    print("\n****CALLING SERVICENOW API****\n")

    # Service domain
    SN_URL = "https://deloittedesscpdemo.service-now.com"

    # Endpoint
    workflow_name = "cleaning"
    sys_id = workflow_sys_id.get(workflow_name)

    endpoint = f"api/sn_sc/servicecatalog/items/{sys_id}/order_now"

    #Payload
    input_parameters = state.get("input_parameters")
    input_parameters["select_device"] = state.get("select_device")

    payload = {"sysparm_quantity": 1, "variables": input_parameters}

    print(f"Payload: {payload}")

    USER = os.getenv("SN_USER")
    PASSWORD = os.getenv("SN_PWD")
    auth = HTTPBasicAuth(USER, PASSWORD)
    headers = {"Content-Type": "application/json"}
    

    # Send request
    response = requests.post(f"{SN_URL}/{endpoint}", auth=auth, headers=headers, json=payload)
    if response.ok:
        response = json.loads(response.text)
        number = response.get("result", {}).get("number", "")
        if not number:
             raise ValueError(f"Number not present in ServiceNow response: {response.text}")
        return number
    else:
        raise ConnectionError(f"Error getting response from ServiceNow. STATUS CODE: {response.status_code}: {response.text}")


if __name__ == "__main__":
    state = {
        "workflow": "cleaning",
        "select_device": "control_cabine",
        "input_parameters": {
            "control_cabine_type": "terminal_box",
            "control_cabine_specification": "models200",
            "device_location": "db98d96493294610d8c5f5747aba104a",
            "device_to_be_cleaned": "IP-Router-1",
            "pollution_description": "highly polutted",
            "device_access": "Yes",
        },
    }
    number = call_servicenow(state)
    print(number)
