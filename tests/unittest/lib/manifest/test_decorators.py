import pytest

from mylabo.lib.manifest import decorators


class TestTemplateFunctionDecorator:
    """Test the template_function decorator."""

    def test_template_function_decorator_adds_attribute(self):
        """Test that @template_function decorator adds _is_template_function attribute."""

        @decorators.template_function
        def sample_function():
            """A sample function for testing."""
            return "test_result"

        # Check that the decorator added the attribute
        assert hasattr(sample_function, "_is_template_function")
        assert sample_function._is_template_function is True

        # Check that the function still works normally
        assert sample_function() == "test_result"

    def test_template_function_decorator_preserves_function_properties(self):
        """Test that @template_function decorator preserves function properties."""

        @decorators.template_function
        def documented_function(param1, param2="default"):
            """A documented function with parameters.

            Args:
                param1: First parameter
                param2: Second parameter with default value

            Returns:
                str: Concatenated parameters
            """
            return f"{param1}_{param2}"

        # Check that function name is preserved
        assert documented_function.__name__ == "documented_function"

        # Check that docstring is preserved
        assert "A documented function with parameters." in documented_function.__doc__

        # Check that the function works with parameters
        assert documented_function("test", "value") == "test_value"
        assert documented_function("test") == "test_default"

        # Check that the decorator attribute is present
        assert documented_function._is_template_function is True

    def test_template_function_decorator_with_class_method(self):
        """Test that @template_function decorator works with class methods."""

        class TestClass:
            @decorators.template_function
            def instance_method(self, value):
                """An instance method."""
                return f"instance_{value}"

            @classmethod
            @decorators.template_function
            def class_method(cls, value):
                """A class method."""
                return f"class_{value}"

            @staticmethod
            @decorators.template_function
            def static_method(value):
                """A static method."""
                return f"static_{value}"

        obj = TestClass()

        # Test instance method
        assert obj.instance_method("test") == "instance_test"
        assert obj.instance_method._is_template_function is True

        # Test class method
        assert TestClass.class_method("test") == "class_test"
        assert TestClass.class_method._is_template_function is True

        # Test static method
        assert TestClass.static_method("test") == "static_test"
        assert TestClass.static_method._is_template_function is True

    def test_template_function_decorator_with_lambda(self):
        """Test that @template_function decorator works with lambda functions."""

        # Apply decorator to lambda
        lambda_func = decorators.template_function(lambda x: x * 2)

        # Check that the decorator added the attribute
        assert hasattr(lambda_func, "_is_template_function")
        assert lambda_func._is_template_function is True

        # Check that the lambda still works
        assert lambda_func(5) == 10

    def test_template_function_decorator_with_generator(self):
        """Test that @template_function decorator works with generator functions."""

        @decorators.template_function
        def number_generator(n):
            """Generate numbers from 0 to n-1."""
            for i in range(n):
                yield i

        # Check that the decorator added the attribute
        assert hasattr(number_generator, "_is_template_function")
        assert number_generator._is_template_function is True

        # Check that the generator still works
        gen = number_generator(3)
        assert list(gen) == [0, 1, 2]

    def test_template_function_decorator_multiple_decorators(self):
        """Test @template_function decorator when combined with other decorators."""

        def another_decorator(func):
            """Another decorator that adds a different attribute."""
            func._another_attribute = "test_value"
            return func

        @decorators.template_function
        @another_decorator
        def multi_decorated_function():
            """Function with multiple decorators."""
            return "result"

        # Check that both decorators work
        assert multi_decorated_function._is_template_function is True
        assert multi_decorated_function._another_attribute == "test_value"
        assert multi_decorated_function() == "result"

    def test_template_function_decorator_with_exceptions(self):
        """Test @template_function decorator with functions that raise exceptions."""

        @decorators.template_function
        def error_function():
            """Function that raises an error."""
            raise ValueError("Test error")

        # Check that the decorator added the attribute
        assert error_function._is_template_function is True

        # Check that the function still raises the expected exception
        with pytest.raises(ValueError, match="Test error"):
            error_function()

    def test_template_function_decorator_preserves_function_attributes(self):
        """Test that @template_function decorator preserves existing function attributes."""

        def original_function():
            """Original function."""
            return "original"

        # Add custom attributes before decoration
        original_function.custom_attr = "custom_value"
        original_function.custom_number = 42

        # Apply the decorator
        decorated_function = decorators.template_function(original_function)

        # Check that original attributes are preserved
        assert decorated_function.custom_attr == "custom_value"
        assert decorated_function.custom_number == 42

        # Check that the new attribute is added
        assert decorated_function._is_template_function is True

        # Check that the function still works
        assert decorated_function() == "original"

    def test_template_function_decorator_returns_same_function_object(self):
        """Test that @template_function decorator returns the same function object."""

        def original_function():
            """Original function."""
            return "test"

        decorated_function = decorators.template_function(original_function)

        # The decorator should return the same function object, just modified
        assert decorated_function is original_function

        # But with the new attribute
        assert original_function._is_template_function is True

    def test_template_function_decorator_integration_with_inspection(self):
        """Test that decorated functions can be identified by inspection."""

        @decorators.template_function
        def template_func():
            """A template function."""
            return "template"

        def regular_func():
            """A regular function."""
            return "regular"

        functions = [template_func, regular_func]

        # Filter functions with the template_function decorator
        template_functions = [
            func for func in functions if hasattr(func, "_is_template_function") and func._is_template_function
        ]

        assert len(template_functions) == 1
        assert template_functions[0] is template_func
