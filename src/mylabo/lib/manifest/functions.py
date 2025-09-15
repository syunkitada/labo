import inspect
from . import functions_ipam


def _load_functions():
    """Load functions marked with @template_function decorator from functions_ipam module."""
    func_map = {}

    # Get all members of functions_ipam module
    for name, obj in inspect.getmembers(functions_ipam):
        # Only include functions that have the @template_function decorator
        if (
            inspect.isfunction(obj)
            and hasattr(obj, "_is_template_function")
            and obj._is_template_function
        ):
            func_map[name] = obj

    return func_map


# Initialize function map automatically
func_map = _load_functions()


def handle(func: str, root_manifest: dict, arg: str):
    if func in func_map:
        return func_map[func](root_manifest, arg)
    else:
        raise Exception(f"Unexpected func: {func}")
