import requests
import json
import time
import unittest


class TestAPI(unittest.TestCase):
    def cleaning_teminal_box(self):
        """Tests the time for the agent to return a response
        HOW_TO_RUN: python -m tests.chat_test
        """
        URL_LOCAL = "http://127.0.0.1:8000"

        url = URL_LOCAL

        history = [
            {"role": "user", "content": "clean a terminal box"},
            {
                "role": "ai",
                "content": '{"output_to_user": "Please provide the specification for the control cabinet, the location of the device, whether the device is freely accessible or not, and if not, the contact that has access to the device.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}, "ai_thoughts": "The user has specified the control cabinet type as \'terminal box\', which is a valid option. However, further details such as control cabinet specification, device location, device access, and access contact (if applicable) are required to proceed. The user has not provided information about the device to be cleaned or pollution description, but they are currently not mandatory."}',
            },
        ]
        state = {
            "workflow_name": "cleaning",
            "select_device": "control_cabine",
            "input_parameters": {
                "control_cabine_type": "terminal_box",
                "control_cabine_specification": "",
                "device_location": "",
                "device_to_be_cleaned": "",
                "pollution_description": "",
                "device_access": "",
                "access_contact": "",
            },
        }
        query = "clean a terminal box"
        print(f"history\t-> {history}")
        print(f"state\t-> {state}")
        print(f"User\t-> {query}")
        payload = {"query": query, "state": state, "history": history}
        start_time = time.time()
        response = requests.post(f"{url}/process-query", json=payload)
        end_time = time.time()

        response_dict = json.loads(response.text)

        # ENDPOINT RESPONSE
        history = response_dict.get("history", [])
        state = response_dict.get("state", {})
        print(
            f"""
            HISTORY: {history}
            """
        )
        print(
            f"""
            STATE: {state}
            """
        )
        output_to_user = response_dict.get("output_to_user", "")

        # TODO: TEXT -> AUDIO
        print(f"AI\t-> {output_to_user}")
        response_time = end_time - start_time
        print(f"API RESPONSE TIME:: {response_time}")
        self.assertLess(response_time, 30)


if __name__ == "__main__":
    unittest.main()
