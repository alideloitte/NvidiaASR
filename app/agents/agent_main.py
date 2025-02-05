from app.agents.abort_agent import AbortAgent
from app.agents.confirmation_agent import ConfirmationAgent
from app.agents.knowledge_base_agent import KnowledgeBaseAgent
from app.agents.service_agent import ServiceAgent
from app.agents.type_selection_agent import TypeSelectionAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.workflow_agent import WorkflowAgent
from app.agents.params_getter_agent import ParamsGetterAgent
from app.agents.state_handler_agent import StateHandlerAgent
import json

from app.services.servicenow_integration import call_servicenow
import time


def main(query, state, history):
    # Check if a service has not been defined in the conversation state
    service = state.get("service")
    if service is None:
        _s = time.time()
        s_agent = ServiceAgent()
        s_agent_response = s_agent.determine_service(query)
        print("ServiceAgent time:", time.time() - _s)

        # If the response is a valid workflow
        if s_agent.validate_service(s_agent_response):
            state["service"] = s_agent_response
            return call_service(s_agent_response, query, state, history)
        else:
            return {"history": history, "output_to_user": s_agent_response, "state": state}
    
    elif service != "":
        user_abort = test_abort(query)
        if user_abort:
            state, history = restart_chat()
            return {"output_to_user": "I apologize if there was any confusion or if I couldn't assist you properly. If you have any other questions or need assistance in the future, feel free to reach out.", "history": history, "state": state}
        return call_service(service, query, state, history)
       

def call_service(service_to_call, query, state, history):
    if service_to_call == "WORKFLOW":
        return workflow_handling(query, state, history)
    elif service_to_call == "KB_ARTICLE":
        return kb_article_handling(query, state, history)
    
def kb_article_handling(query:str, state:dict, history:list) -> dict:
    """Call agents responsible for KB

    Args:
        query (str): User's input or query.
        state (dict):  Stores conversation-related information.

    Returns:
        dict: A dictionary containing updated state, output to the user, and history.
    """
    kb_agent = KnowledgeBaseAgent()
    kb_agent_response = kb_agent.process_query(query, state, history)
    if kb_agent_response == "WORKFLOW":
        state["service"] = kb_agent_response
        _, history = restart_chat(leave_first_message=True, history=history)
        return workflow_handling(query, state, history)
    history = kb_agent.update_history(query, kb_agent_response, history)
    return {"history": history, "output_to_user": kb_agent_response, "state": state}

def workflow_handling(query, state, history):
    """
    The main function handles user queries related to workflows, types, and parameters.

    Args:
        query (str): User's input or query.
        state (dict): Stores conversation-related information.
        history (list): Tracks previous interactions.

    Returns:
        dict: A dictionary containing updated state, output to the user, and history.
    """

    # Check if a workflow has not been defined in the conversation state
    if state.get("workflow_name", "") == "":
        _s = time.time()
        wf_agent = WorkflowAgent()
        workflow_response = wf_agent.get_workflow(query)
        print("WorkflowAgent time:", time.time() - _s)

        # If the response is a valid workflow
        if wf_agent.validate_workflow(workflow_response):
            state["workflow_name"] = workflow_response
            _s = time.time()
            type_agent = TypeSelectionAgent()
            type_response = type_agent.get_type(query, state, history)
            print("TypeSelectionAgent time:", time.time() - _s)

            # If the type exists, call the parameters agent
            if type_agent.validate_type(state["workflow_name"], type_response):
                state["select_device"] = type_response
                state["input_parameters"] = get_input_parameters(type_agent, state["workflow_name"], state["select_device"])
                return call_state_handler_agent(query, state, history, first_call=True)

            # If the type does not exist, prompt the user to provide a type
            else:
                history = type_agent.update_history(query, type_response, history)
                return {"history": history, "output_to_user": type_response, "state": state}

        # If the workflow response is not valid, return the workflow-related error message
        if workflow_response == "KB_ARTICLE":
            _, history = restart_chat(leave_first_message=True, history=history)
            state["service"] = workflow_response
            return kb_article_handling(query, state, history)
        else:
            return {"history": history, "output_to_user": workflow_response, "state": state}


    # If a workflow has been defined in the conversation state
    else:
        # Check if a device type has been defined
        if state.get("select_device", "") == "":
            _s = time.time()
            type_agent = TypeSelectionAgent()
            type_response = type_agent.get_type(query, state, history)
            print("TypeSelectionAgent time:", time.time() - _s)

            # If the type exists, call the parameters agent
            if type_agent.validate_type(state["workflow_name"], type_response):
                state["select_device"] = type_response
                state["input_parameters"] = get_input_parameters(type_agent, state["workflow_name"], state["select_device"])
                return call_state_handler_agent(query, state, history, first_call=True)

            # If the type does not exist, prompt the user to provide a type
            else:
                history = type_agent.update_history(query, type_response, history)
                return {"history": history, "output_to_user": type_response, "state": state}

        # if state HAVE a device type defined
        else:
            # if all the parameters have values
            if check_parameters_complete(state):
                user_confirmation = call_validation_agent(query, state, history)
                if user_confirmation == "TRUE":
                    req_number = call_servicenow(state)
                    state, history = restart_chat()
                    return {"history": history, "output_to_user": f"Thank you for confirming. Workflow has been called!\nRequest Number: {req_number}", "state": state}
                elif user_confirmation == "UNKNOWN":
                    #TODO does the user want to change device type?
                    return call_state_handler_agent(query, state, history) # test if user wnats to change a parameter
                elif user_confirmation == "FALSE": 
                    state, history = restart_chat()
                    return {"history": history, "output_to_user": "Workflow call has been aborted. Thank you.", "state": state}
                else:
                    state, history = restart_chat()
                    return {"history": history, "output_to_user": "Workflow call has been aborted due to an error.", "state": state}

            # if there are parameters with missing values
            else:
                return call_state_handler_agent(query, state, history)
    

def get_input_parameters(type_agent, workflow_name, device_type):
    """Creates a 

    Args:
        type_agent (_type_): _description_
        workflow_name (_type_): _description_
        device_type (_type_): _description_

    Returns:
        _type_: _description_
    """
    input_parameters_keys = type_agent.workflows_description.get(workflow_name, {}).get("select_device", {}).get(device_type, {}).get("input_parameters", {}).keys()
    return {key: "" for key in input_parameters_keys}

def check_parameters_complete(state):
    # TODO: nice to have: an agent replacing this validation 
    print("\n\nVALIDATING PARAMETERS\nChecking if every parameter is filled in.\n")
    param_dict = state.get("input_parameters")
    print(list(param_dict.items()))
    for k, v in param_dict.items():
        if not v:
            if k == "access_contact" and param_dict["device_access"] == "Yes":
                continue
            print("\nPARAMS VALIDATED: FALSE\n")
            return False
    print(f"\nPARAMS VALIDATED: TRUE\n")
    return True

def test_abort(query:str):
    _s = time.time()
    #user_abort = AbortAgent().user_abort(query)
    user_abort = (
        query.lower() == "cancel" or
        query.lower() == "abort"
        )
    print("AbortAgent time:", time.time() - _s)
    return user_abort

def call_state_handler_agent(query, state, history, first_call=False):
    _s = time.time()
    state_handler = StateHandlerAgent()
    updated_parameters = state_handler.update_state(query, state, history)
    print("StateHandlerAgent time:", time.time() - _s)

    state["input_parameters"] = updated_parameters.get("input_parameters")
    if check_parameters_complete(state):
        output_to_user = ask_user_confirmation(f"What are the parameters?", state, history)
        return {"history": history, "output_to_user": output_to_user, "state": state}
    else:
        return call_params_getter_agent(query, state, history, first_call)

def call_params_getter_agent(query, state, history, first_call):
    _s = time.time()
    params_agent = ParamsGetterAgent()
    if first_call:
        history = []
        output_to_user = params_agent.write_message("What information do you need?", state, history)
    else: 
        output_to_user = params_agent.write_message(query, state, history)
    
    print("ParamsGetterAgent time:", time.time() - _s)

    history = params_agent.update_history(query, json.dumps({"output_to_user": output_to_user, "input_parameters": state["input_parameters"]}), history)
    return {"history": history, "output_to_user": output_to_user, "state": state}

def call_validation_agent(query, state, history):
    _s = time.time()
    validation_agent = ValidationAgent()
    response = validation_agent.validate_workflow_call(query, state, history)
    print("ValidationAgent time:", time.time() - _s)

    user_confirmation = response.get("user_confirmation", "UNKNOWN")

    return user_confirmation

def ask_user_confirmation(query, state, history):
    _s = time.time()
    confirmation_agent = ConfirmationAgent()
    output_to_user = confirmation_agent.ask_user_confirmation(query, state, history)
    print("ConfirmationAgent time:", time.time() - _s)
    input_parameters = state.get("input_parameters", "")
    response = json.dumps({"output_to_user": output_to_user, "input_parameters": input_parameters})
    history = confirmation_agent.update_history(query, response, history)
    return output_to_user

def restart_chat(leave_first_message=False, history=[]):
    print("CHAT RESTARTED. state and history emptied.")
    state = {}
    if leave_first_message:
        try:
            history = history[0]
        except IndexError:
            history = []
    else: history = []
    return state, history
