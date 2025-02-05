from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import MessagesPlaceholder
from app.agents.base_agent import BaseAgent

import json

from app.utils.get_state_with_labels import get_state_with_labels


CONFIRMATION_SYSTEM_PROMPT = """###YOUR ROLE:
    You are an AI validator responsible for determining whether a user is positive about running a workflow.

    ###GOAL:
    Compose a message to the user asking for confirmation, given a workflow.

    ###PARAMETERS
    The workflow and parameters are the following:
    {workflow_and_parameters}

    These are the parameters descriptions:
    {params_desc_list}
   
    ###PROCESS
    This is the process you should follow to accomplish your goal:
    - First, check what is the workflow being called and the respective parameters
    - Next, compose a user friendly message asking if the user confirms the calling of the workflow with the given parameters
    - If the users asks for the parameters, give him the values for the parameters provided by the user.

    ###EXAMPLE
    example 1:
        User: what are the parameters?
        AI: {{show the parameters with an introductory message}}
            - Device Location: Smart Factory Duesseldorf
            - Device to be Cleaned: IP-Router-1
            - Pollution Description: Carbon dioxide
            - Device Access: Yes
            - Access Contact: Not provided
    example 2:
        User: how to clean a macbook (input not related with the confirmation of the workflow)
        AI: {{message stating you can't help with cleaning a macbook, then ask for confirmation calling the workflow}}    

    ###RULES
    Here are the rules you must follow to complete your goal:
    - Only ask the user if he confirms the workflow.
    - To respond to the user, reply in the same language as the user input.
    - If the input does not seem to be related with the confirmation of the workflow, ask the user to reformulate.
    - NEVER answer questions, simply ask for the confirmation.
    - It is NOT possible to change values at this moment.

    ###ANSWER:
    Take a deep deep breath and think about your answer first before you compose the output message
    """


class ConfirmationAgent(BaseAgent):
    """Confirmation Agent: asks the user for confirmation on calling the Workflow
    Has examples in the system prompt to guide its behaviour."""
    def ask_user_confirmation(self, query:str, state:dict, history:list) -> str: #TODO: Remove history arg, not used
        """Main function of Knowledge Agent, processes the user query based on the system prompt.

        Args:
            query (str): the user query
            state (dict): conversation state 
            history (list): conversation history, not used

        Returns:
            str: the agent's response, asking for the user's confirmation
        """
        print("\n\n***\nCALLING CONFIRMATION AGENT\nAgent that asks user for confirmation\n\n")
        workflow_name = state.get("workflow_name", "")
        select_device = state.get("select_device", "")
        if select_device == "":
            raise ValueError("Workflow value is empty")
        

        params_desc_list = json.dumps(self.workflows_description[workflow_name]["select_device"][select_device]["input_parameters"])
        state_with_labels = get_state_with_labels(state)
        conf_system_prompt = CONFIRMATION_SYSTEM_PROMPT.format(
                        workflow_and_parameters = state_with_labels,
                        params_desc_list=params_desc_list)
        print("--confirmation agent system prompt:", conf_system_prompt)
        msgs = [SystemMessage(content=conf_system_prompt)]
        
        msgs += [HumanMessage(content=query)]
        
        result = self.llm.invoke(msgs).content

        print(f"CONFIRMATION AGENT RESULT:\n{result}\n")

        return result

    # TODO: Remove this function
    def _filter_history(self, history):
        print("\nFILTER HISTORY (CONFIRMATION): ", history)
        new_history = []
        for message in history:
            if message["role"] == "user":
                new_history.append(message)
            else:
                message_filtered = {}
                message_filtered["role"] = message["role"]
                content = json.loads(message["content"])
                message_filtered["content"] = content["output_to_user"]
                new_history.append(message_filtered)
        return new_history