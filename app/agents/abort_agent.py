from app.agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage, SystemMessage
import json

ABORT_SYSTEM_PROMPT = """###YOUR ROLE:
    You are an agent that analyzes a user message and determines if the user wants to abort.

    ###GOAL:
    Your goal is to return ABORT if the user wants to abort, or CONTINUE otherwise
    Only return "ABORT" or "CONTINUE" 

    ###EXAMPLES
    
    example 1:
        User: I need to do some cleaning
        Assistant: CONTINUE
    example 2:
        User: cancel
        Assistant: ABORT
    example 3:
        User: lets start over
        Assistant: ABORT
    
    ###ANSWER:
    CLassify if the user wants to abort.
    Take a deep breath and think about your answer first before you reply."""


class AbortAgent(BaseAgent):

    def user_abort(self, query: str) -> str:
        print("\n\n***\nCALLING ABORT AGENT\nAgent that returns wether the user wants to abort\n\n")

        print(f"\nabort agent system prompt::\n{ABORT_SYSTEM_PROMPT}\n")

        msgs = [SystemMessage(content=ABORT_SYSTEM_PROMPT)]
        msgs += [HumanMessage(content=query)]
        
        result = self.llm.invoke(msgs).content

        print(f"\nabort agent response: {result}\n\n")


        return result == "ABORT"
