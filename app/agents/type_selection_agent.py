from app.agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage, SystemMessage
import json

TYPE_SELECTOR_SYSTEM_PROMPT = """###YOUR ROLE:
You are a Type Classifier agent.

###GOAL:
Your goal is to determine the device type the user is trying to process, based on the input provided.

###TYPES
The following information is a definition of the possible types of devices you can choose from:
{types_descriptions}

###PROCESS
Here is the process you must follow to complete your goal:
- Try to determine the type name
- The type name must be one in the list of TYPES
- To inform the user, reply in the same language as the user input.

###RULES
Here are the rules you must follow to complete the PROCESS:
- Your answer should ONLY contain the name of the device type.
- Do not provide any context or explanations if you know the device type name.
- If the input does not seem to be related with one of the types defined, inform the user about the available types.
- if the input is unclear, ask the user to reformulate.

###EXAMPLES
User: I need to do some cleaning
Assistant: What is the device type you need cleaning for? {types_beautified}\n
##
User: what are the options?
Assistant: {types_beautified}\n
##
User: clean a printer
Assistant: I apologize, but printer is not a valid option. {types_beautified}\n
##
User: I need to clean a cnc machine
Assistant: cnc_machine
##
User: PC
Assistant: factory_pc

###ANSWER:
Take a deep breath and think about your answer first before you reply."""


class TypeSelectionAgent(BaseAgent):

    def get_type(self, query: str, state: dict, history: list) -> str:
        print("\n\n***\nCALLING TYPESELECTION AGENT\nAgent that returns what type is the device to be cleaned.\nThis agent has no history or examples implemented.\n\n")
        workflow_name = state.get("workflow_name", "")
        if workflow_name == "":
            raise ValueError("Workflow value is empty")
        
        select_device_list = self.workflows_description[workflow_name].get("select_device")
        summarized_types = {}
        for k, v in select_device_list.items():
            summarized_types[k] = {"type_name": v.get("type_name"), "type_description": v.get("type_description")}

        types_beautified = ""
        for k in summarized_types.keys():
            types_beautified += self.parameters_helpers[workflow_name][k] + "\n"
        

        type_system_prompt = TYPE_SELECTOR_SYSTEM_PROMPT.format(types_descriptions=json.dumps(summarized_types), types_beautified=types_beautified)
        print(f"\ntype agent system prompt::\n{type_system_prompt}\n")

        msgs = [SystemMessage(content=type_system_prompt)]
        msgs += history[-2:]
        print("-- type_selection agent history:", history[-2:])
        msgs += [HumanMessage(content=query)]
        
        
        result = self.llm.invoke(msgs).content

        print(f"\ntype agent response: {result}\n\n")

        return result

    def validate_type(self, workflow_name, type_name: str) -> bool:
        """
        Validates if the type name provided is one of the possible types
        """
        select_device_list = self.workflows_description[workflow_name].get("select_device")
        type_names_list = select_device_list.keys()
        
        type_validated = type_name in type_names_list

        print("\n**validating type...\ntype validated:", type_validated)
        return type_validated
