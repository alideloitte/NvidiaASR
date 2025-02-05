import yaml


def get_state_with_labels(state: dict) -> str:
    service = state.get("service")
    if service == "WORKFLOW":
        input_parameters = state.get("input_parameters")

        workflow = state.get("workflow_name", "")
        if workflow == "":
            return "Service: Submit Shop Floor Service"

        with open("./config/parameters_helpers.yml", "r") as params_file:
            params_labels = yaml.safe_load(params_file).get(workflow)
        with open("./config/workflows.yml", "r") as wf_file:
            workflows_description = yaml.safe_load(wf_file)

        select_device = state.get("select_device", "")
        if select_device == "":
            return "Service: Submit Shop Floor Service\n Workflow: " + params_labels[workflow]


        params_desc_list = workflows_description[workflow]["select_device"][select_device][
            "input_parameters"
        ]

        state_with_labels = {"Workflow": params_labels[workflow], "Device Type": params_labels[select_device]}
        for param_name, value in input_parameters.items():
            param_label = params_labels[param_name]
            value_label = get_value_label(param_name, value, params_desc_list)

            state_with_labels[param_label] = value_label

        state_with_labels_str = ""
        for k, v in state_with_labels.items():
            state_with_labels_str += f"{k}: {v}\n"
        state_with_labels_str = state_with_labels_str[:-1]
        return state_with_labels_str
    elif service == "KB_ARTICLE":
        return "Service: Query Knowledge Base Articles"
    else:
        return "<empty>"



def get_value_label(param_name, param_value, params_desc):
    """Gets the label for the option or the original value if no options are defined"""

    param_info = params_desc.get(param_name)

    if param_info is None:
        raise ValueError("Parameter does not exist:", param_name)

    param_options = param_info.get("options")

    # return original value if no options are defined
    if param_options is None:
        return param_value

    else:
        for o_dict in param_options:
            k, v = list(o_dict.items())[0]
            if v == param_value:
                return k
        return ""


if __name__ == "__main__":
    state = {
        "workflow_name": "cleaning",
        "select_device": "factory_pc",
        "input_parameters": {
            "device_location": "Smart Factory Duesseldorf",
            "device_to_be_cleaned": "Macbook",
            "pollution_description": "has dust all over",
            "device_access": "No",
            "access_contact": "guicorreia@deloitte.pt",
        },
    }

    import time
    
    start = time.time()
    print(get_state_with_labels(state))
    end = time.time()

    print("TIME: ", end - start)