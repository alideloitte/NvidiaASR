from app.agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage, SystemMessage


WF_CLASSIFIER_SYSTEM_PROMPT = """###YOUR ROLE:
You are an AI workflow classifier. 

###GOAL:
Your goal is to determine the Shop Floor Service that user wants to call, based on the input provided.

###SHOP FLOOR SERVICES
Possible Shop Floor Services you can choose from:
{workflows_description}

###EXAMPLES
User: i want to submit a shop floor service
Assistant: The available Shop Floor Service options are: cleaning.
##
User: I need to query a knowledge base article
Assistant: KB_ARTICLE

###RULES
Here are the rules you must follow to complete your goal:
- Your answer should ONLY contain the name of the Shop Floor Services
- Do not provide any context or explanations if you know the Shop Floor Service name.
- You should maintain a friendly but formal user service tone.
- If the input does not seem to be related with one of the Shop Floor Services defined, ask the user to reformulate.

###ANSWER:
How do you classify the input provided?
Take a deep breath and think about your answer first before you reply."""


class WorkflowAgent(BaseAgent):

    def get_workflow(self, query: str) -> str:
        print("\n\n***\nCALLING WORKFLOW AGENT\nAgent that returns which workflow the user is trying to run.\nThis agent has no history or examples implemented.\n\n")
        summarized_wf = [{"workflow_name": wf["workflow_name"], "workflow_description": wf["workflow_description"]} for wf in self.workflows_description.values()]
        
        wf_system_prompt = WF_CLASSIFIER_SYSTEM_PROMPT.format(workflows_description=summarized_wf)
        print(f"\n**workflow agent system prompt::\n{wf_system_prompt}\n")
        msgs = [
            SystemMessage(content=WF_CLASSIFIER_SYSTEM_PROMPT.format(workflows_description=summarized_wf)),
            HumanMessage(content=query)
        ]
        
        result = self.llm.invoke(msgs).content
        print(f"\n**workflow agent response: {result}")
        return result

    def validate_workflow(self, workflow_name: str) -> bool:
        """
        Validates if the workflow name provided is one of the possible workflows
        """

        workflow_names_list = self.workflows_description.keys()
        workflow_validated = workflow_name in workflow_names_list
        print("\n**validating workflow...\nworkflow validated:", workflow_validated)
        return workflow_validated
