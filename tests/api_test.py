import requests
from requests.auth import HTTPBasicAuth
import json
import time
import unittest
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

URL_LOCAL = "http://127.0.0.1:8000"
URL_MAIN = "https://waittvpsf4.execute-api.eu-central-1.amazonaws.com/default"

CLIENT_ID = "ki55vk3sq8i4v622oq43dspec"
CLIENT_SECRET = "1sh9fiign9riboq0iucmtl87s7eiredpj9ocqihsvd2bo3mhql9o"

TOKEN_ENDPOINT = "https://snow-nvidia-voicebot-userpool.auth.eu-central-1.amazoncognito.com/oauth2/token"

class TestBase(unittest.TestCase):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.url = URL_LOCAL

    def process_query(self, query, state, history):
        """Process a query given a state and history. 
        Always tests if time is under 29 seconds"""
        
        token = self.get_access_token(CLIENT_ID, CLIENT_SECRET)

        headers = {"Authorization": f"Bearer {token}"}

        logger.debug("Running process_query...")

        logger.debug(f"history\t-> {history}")
        logger.debug(f"state\t-> {state}")
        logger.debug(f"User\t-> {query}")
        payload = {
            "query": query,
            "state": state,
            "history": history
        }
        start_time = time.time()
        response = requests.post(f"{self.url}/process-query", json=payload, headers=headers)
        end_time = time.time()

        response_dict = json.loads(response.text)

        # ENDPOINT RESPONSE
        history = response_dict.get("history", [])
        state = response_dict.get("state", {})
        logger.debug(f"""
            HISTORY: {history}
            """)
        logger.debug(f"""
            STATE: {state}
            """)
        output_to_user = response_dict.get("output_to_user", "")

        # TODO: TEXT -> AUDIO
        logger.info(f"AI\t-> {output_to_user}")
        response_time = end_time-start_time
        logger.info(f"API RESPONSE TIME:: {response_time}")
        self.assertLess(response_time, 29)
        return output_to_user, state, history

    def get_access_token(self, client_id, client_secret):
        auth = HTTPBasicAuth(client_id, client_secret)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {"grant_type": "client_credentials"}
        response = requests.post(TOKEN_ENDPOINT, auth=auth, headers=headers, data=body)
        return response.json().get("access_token")
    
class TestEasy(TestBase):

    def test_cleaning_teminal_box_first(self):
        """Tests the time for the agent to return a response
        HOW_TO_RUN: python -m tests.chat_test
        """

        history = []
        state = {}
        query = "clean a terminal box"

        output_to_user, state, history = self.process_query(query, state, history)
        self.assertIn("location", output_to_user.lower()) # should ask for parameters

    def test_cleaning_teminal_box_second(self):
        """Tests the time for the agent to return a response
        HOW_TO_RUN: python -m tests.chat_test
        """
        history = [
            {
                'role': 'user',
                'content': 'clean a terminal box'
            }, 
            {
                'role': 'ai',
                'content': '{"output_to_user": "Sure, I can help you with that. Before we proceed, I need some additional information. Could you please provide the following details:\\n\\n1. The specification for the control cabinet.\\n2. The location of the device (options: SmartFactory Duesseldorf, SmartFactory Hannover).\\n3. The name of the device to be cleaned (options: IP-Router-1, Workstation).\\n4. An explanation of the pollution on the device.\\n5. Whether the device is freely accessible or not (options: Yes, No).\\n6. The contact that has access to the device (only required when device access is \\"No\\").\\n\\nPlease provide the missing information so that I can assist you further.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'}]
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

        query = """specification: models200,
        device located in SmartFactory Duesseldorf,
        device name is IP-Router-1,
        highly polluted,
        not free to access. access given by guicorreia@test.com
        """
        output_to_user, state, history = self.process_query(query, state, history)
        self.assertIn("confirm", output_to_user.lower())

    def test_confirmation_oky(self):
        """Test if validation agent perceives a confirmation TRUE.
        """
        print("Running test_confirmation_ok...")

        history = [{'role': 'user', 'content': 'clean a terminal box'}, {'role': 'ai', 'content': '{"output_to_user": "Sure, I can help you with that. Before we proceed, I need some additional information. Could you please provide the following details:\\n\\n1. The specification for the control cabinet.\\n2. The location of the device (options: SmartFactory Duesseldorf, SmartFactory Hannover).\\n3. The name of the device to be cleaned (options: IP-Router-1, Workstation).\\n4. An explanation of the pollution on the device.\\n5. Whether the device is freely accessible or not (options: Yes, No).\\n6. The contact that has access to the device (only required when device access is \\"No\\").\\n\\nPlease provide the missing information so that I can assist you further.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'}, {'role': 'user', 'content': 'specification: models200,\n        device located in SmartFactory Duesseldorf,\n        device name is IP-Router-1,\n        highly polluted,\n        not free to access. access given by guicorreia@test.com\n        '}, {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Just to confirm, you would like to run the \\"cleaning\\" workflow with the following parameters:\\n\\n- Specification: models200\\n- Location: SmartFactory Duesseldorf\\n- Device Name: IP-Router-1\\n- Pollution Level: highly polluted\\n- Accessibility: not freely accessible\\n- Access Granted by: guicorreia@test.com\\n\\nIs that correct? Please confirm if you would like to proceed with this workflow.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "models200", "device_location": "Smart Factory Duesseldorf", "device_to_be_cleaned": "IP-Router-1", "pollution_description": "highly polluted", "device_access": "No", "access_contact": "guicorreia@test.com"}}'}]
        state = {
            "workflow_name": "cleaning",
            "select_device": "control_cabine",
            "input_parameters": {
                "control_cabine_type": "terminal_box",
                "control_cabine_specification": "models200",
                "device_location": "Smart Factory Duesseldorf",
                "device_to_be_cleaned": "IP-Router-1",
                "pollution_description": "highly polluted",
                "device_access": "No",
                "access_contact": "guicorreia@test.com",
            },
        }

        query = """Everithing is correct."""

        output_to_user, state, history = self.process_query(query, state, history)

        self.assertIn("workflow has been called", output_to_user.lower())

    def test_confirmation_not_ok(self):
        """Test if validation agent perceives a confirmation TRUE.
        """
        print("Running test_confirmation_not_ok...")
        history = [{'role': 'user', 'content': 'clean a terminal box'}, {'role': 'ai', 'content': '{"output_to_user": "Sure, I can help you with that. Before we proceed, I need some additional information. Could you please provide the following details:\\n\\n1. The specification for the control cabinet.\\n2. The location of the device (options: SmartFactory Duesseldorf, SmartFactory Hannover).\\n3. The name of the device to be cleaned (options: IP-Router-1, Workstation).\\n4. An explanation of the pollution on the device.\\n5. Whether the device is freely accessible or not (options: Yes, No).\\n6. The contact that has access to the device (only required when device access is \\"No\\").\\n\\nPlease provide the missing information so that I can assist you further.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'}, {'role': 'user', 'content': 'specification: models200,\n        device located in SmartFactory Duesseldorf,\n        device name is IP-Router-1,\n        highly polluted,\n        not free to access. access given by guicorreia@test.com\n        '}, {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Just to confirm, you would like to run the \\"cleaning\\" workflow with the following parameters:\\n\\n- Specification: models200\\n- Location: SmartFactory Duesseldorf\\n- Device Name: IP-Router-1\\n- Pollution Level: highly polluted\\n- Accessibility: not freely accessible\\n- Access Granted by: guicorreia@test.com\\n\\nIs that correct? Please confirm if you would like to proceed with this workflow.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "models200", "device_location": "Smart Factory Duesseldorf", "device_to_be_cleaned": "IP-Router-1", "pollution_description": "highly polluted", "device_access": "No", "access_contact": "guicorreia@test.com"}}'}]
        state = {
            "workflow_name": "cleaning",
            "select_device": "control_cabine",
            "input_parameters": {
                "control_cabine_type": "terminal_box",
                "control_cabine_specification": "models200",
                "device_location": "Smart Factory Duesseldorf",
                "device_to_be_cleaned": "IP-Router-1",
                "pollution_description": "highly polluted",
                "device_access": "No",
                "access_contact": "guicorreia@test.com",
            },
        }

        query = """Wrong"""

        output_to_user, state, history = self.process_query(query, state, history)
        self.assertIn("workflow has been aborted", output_to_user.lower())
    
    def test_confirmation_unknown(self):
        """Test if validation agent perceives a confirmation TRUE.
        """
        print("Running test_confirmation_not_ok...")
        history = [{'role': 'user', 'content': 'clean a terminal box'}, {'role': 'ai', 'content': '{"output_to_user": "Sure, I can help you with that. Before we proceed, I need some additional information. Could you please provide the following details:\\n\\n1. The specification for the control cabinet.\\n2. The location of the device (options: SmartFactory Duesseldorf, SmartFactory Hannover).\\n3. The name of the device to be cleaned (options: IP-Router-1, Workstation).\\n4. An explanation of the pollution on the device.\\n5. Whether the device is freely accessible or not (options: Yes, No).\\n6. The contact that has access to the device (only required when device access is \\"No\\").\\n\\nPlease provide the missing information so that I can assist you further.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'}, {'role': 'user', 'content': 'specification: models200,\n        device located in SmartFactory Duesseldorf,\n        device name is IP-Router-1,\n        highly polluted,\n        not free to access. access given by guicorreia@test.com\n        '}, {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Just to confirm, you would like to run the \\"cleaning\\" workflow with the following parameters:\\n\\n- Specification: models200\\n- Location: SmartFactory Duesseldorf\\n- Device Name: IP-Router-1\\n- Pollution Level: highly polluted\\n- Accessibility: not freely accessible\\n- Access Granted by: guicorreia@test.com\\n\\nIs that correct? Please confirm if you would like to proceed with this workflow.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "models200", "device_location": "Smart Factory Duesseldorf", "device_to_be_cleaned": "IP-Router-1", "pollution_description": "highly polluted", "device_access": "No", "access_contact": "guicorreia@test.com"}}'}]
        state = {
            "workflow_name": "cleaning",
            "select_device": "control_cabine",
            "input_parameters": {
                "control_cabine_type": "terminal_box",
                "control_cabine_specification": "models200",
                "device_location": "Smart Factory Duesseldorf",
                "device_to_be_cleaned": "IP-Router-1",
                "pollution_description": "highly polluted",
                "device_access": "No",
                "access_contact": "guicorreia@test.com",
            },
        }

        query = """I don't know"""

        output_to_user, state, history = self.process_query(query, state, history)
        self.assertNotIn("workflow has been called", output_to_user.lower())
        self.assertNotIn("workflow has been aborted", output_to_user.lower())
        self.assertIn("location", output_to_user.lower())
        self.assertIn("pollution", output_to_user.lower())
        self.assertIn("access", output_to_user.lower())
        self.assertIn("device", output_to_user.lower())

    def test_cleaning_factory_pc_first(self):
        """Tests the time for the agent to return a response
        HOW_TO_RUN: python -m tests.chat_test
        """

        history = []
        state = {}
        query = "clean a factory pc"

        output_to_user, state, history = self.process_query(query, state, history)

class TestHard(TestBase):
    def test_cleaning_teminal_box_first_hard(self):
        """Tests the time for the agent to return a response
        HOW_TO_RUN: python -m tests.chat_test
        """

        history = []
        state = {}

        query = """how do i clean a terminal box"""

        output_to_user, state, history = self.process_query(query, state, history)
        self.assertIn("location", output_to_user.lower()) # should ask for parameters
    
    def test_confirmation_unknown_hard(self):
        """Test if validation agent perceives a confirmation TRUE.
        """
        print("Running test_confirmation_not_ok...")
        history = [{'role': 'user', 'content': 'clean a terminal box'}, {'role': 'ai', 'content': '{"output_to_user": "Sure, I can help you with that. Before we proceed, I need some additional information. Could you please provide the following details:\\n\\n1. The specification for the control cabinet.\\n2. The location of the device (options: SmartFactory Duesseldorf, SmartFactory Hannover).\\n3. The name of the device to be cleaned (options: IP-Router-1, Workstation).\\n4. An explanation of the pollution on the device.\\n5. Whether the device is freely accessible or not (options: Yes, No).\\n6. The contact that has access to the device (only required when device access is \\"No\\").\\n\\nPlease provide the missing information so that I can assist you further.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'}, {'role': 'user', 'content': 'specification: models200,\n        device located in SmartFactory Duesseldorf,\n        device name is IP-Router-1,\n        highly polluted,\n        not free to access. access given by guicorreia@test.com\n        '}, {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Just to confirm, you would like to run the \\"cleaning\\" workflow with the following parameters:\\n\\n- Specification: models200\\n- Location: SmartFactory Duesseldorf\\n- Device Name: IP-Router-1\\n- Pollution Level: highly polluted\\n- Accessibility: not freely accessible\\n- Access Granted by: guicorreia@test.com\\n\\nIs that correct? Please confirm if you would like to proceed with this workflow.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "models200", "device_location": "Smart Factory Duesseldorf", "device_to_be_cleaned": "IP-Router-1", "pollution_description": "highly polluted", "device_access": "No", "access_contact": "guicorreia@test.com"}}'}]
        state = {
            "workflow_name": "cleaning",
            "select_device": "control_cabine",
            "input_parameters": {
                "control_cabine_type": "terminal_box",
                "control_cabine_specification": "models200",
                "device_location": "Smart Factory Duesseldorf",
                "device_to_be_cleaned": "IP-Router-1",
                "pollution_description": "highly polluted",
                "device_access": "No",
                "access_contact": "guicorreia@test.com",
            },
        }

        query = """what are the parameters"""

        output_to_user, state, history = self.process_query(query, state, history)
        self.assertNotIn("workflow has been called", output_to_user.lower())
        self.assertNotIn("workflow has been aborted", output_to_user.lower())
        self.assertIn("location", output_to_user.lower())
        self.assertIn("pollution", output_to_user.lower())
        self.assertIn("access", output_to_user.lower())
        self.assertIn("device", output_to_user.lower())

    def test_confirmation_random_1_hard(self):
        """Test if validation agent perceives a confirmation TRUE.
        """
        print("Running test_confirmation_not_ok...")
        history = [{'role': 'user', 'content': 'clean a terminal box'}, {'role': 'ai', 'content': '{"output_to_user": "Sure, I can help you with that. Before we proceed, I need some additional information. Could you please provide the following details:\\n\\n1. The specification for the control cabinet.\\n2. The location of the device (options: SmartFactory Duesseldorf, SmartFactory Hannover).\\n3. The name of the device to be cleaned (options: IP-Router-1, Workstation).\\n4. An explanation of the pollution on the device.\\n5. Whether the device is freely accessible or not (options: Yes, No).\\n6. The contact that has access to the device (only required when device access is \\"No\\").\\n\\nPlease provide the missing information so that I can assist you further.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'}, {'role': 'user', 'content': 'specification: models200,\n        device located in SmartFactory Duesseldorf,\n        device name is IP-Router-1,\n        highly polluted,\n        not free to access. access given by guicorreia@test.com\n        '}, {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Just to confirm, you would like to run the \\"cleaning\\" workflow with the following parameters:\\n\\n- Specification: models200\\n- Location: SmartFactory Duesseldorf\\n- Device Name: IP-Router-1\\n- Pollution Level: highly polluted\\n- Accessibility: not freely accessible\\n- Access Granted by: guicorreia@test.com\\n\\nIs that correct? Please confirm if you would like to proceed with this workflow.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "models200", "device_location": "Smart Factory Duesseldorf", "device_to_be_cleaned": "IP-Router-1", "pollution_description": "highly polluted", "device_access": "No", "access_contact": "guicorreia@test.com"}}'}]
        state = {
            "workflow_name": "cleaning",
            "select_device": "control_cabine",
            "input_parameters": {
                "control_cabine_type": "terminal_box",
                "control_cabine_specification": "models200",
                "device_location": "Smart Factory Duesseldorf",
                "device_to_be_cleaned": "IP-Router-1",
                "pollution_description": "highly polluted",
                "device_access": "No",
                "access_contact": "guicorreia@test.com",
            },
        }

        query = """How to clean a macbook"""

        output_to_user, state, history = self.process_query(query, state, history)
        self.assertNotIn("workflow has been called", output_to_user.lower())
        self.assertNotIn("workflow has been aborted", output_to_user.lower())
        self.assertNotIn("power", output_to_user.lower())
        self.assertNotIn("cloth", output_to_user.lower())
        self.assertNotIn("keyboard", output_to_user.lower())

    def test_confirmation_random_1_hard_3_times(self):
        """Test if validation agent perceives a confirmation TRUE.
        """
        print("Running test_confirmation_not_ok...")
        history = [{'role': 'user', 'content': 'clean a terminal box'}, {'role': 'ai', 'content': '{"output_to_user": "Sure, I can help you with that. Before we proceed, I need some additional information. Could you please provide the following details:\\n\\n1. The specification for the control cabinet.\\n2. The location of the device (options: SmartFactory Duesseldorf, SmartFactory Hannover).\\n3. The name of the device to be cleaned (options: IP-Router-1, Workstation).\\n4. An explanation of the pollution on the device.\\n5. Whether the device is freely accessible or not (options: Yes, No).\\n6. The contact that has access to the device (only required when device access is \\"No\\").\\n\\nPlease provide the missing information so that I can assist you further.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'}, {'role': 'user', 'content': 'specification: models200,\n        device located in SmartFactory Duesseldorf,\n        device name is IP-Router-1,\n        highly polluted,\n        not free to access. access given by guicorreia@test.com\n        '}, {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Just to confirm, you would like to run the \\"cleaning\\" workflow with the following parameters:\\n\\n- Specification: models200\\n- Location: SmartFactory Duesseldorf\\n- Device Name: IP-Router-1\\n- Pollution Level: highly polluted\\n- Accessibility: not freely accessible\\n- Access Granted by: guicorreia@test.com\\n\\nIs that correct? Please confirm if you would like to proceed with this workflow.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "models200", "device_location": "Smart Factory Duesseldorf", "device_to_be_cleaned": "IP-Router-1", "pollution_description": "highly polluted", "device_access": "No", "access_contact": "guicorreia@test.com"}}'}]
        state = {
            "workflow_name": "cleaning",
            "select_device": "control_cabine",
            "input_parameters": {
                "control_cabine_type": "terminal_box",
                "control_cabine_specification": "models200",
                "device_location": "Smart Factory Duesseldorf",
                "device_to_be_cleaned": "IP-Router-1",
                "pollution_description": "highly polluted",
                "device_access": "No",
                "access_contact": "guicorreia@test.com",
            },
        }

        query = """How to clean a macbook"""

        # run 3 times
        for i in range(3):
            output_to_user, state, history = self.process_query(query, state, history)
            self.assertNotIn("workflow has been called", output_to_user.lower())
            self.assertNotIn("workflow has been aborted", output_to_user.lower())
            self.assertNotIn("power", output_to_user.lower())
            self.assertNotIn("cloth", output_to_user.lower())
            self.assertNotIn("keyboard", output_to_user.lower())
    
    def test_param_not_valid_option(self):
        state = {'service': 'WORKFLOW', 'workflow_name': 'cleaning', 'select_device': 'control_cabine', 'input_parameters': {'control_cabine_type': 'terminal_box', 'control_cabine_specification': 'CC1234, Version: 3', 'device_location': 'db98d96493294610d8c5f5747aba104a', 'device_to_be_cleaned': '', 'pollution_description': '', 'device_access': '', 'access_contact': ''}}
        history = [{'role': 'ai', 'content': 'How can I help?'}, 
                   {'role': 'user', 'content': 'i want to do a device cleaning'}, 
                   {'role': 'ai', 'content': 'What is the device type you need cleaning for?'}, 
                   {'role': 'user', 'content': 'what are the options?'}, 
                   {'role': 'ai', 'content': 'The available device types for cleaning are:\n- Control Cabine\n- CNC Machine\n- Factory PC'}, 
                   {'role': 'user', 'content': 'control cabine'}, 
                   {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Can you please provide the specific type of control cabinet?", "input_parameters": {"control_cabine_type": "", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'},
                   {'role': 'user', 'content': 'what are the options?'}, {'role': 'ai', 'content': '{"output_to_user": "The specific type of control cabinet can be one of the following options:\\n- StandBayed\\n- Terminal box\\n- Wall-mounted", "input_parameters": {"control_cabine_type": "", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'},
                   {'role': 'user', 'content': 'terminal box'},
                   {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Can you please provide the specification for the terminal box?", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'},
                   {'role': 'user', 'content': 'CC1234, Version: 3'}, {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Can you please provide the location of the device?", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "CC1234, Version: 3", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'},
                   {'role': 'user', 'content': 'lisbon grand hotel?'}, {'role': 'ai', 'content': '{"output_to_user": "\\"Lisbon Grand Hotel\\" is not a valid option. The valid options for the location of the device are:\\n- Smart Factory Duesseldorf\\n- Hannover Messe Booth\\n\\nCan you please provide the correct location of the device?", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "CC1234, Version: 3", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'},
                   {'role': 'user', 'content': 'Hannover Messe Booth'}, 
                   {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the location of the device. Can you please provide the name of the device to be cleaned?", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "CC1234, Version: 3", "device_location": "db98d96493294610d8c5f5747aba104a", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}'}]
        
        query = "what are the options for the device to be cleaned. can it be plc1200"

        output_to_user, state, history = self.process_query(query, state, history)

        self.assertNotIn("plc1200", output_to_user)

if __name__ == '__main__':
    unittest.main(failfast=True)
