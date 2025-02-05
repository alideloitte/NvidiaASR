import re
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.base_agent import BaseAgent
from langchain_openai import AzureChatOpenAI

import json

HANDLE_STATE_SYSTEM_PROMPT = """###YOUR ROLE:
You are an AI assistant, responsible for determining workflow parameters.

###GOAL:
Your goal is to extract information about workflow parameters, based on the input provided by the user.

###PARAMETERS
The parameters you are looking for are described in the following json:
{params_desc_list}
The json is composed of {{"parameter_name": {{"description": parameter_description, "options": parameter_options}}, containing the parameter name, the corresponding parameter description and the available options for the parameter. 
Some parameters don't have options.

###STATE
This is the parameters you have determined so far:
{{"input_parameters": {input_parameters_state}}}
You may update populated values.

###PROCESS
This is the process you should follow to accomplish your goal:
- First, try to determine the input_parameters present in STATE, following the RULES.
- If you cannot infer a value for one of the input_parameters, the parameter is missing.
- The value returned for a missing parameter must be an empty string ("")
- Finally, respond in JSON, by filling the empty values in STATE.

###RULES
Here are the rules you have to follow to complete the PROCESS:
- If the parameter has options composed of label:value pairs store only the value.
- Before you answer, validate each of the values you set for the parameters. Has the user provided the information?
- If the user input is empty don't change the parameters.

###EXAMPLES:

AI: {{"output_to_user": "Please provide the device location.", "input_parameters": {{"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}}}
USER: Hannover Messe Booth
AI: {{"input_parameters": {{"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "db98d96493294610d8c5f5747aba104a", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}}}

##

AI: {{"output_to_user": "What is the device type?", "input_parameters": {{"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}}}
USER: Factory PC
AI: {{"input_parameters": {{"device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""}}}}

###ANSWER:
Take a deep deep breath and think about your answer first before you reply."""


class StateHandlerAgent(BaseAgent):
    def __init__(self) -> None:
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-35-turbo",
            model_name="gpt-35-turbo",
            azure_endpoint="https://gen-ai-snow-bot.openai.azure.com/",
            openai_api_version="2024-02-15-preview",
            openai_api_key="a89d3e8a6f184edaa61957e4e98063e6",
        )
        self._get_env()

    def update_state(self, query, state, history):
        print(
            "\n\n***\nCALLING STATE HANDLER AGENT\nAgent that fills in the input parameteres\nThis agent has history and examples\n"
        )
        workflow = state.get("workflow_name", "")
        if workflow == "":
            raise ValueError("Workflow value is empty")

        select_device = state.get("select_device", "")
        if select_device == "":
            raise ValueError("Workflow value is empty")

        params_desc_list = self.workflows_description[workflow]["select_device"][
            select_device
        ]["input_parameters"]

        input_parameters = state.get("input_parameters", "")
        missing_parameters = {}
        example_parameters = {}
        for param_name, param_description in params_desc_list.items():
            if input_parameters.get(param_name, "") == "":
                missing_parameters[param_name] = param_description
            example_parameters[param_name] = ""
        
        # Example messages
        # example_messages = "User: clean Factory PC\nAI: " + json.dumps(
        #             {
        #                 "input_parameters": {
        #                     "device_location": "",
        #                     "device_to_be_cleaned": "",
        #                     "pollution_description": "",
        #                     "device_access": "",
        #                     "access_contact": "",
        #                 }, "ai_toughts": "_SOME THOUGHTS YOU MAY HAVE_"
        #             }) + "\n"
        
        state_system_msg = HANDLE_STATE_SYSTEM_PROMPT.format(
            params_desc_list=json.dumps(missing_parameters),
            answer_template=json.dumps(example_parameters),
            input_parameters_state=json.dumps(state.get("input_parameters", ""),)
            # example_messages = example_messages
        )

        msgs = [SystemMessage(content=state_system_msg)]

        print("\n--state handler agent. system prompt\n", state_system_msg)

        print("\n--state handler agent. example messages are in system prompt")

        # History
        filtered_history = self._filter_history(history[-5:])
        msgs += filtered_history

        print("\n--state handler history (filtered):", filtered_history)

        msgs += [HumanMessage(content=query)]

        result = self.llm.invoke(msgs).content

        try:
            result_json = json.loads(result)
        except json.decoder.JSONDecodeError:
            print(
                "**WARNING: state handler agent did not produce a json response:\t",
                result,
            )
            print("---Will try to extract the json using regex or undo the response of the agent to its last.")
            result_json_text = get_input_parameters(result, state)
            print("----returned:", result_json_text)
            result_json = json.loads(result_json_text)

        
        print("\n--state handler response before helper functions::\t", result_json)

        try:
            # updates invalid options to empty, INPLACE
            self.check_options(result_json, params_desc_list)

            # check if input parameters dictionary has all the parameters vs. only the filled ones. INPLACE
            self.check_parameters(result_json, params_desc_list)
        except ValueError as e:
            print("invalid result from state handler, resetting to latest value...")
            print("\n--state handler response::\t", result_json)
            return {"input_parameters": state.get("input_parameters", "")}
        
        print("\n--state handler response::\t", result_json)

        return result_json

    def check_parameters(self, agent_response: dict, input_desc: dict):
        """Makes sure the agent response always has all the parameters.
        If some parameters are missing they are added to the agent's
        response with an empty result.

        Args:
            agent_response (dict): the original response from the agent
            input_desc (dict): the inputs descriptions containing the parameters
        """
        print(
            "\n*state handler parameters check.\nMakes sure the agent response always has all the parameters.\nIf some parameters are missing they are added to the agent's response with an empty result."
        )
        print("original agent response:", agent_response)
        input_parameters = agent_response.get("input_parameters")
        if input_parameters is None:
            raise ValueError("No input parameters.")
        for k in input_desc.keys():
            if input_parameters.get(k, "--nan--") == "--nan--":
                input_parameters[k] = ""

    def check_options(self, agent_response: dict, input_desc: dict):
        """Deletes invalid options from the state handler agent output. INPLACE

        Args:
            agent_response (dict): the original response from the agent
            input_desc (dict): the inputs descriptions containing the possible options
        """
        print(
            "\n*state handler options check.\ndeletes invalid options from the state handler agent output."
        )
        input_parameters = agent_response.get("input_parameters")
        
        if input_parameters is None:
            raise ValueError("No input parameters.")
        
        for k, v in input_parameters.items():
            if v:
                options = input_desc[k].get("options", "")
                if options != "":
                    options_values = [list(o.values())[0] for o in options]
                    if v not in options_values:
                        print(f"\invalid option corrected {k}: {v}\n")
                        input_parameters[k] = ""

    def _filter_history(self, history):
        print(
            "\n*state handler history filter.\nthe agent can only see the outputs it generated (the input parameters)"
        )
        new_history = []
        for message in history:
            if message["role"] == "user":
                new_history.append(message)
            else:
                message_filtered = {}
                message_filtered["role"] = message["role"]
                try:
                    content = json.loads(message.get("content"))
                    message_filtered["content"] = message.get("content") 
                    # (
                    #     '{"input_parameters":'
                    #     + json.dumps(content["input_parameters"])
                    #     + "}"
                    # )
                    new_history.append(message_filtered)
                except:
                    print("Ignored: ", message)
        return new_history


def get_input_parameters(text: str, state: dict) -> str:
    """
    Extract a json that is in quotes from the given text.
    """
    return ('{"input_parameters":' + json.dumps(state.get("input_parameters", "")) + "}")


if __name__ == "__main__":

    history = [
        {"role": "user", "content": "clean a terminal box"},
        {
            "role": "ai",
            "content": '{"output_to_user": "Please provide the device location.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""} }',
        },
        # {"role": "user", "content": "specification is model s200"},
        # {
        #     "role": "ai",
        #     "content": '{"output_to_user": "Please provide the location of the device, whether the device is freely accessible or not, and if not, the contact that has access to the device.", "input_parameters": {"control_cabine_type": "terminal_box", "control_cabine_specification": "model s200", "device_location": "", "device_to_be_cleaned": "", "pollution_description": "", "device_access": "", "access_contact": ""} }',
        # },
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

    query = "hannover messe booth"
    

    state_handler = StateHandlerAgent()
    response = state_handler.update_state(query, state, history)
    print("\n\nhistory =", history)
    print("\n\nstate =", state)
    print("\n\nquery =", query)

    print("\n\nstate_handler response = ", response)
    # print("\nINPUT_PARAMETERS:")
    # input_params = response.get("input_parameters")
    # for k, v in input_params.items():
    #     print(f'\t{k}:\t"{v}"')


""" PROBLEMS FOUND
    1.  first input: clean factory pc
        problem: automatically sets location to Smart Factory Duesseldorf
        IDEAS: add more examples to messages

    2.  inputs: clean a macbook
                duesseldorf, hihly polluted
                no
        problem: JSON decode error, no input_parameters in state handler response
"""
