from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import MessagesPlaceholder
from app.agents.base_agent import BaseAgent

import json


VALIDATION_SYSTEM_PROMPT = """###YOUR ROLE:
You are an AI validator responsible for determining whether a user is confirming running a workflow.

###PARAMETERS
The workflow being called is the following:
{workflow_name}: {workflow_description}

###EXAMPLES:
##
messages:
    AI:     {{"output_to_user": "Do you confirm?", "user_confirmation": "UNKNOWN"}}
    User:   location is hannover (user informs about a wrong parameter)
your response:
    {{"user_confirmation": "UNKNOWN", ai_thoughts:"The user did not explicitly confirmed the call of the cleaning workflow."}}

##
messages:
    AI:     {{"output_to_user": "Do you confirm?", "user_confirmation": "UNKNOWN"}}
    User:   yes/correct
your response:
    {{"user_confirmation": "TRUE", ai_thoughts:"The user explicitly confirmed the call of the cleaning workflow."}}

##
messages:
    AI:     {{"output_to_user": "Do you confirm?", "user_confirmation": "UNKNOWN"}}
    User:   no
your response:
    {{"user_confirmation": "FALSE", ai_thoughts:"The user wants to abort"}}

##
messages:
    AI:     {{"output_to_user": "Do you confirm?", "user_confirmation": "UNKNOWN"}}
    User:   can i call it later?
your response:
    {{"user_confirmation": "FALSE", ai_thoughts:"The user wants to abort"}}

##
messages:
    AI:     {{"output_to_user": "Would you like to abort?", "user_confirmation": "UNKNOWN"}}
    User:   yes
your response:
    {{"user_confirmation": "FALSE", ai_thoughts:"The user wants to abort."}}

##
messages:
    AI:     {{"output_to_user": "Do you confirm?", "user_confirmation": "UNKNOWN"}}
    User:   the device is not free to access
your response:
    {{"user_confirmation": "UNKNOWN", ai_thoughts:"The user wants to abort."}}

###ANSWER:
Is the user confirming the workflow procedure? 
Take a deep deep breath and think about your answer first before you reply.
"""


class ValidationAgent(BaseAgent):
    """Validation Agent: determines if the user confirmed on calling the workflow.
    This agent should determine wether the user wants to confirm, or abort the workflow, returning either TRUE or FALSE.
    When the agent is not sure what the user intention is, returns UNKNOWN.
    This validation is done using examples, present in the system prompt, as well as history (only last 2 messages - one from the user and one from the confirmation agent)
    """

    def validate_workflow_call(self, query, state, history):
        """Main function of Validation Agent, processes the user query based on the system prompt.
        
        Args:
            query (str): the user query
            state (dict): conversation state 
            history (list): conversation history, only last two messages are used

        Returns:
            str: the agent's response
        """
        print("\n\n***\nCALLING VALIDATION AGENT\nAgent that returns whether the user confirms the call of the workflow.\nThis agent has examples in the system prompt, as well as history (only last two messages).\n\n")
        workflow_name = state.get("workflow_name", "")
        input_parameters = state.get("input_parameters", "")
        if workflow_name == "":
            raise ValueError("Workflow value is empty")

        workflow_description = json.dumps(
            self.workflows_description[workflow_name]["workflow_description"]
        )
        select_device = state.get("select_device", "")
        if select_device == "":
            raise ValueError("select_device value is empty")

        params_desc_list = json.dumps(
            self.workflows_description[workflow_name]["select_device"][select_device][
                "input_parameters"
            ]
        )

        val_system_msg = VALIDATION_SYSTEM_PROMPT.format(
                    workflow_name=workflow_name,
                    workflow_description=workflow_description,
                    input_parameters=input_parameters,
                    params_desc_list=params_desc_list,
                )
        
        print("--validation agent system prompt\n", val_system_msg)


        msgs = [
            SystemMessage(
                content=val_system_msg
            )
        ]
        history = self._filter_history(history[-2:])
        msgs += history
        print("--validation agent history(filtered)\n", history)
        msgs += [HumanMessage(content=query)]

        result_json = self.llm.invoke(msgs).content

        try:
            result = json.loads(result_json)
        except:
            result = {"user_confirmation": "UNKNOWN"}

        print(f"\n--validation agent response: {result}")

        return result

    def _filter_history(self, history):
        print("\n--validation agent history filtering.\nthe history is filtered to include only the output to user, and a new parameter, user_confirmation is added = UNKNOWN")
        
        new_history = []
        if history:
            for message in history:
                if message["role"] == "user":
                    new_history.append(message)
                else:
                    message_filtered = {}
                    message_filtered["role"] = message["role"]
                    content = json.loads(message["content"])
                    message_filtered["content"] = {
                        "output_to_user": content["output_to_user"]
                    }
                    message_filtered["content"]["user_confirmation"] = "UNKNOWN"
                    message_filtered["content"] = json.dumps(message_filtered["content"])
                    new_history.append(message_filtered)
        return new_history


if __name__ == "__main__":
    state = {'workflow_name': 'cleaning', 'select_device': 'control_cabine', 'input_parameters': {'control_cabine_type': 'terminal_box', 'control_cabine_specification': 'model s200', 'device_location': 'Smart Factory Duesseldorf', 'device_to_be_cleaned': 'IP-Router-1', 'pollution_description': 'highly polluted', 'device_access': 'Yes', 'access_contact': ''}}
    history = [{'role': 'user', 'content': 'clean a terminal box'}, {'role': 'ai', 'content': '{"output_to_user": "Sure, I can help you with that. Before we proceed, I need some additional information. Please provide the following details:\\n\\n1. The specification for the control cabinet.\\n2. The location of the device (options: Smart Factory Duesseldorf, Smart Factory Hannover).\\n3. The name of the device to be cleaned (options: IP-Router-1, Workstation).\\n4. An explanation of the pollution on the device.\\n5. Whether the device is freely accessible or not (options: Yes, No).\\n6. The contact that has access to the device (only required when device access is \\"No\\").\\n\\nPlease provide the missing information so that I can assist you further.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}'}, {'role': 'user', 'content': 'model s200, located in duesseldorf. the name of the device is IP-Router-1 and is free to access'}, {'role': 'ai', 'content': '{"output_to_user": "I\'m glad to hear that the device \\"IP-Router-1\\" is free to access. However, I still need some additional information from you. Could you please provide me with an explanation of the pollution on the device? Additionally, if applicable, please provide the contact that has access to the device. Thank you!", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "model s200", "device_location": "Smart Factory Duesseldorf", "device_to_be_cleaned": "IP-Router-1", "pollution_description": "", "device_access": "Yes", "access_contact": ""}}'}, {'role': 'user', 'content': 'highly polluted'}, {'role': 'ai', 'content': '{"output_to_user": "Thank you for providing the information. Based on the details you have provided, I understand that you would like to run the workflow for ordering a device cleaning for the IP-Router-1 located in Duesseldorf, which is highly polluted. \\n\\nBefore proceeding with the cleaning, we just want to confirm if you are sure about running this workflow. Are you certain that you would like to proceed with ordering a cleaning for the IP-Router-1 device in its current state? Please let us know your confirmation.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "model s200", "device_location": "Smart Factory Duesseldorf", "device_to_be_cleaned": "IP-Router-1", "pollution_description": "highly polluted", "device_access": "Yes", "access_contact": ""}}'}, {'role': 'user', 'content': 'not sure'}, {'role': 'ai', 'content': '{"output_to_user": "I understand that you are not sure about proceeding with ordering a cleaning for the IP-Router-1 device. It\'s important to make an informed decision before proceeding with any workflow.\\n\\nIf you need any further information or assistance, please let me know. I\'m here to help.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "model s200", "device_location": "Smart Factory Duesseldorf", "device_to_be_cleaned": "IP-Router-1", "pollution_description": "highly polluted", "device_access": "Yes", "access_contact": ""}}'}]
    query = "how to clean a macbook?"

    import time
    from app.agents.confirmation_agent import ConfirmationAgent
    start = time.time()
    agent_v = ValidationAgent()
    result = agent_v.validate_workflow_call(query, state, history)
    end = time.time()
    print("VALIDATION::::", result)
    print(end-start)
    agent_c = ConfirmationAgent()
    start = time.time()
    result = agent_c.ask_user_confirmation(query, state, history)
    end = time.time()
    print(end-start)