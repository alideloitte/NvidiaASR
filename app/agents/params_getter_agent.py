import re
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.base_agent import BaseAgent
from langchain_openai import AzureChatOpenAI

import json


GET_PARAMETER_SYSTEM_PROMPT = """###YOUR ROLE:
You are an AI assistant, responsible to write a message to the user asking information about a missing parameter.

###PARAMETER
This is the missing parameter you are looking for:
{missing_parameter}

###RULES
Here are the rules you must follow to complete your goal:
- Do NOT provide any context or explanations.
- The parameter you are looking for is specified in PARAMETER.
- Make sure the user has provided a valid option.
- Do not ask for confirmation.
- Always provide the parameter options line by line.

###EXAMPLES
User: model s200 format4b4
AI: Thank you for providing the information. Can you please provide {missing_param_desc}?
##
User: stand
AI: Thank you. Can you please provide {missing_param_desc}?
##
User: how to clean a TV (asking information on how to clean a tv)
AI: This does not seem to be related to {missing_param_desc}.
##
User: yes
AI: Can you provide {missing_param_desc}?
##
User: Paris Office Floor (not a valid option)
AI: Paris Office Floor is not a valid option. The valid options are...

###ANSWER:
Take a deep deep breath and think about your answer before you reply."""


class ParamsGetterAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
                temperature=0.1,
            )

    def write_message(self, query, state, history):

        print("\n\n***\nCALLING PARAMS GETTER AGENT\nAgent that returns a message asking for missing parameters.\nThis agent has no history or examples implemented.\nInstead it simply has access at the current state (which shows missing parameters) and the user input.\n\n")

        workflow = state.get("workflow_name", "")
        if workflow == "":
            raise ValueError("Workflow value is empty")

        select_device = state.get("select_device", "")
        if select_device == "":
            raise ValueError("Workflow value is empty")

        params_desc_list = self.workflows_description[workflow]["select_device"][select_device]["input_parameters"]

        input_parameters = state.get("input_parameters", "")
        #missing_parameter = {}
        for key, value in input_parameters.items():
            if value == "":
                #missing_parameter[key] = params_desc_list[key]
                missing_param_desc = params_desc_list[key]["description"]
                options = params_desc_list[key].get("options", [])
                break
        
        if options:
            options_str = ""
            for o in options:
                options_str += list(o.keys())[0]+"\n"
            missing_parameter = missing_param_desc + "\nWith the following options:\n" + options_str
        else:
            missing_parameter = missing_param_desc + "\n"
        params_system_msg = GET_PARAMETER_SYSTEM_PROMPT.format(missing_parameter=missing_parameter, missing_param_desc=missing_param_desc.lower())

        print("param agent system message:", params_system_msg)
        msgs = [SystemMessage(content=params_system_msg)]
        msgs += self._filter_history(history[-5:])
        msgs += [HumanMessage(content=query)]

        result = self.llm.invoke(msgs).content

        print("\nparam getter final response:\n", result)
        
        return result
    
    def _filter_history(self, history):
        print("\nFILTER HISTORY (PARAM GETTER): ", history)
        new_history = []
        for message in history:
            if message["role"] == "user":
                new_history.append(message)
            else:
                message_filtered = {}
                print("MESSAGE:", message)
                print("MESSAGE TYPE:", type(message))
                message_filtered["role"] = message["role"]
                try:
                    content = json.loads(message["content"])
                    # if the content is json it should have output_to_user key
                    output_to_user = content.get("output_to_user", None)
                    if output_to_user is None:
                        # if the content is json but there is no output_to_user key, ignore the message
                        print("Ignored: ", message)
                        continue
                    else:
                        message_filtered["content"] = output_to_user
                        new_history.append(message_filtered)    
                except json.decoder.JSONDecodeError:
                    # if the content is not json save the whole content
                    message_filtered["content"] = message["content"]
                    new_history.append(message_filtered)
        return new_history
