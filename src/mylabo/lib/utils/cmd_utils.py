def parse_labels(label: str) -> dict:
    if label is None or label == "":
        return {}

    labels = {}
    label_strs = label.split(",")
    for label_str in label_strs:
        key_value = label_str.split("=")
        if len(key_value) != 2:
            raise ValueError(f"Invalid label format: {label_str}. Expected format is key=value.")
        labels[key_value[0]] = key_value[1]
    return labels
