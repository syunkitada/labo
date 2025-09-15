def template_function(func):
    """Decorator to mark functions as available for template processing."""
    func._is_template_function = True
    return func
