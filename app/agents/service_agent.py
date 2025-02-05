from app.agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage, SystemMessage
import json

SERVICE_SYSTEM_PROMPT = """###YOUR ROLE:
You are an agent that analyzes a user message and determines the service a user wants to call.
It can either be a Shop Floor Service request or a Knowledge Base Article query.

##
These are the ONLY available Shop Floor Services:
{workflows}

##
These are the ONLY available Knowledge Articles:
{kb_articles}

### GOAL
Your goal is to return WORKFLOW or KB_ARTICLE.
If the user seems to want to submit one of the available Shop Floor Services, return WORKFLOW.
If the user seems to want to query knowledge articles return KB_ARTICLE.
If you can't understand what the user needs, ask the user in a short manner.

### EXAMPLES:
User: i want to submit a shop floor service
Assistant: WORKFLOW
##
User: i want to error handle a plc
Assistant: KB_ARTICLE
##
User: How can you help?
Assistant: I can assist you with either submitting a Shop Floor Service or finding information in our Knowledge Base Articles. How can I assist you today?

###ANSWER:
Take a deep breath and think about your answer first before you reply."""



class ServiceAgent(BaseAgent):
    def __init__(self, **kwargs) -> None:
        super().__init__(temperature=0)
        
        ### knowledge base
        with open("./config/embeddings.json", 'r') as infile:
            self.embeddings_file = json.load(infile)

    def determine_service(self, query: str, history = []) -> str:
        print("\n\n***\nCALLING SERVICE AGENT\nAgent that returns classifies what the user wants to do\n\n")

        workflows = list(self.workflows_description.keys())
        kb_articles = []
        for e in self.embeddings_file:
            kb_articles.append(e.get("title", ""))
        
        service_system_prompt = SERVICE_SYSTEM_PROMPT.format(workflows=workflows, kb_articles=kb_articles)
        print(f"\nservice agent system prompt::\n{service_system_prompt}\n")

        msgs = [SystemMessage(content=service_system_prompt)]
        msgs += history
        msgs += [HumanMessage(content=query)]
        
        result = self.llm.invoke(msgs).content

        print(f"\nservice agent response: {result}\n\n")


        return result
    
    def validate_service(self, to_validate) -> bool:
        services = ["WORKFLOW", "KB_ARTICLE"]
        return to_validate in services


if __name__ == "__main__":
    USER_FIRST_QUERY = "Hello"
    AI_FIRST_QUERY = "How can I assist you today? Are you looking to run a workflow or query knowledge base articles?"
    
    history = [
        {"role":"user", "content":USER_FIRST_QUERY},
        {"role":"ai", "content":AI_FIRST_QUERY},
        {"role":"user", "content":USER_FIRST_QUERY},
        {"role":"ai", "content":AI_FIRST_QUERY}]
    
    sa = ServiceAgent()
    print("\nAI:\t", AI_FIRST_QUERY)
    
    while True:
        query = input("\nUser:\t")
        print("\nAI:\t", sa.determine_service(query, history))