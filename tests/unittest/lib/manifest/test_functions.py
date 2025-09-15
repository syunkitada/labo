import pytest
from unittest.mock import Mock, patch

from mylabo.lib.manifest import functions


class TestLoadFunctions:
    """Test the _load_functions() function."""

    def test_load_functions_with_decorated_functions(self):
        """Test that _load_functions loads functions with @template_function decorator."""
        func_map = functions._load_functions()

        # Should load all functions with @template_function decorator
        assert isinstance(func_map, dict)
        assert len(func_map) > 0

        # Check that expected functions are loaded
        expected_functions = [
            "assign_inet4",
            "assign_ip4",
            "gateway_inet4",
            "gateway_ip",
            "inet_to_ip",
            "ipv4_to_asn",
            "asn_to_ipv4",
            "asn_to_sid",
            "inet4_to_inet6",
        ]

        for func_name in expected_functions:
            assert func_name in func_map, f"Function {func_name} should be in func_map"
            assert callable(func_map[func_name]), f"Function {func_name} should be callable"

    def test_load_functions_excludes_non_decorated_functions(self):
        """Test that _load_functions excludes functions without @template_function decorator."""
        func_map = functions._load_functions()

        # init_network_if_needed should not be loaded (no decorator)
        assert "init_network_if_needed" not in func_map

    def test_load_functions_excludes_non_functions(self):
        """Test that _load_functions excludes non-function objects."""
        func_map = functions._load_functions()

        # Constants and variables should not be loaded
        excluded_items = ["PRIVATE_ASN_START", "PRIVATE_ASN_END", "ASN_NETWORKS", "ASN_IP_NETWORKS"]

        for item in excluded_items:
            assert item not in func_map, f"Non-function {item} should not be in func_map"

    @patch("mylabo.lib.manifest.functions.inspect.getmembers")
    def test_load_functions_with_mock_members(self, mock_getmembers):
        """Test _load_functions with mocked module members."""
        # Create mock functions with and without decorator
        mock_func_with_decorator = Mock()
        mock_func_with_decorator._is_template_function = True

        mock_func_without_decorator = Mock()
        # No _is_template_function attribute

        mock_non_function = "not_a_function"

        # Mock inspect.getmembers to return our test objects
        mock_getmembers.return_value = [
            ("decorated_func", mock_func_with_decorator),
            ("non_decorated_func", mock_func_without_decorator),
            ("non_function", mock_non_function),
        ]

        # Mock inspect.isfunction
        with patch("mylabo.lib.manifest.functions.inspect.isfunction") as mock_isfunction:
            mock_isfunction.side_effect = lambda obj: callable(obj)

            func_map = functions._load_functions()

            # Only the decorated function should be loaded
            assert "decorated_func" in func_map
            assert "non_decorated_func" not in func_map
            assert "non_function" not in func_map
            assert func_map["decorated_func"] == mock_func_with_decorator

    def test_load_functions_handles_missing_decorator_attribute(self):
        """Test that _load_functions handles functions without _is_template_function attribute."""
        with patch("mylabo.lib.manifest.functions.inspect.getmembers") as mock_getmembers:
            mock_func = Mock()
            # Don't set _is_template_function attribute

            mock_getmembers.return_value = [("test_func", mock_func)]

            with patch("mylabo.lib.manifest.functions.inspect.isfunction", return_value=True):
                func_map = functions._load_functions()

                # Function without _is_template_function should not be loaded
                assert "test_func" not in func_map

    def test_load_functions_handles_false_decorator_attribute(self):
        """Test that _load_functions handles functions with _is_template_function = False."""
        with patch("mylabo.lib.manifest.functions.inspect.getmembers") as mock_getmembers:
            mock_func = Mock()
            mock_func._is_template_function = False

            mock_getmembers.return_value = [("test_func", mock_func)]

            with patch("mylabo.lib.manifest.functions.inspect.isfunction", return_value=True):
                func_map = functions._load_functions()

                # Function with _is_template_function = False should not be loaded
                assert "test_func" not in func_map


class TestFuncMapInitialization:
    """Test the func_map global variable initialization."""

    def test_func_map_is_initialized(self):
        """Test that func_map is properly initialized."""
        assert hasattr(functions, "func_map")
        assert isinstance(functions.func_map, dict)
        assert len(functions.func_map) > 0

    def test_func_map_contains_expected_functions(self):
        """Test that func_map contains expected template functions."""
        expected_functions = [
            "assign_inet4",
            "assign_ip4",
            "gateway_inet4",
            "gateway_ip",
            "inet_to_ip",
            "ipv4_to_asn",
            "asn_to_ipv4",
            "asn_to_sid",
            "inet4_to_inet6",
        ]

        for func_name in expected_functions:
            assert func_name in functions.func_map
            assert callable(functions.func_map[func_name])

    def test_func_map_functions_have_decorator_attribute(self):
        """Test that all functions in func_map have the decorator attribute."""
        for func_name, func_obj in functions.func_map.items():
            assert hasattr(func_obj, "_is_template_function")
            assert func_obj._is_template_function is True


class TestHandle:
    """Test the handle() function."""

    def test_handle_calls_existing_function(self):
        """Test that handle calls an existing function successfully."""
        # Create test data
        root_manifest = {"spec": {"ipam": {"test_network": {"kind": "l2", "subnet": "192.168.1.0/24"}}}}

        # Call a function that exists
        result = functions.handle("assign_inet4", root_manifest, "test_network")

        # Should return a valid inet address
        assert isinstance(result, str)
        assert "/" in result  # Should contain subnet mask

    def test_handle_calls_inet_to_ip_function(self):
        """Test handle with inet_to_ip function."""
        root_manifest = {}
        inet_address = "192.168.1.10/24"

        result = functions.handle("inet_to_ip", root_manifest, inet_address)

        assert result == "192.168.1.10"

    def test_handle_calls_gateway_ip_function(self):
        """Test handle with gateway_ip function."""
        root_manifest = {}
        network = "192.168.1.0/24"

        result = functions.handle("gateway_ip", root_manifest, network)

        assert result == "192.168.1.1"

    def test_handle_with_unknown_function_raises_exception(self):
        """Test that handle raises exception for unknown function."""
        root_manifest = {}

        with pytest.raises(Exception) as exc_info:
            functions.handle("unknown_function", root_manifest, "arg")

        assert "Unexpected func: unknown_function" in str(exc_info.value)

    def test_handle_with_empty_function_name_raises_exception(self):
        """Test that handle raises exception for empty function name."""
        root_manifest = {}

        with pytest.raises(Exception) as exc_info:
            functions.handle("", root_manifest, "arg")

        assert "Unexpected func:" in str(exc_info.value)

    def test_handle_with_none_function_name_raises_exception(self):
        """Test that handle raises exception for None function name."""
        root_manifest = {}

        with pytest.raises(Exception) as exc_info:
            functions.handle(None, root_manifest, "arg")

        assert "Unexpected func: None" in str(exc_info.value)

    @patch.object(functions, "func_map")
    def test_handle_with_mocked_function(self, mock_func_map):
        """Test handle with a mocked function in func_map."""
        mock_function = Mock(return_value="mocked_result")
        mock_func_map = {"test_func": mock_function}

        # Replace the actual func_map with our mock
        functions.func_map = mock_func_map

        try:
            root_manifest = {"key": "value"}
            arg = "test_arg"

            result = functions.handle("test_func", root_manifest, arg)

            assert result == "mocked_result"
            mock_function.assert_called_once_with(root_manifest, arg)
        finally:
            # Restore the original func_map
            functions.func_map = functions._load_functions()

    def test_handle_propagates_function_exceptions(self):
        """Test that handle propagates exceptions from called functions."""
        # Use a function that will raise an exception
        root_manifest = {}
        invalid_arg = "invalid_network_name"

        with pytest.raises(Exception):
            # This should raise an exception because the network doesn't exist
            functions.handle("assign_inet4", root_manifest, invalid_arg)

    def test_handle_with_different_argument_types(self):
        """Test handle with different argument types."""
        root_manifest = {}

        # Test with string argument
        result1 = functions.handle("inet_to_ip", root_manifest, "10.0.0.1/32")
        assert result1 == "10.0.0.1"

        # Test with network argument
        result2 = functions.handle("gateway_ip", root_manifest, "10.0.0.0/24")
        assert result2 == "10.0.0.1"


class TestIntegration:
    """Integration tests for the functions module."""

    def test_all_functions_in_func_map_are_callable(self):
        """Test that all functions in func_map are actually callable."""
        for func_name, func_obj in functions.func_map.items():
            assert callable(func_obj), f"Function {func_name} should be callable"

    def test_func_map_consistency_with_load_functions(self):
        """Test that func_map is consistent with _load_functions()."""
        loaded_func_map = functions._load_functions()

        assert len(functions.func_map) == len(loaded_func_map)

        for func_name in functions.func_map:
            assert func_name in loaded_func_map
            assert functions.func_map[func_name] == loaded_func_map[func_name]

    def test_handle_integration_with_real_ipam_functions(self):
        """Test handle integration with real IPAM functions."""
        # Test with assign_inet4
        root_manifest = {"spec": {"ipam": {"mgmt": {"kind": "l2", "subnet": "192.168.100.0/24"}}}}

        # Call assign_inet4 multiple times to test state management
        result1 = functions.handle("assign_inet4", root_manifest, "mgmt")
        result2 = functions.handle("assign_inet4", root_manifest, "mgmt")

        assert result1 != result2  # Should get different IPs
        assert result1.endswith("/24")
        assert result2.endswith("/24")

    def test_handle_integration_with_conversion_functions(self):
        """Test handle integration with conversion functions."""
        root_manifest = {}

        # Test IPv4 to ASN conversion
        asn_result = functions.handle("ipv4_to_asn", root_manifest, "192.168.1.1")
        assert isinstance(asn_result, int)
        assert asn_result >= 4200000000  # Should be in private ASN range

        # Test ASN back to IPv4 conversion
        ipv4_result = functions.handle("asn_to_ipv4", root_manifest, asn_result)
        assert ipv4_result == "192.168.1.1"

    def test_module_level_func_map_reload(self):
        """Test that func_map can be reloaded if needed."""
        original_func_map = functions.func_map.copy()

        # Reload the func_map
        functions.func_map = functions._load_functions()

        # Should have the same functions
        assert len(functions.func_map) == len(original_func_map)
        for func_name in original_func_map:
            assert func_name in functions.func_map

    def test_no_duplicate_functions_in_func_map(self):
        """Test that there are no duplicate functions in func_map."""
        func_names = list(functions.func_map.keys())
        unique_func_names = set(func_names)

        assert len(func_names) == len(unique_func_names), "No duplicate function names should exist"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_handle_with_malformed_root_manifest(self):
        """Test handle behavior with malformed root_manifest."""
        # Test with None root_manifest
        with pytest.raises(Exception):
            functions.handle("assign_inet4", None, "test_network")

        # Test with wrong structure
        malformed_manifest = {"wrong": "structure"}
        with pytest.raises(Exception):
            functions.handle("assign_inet4", malformed_manifest, "test_network")

    def test_handle_preserves_original_exception_details(self):
        """Test that handle preserves original exception details from called functions."""
        root_manifest = {}

        try:
            functions.handle("assign_inet4", root_manifest, "nonexistent_network")
        except Exception as e:
            # Should contain details about the original error
            assert "nonexistent_network" in str(e) or "ipam" in str(e) or "KeyError" in str(type(e).__name__)

    @patch.object(functions, "func_map", {})
    def test_handle_with_empty_func_map(self):
        """Test handle behavior when func_map is empty."""
        try:
            with pytest.raises(Exception) as exc_info:
                functions.handle("any_function", {}, "arg")

            assert "Unexpected func: any_function" in str(exc_info.value)
        finally:
            # Restore the original func_map
            functions.func_map = functions._load_functions()


class TestDocumentation:
    """Test documentation and help functionality."""

    def test_load_functions_has_docstring(self):
        """Test that _load_functions has proper docstring."""
        assert functions._load_functions.__doc__ is not None
        assert "template_function decorator" in functions._load_functions.__doc__

    def test_handle_function_signature(self):
        """Test that handle function has correct signature."""
        import inspect

        signature = inspect.signature(functions.handle)
        params = list(signature.parameters.keys())

        assert params == ["func", "root_manifest", "arg"]

    def test_all_loaded_functions_have_proper_signatures(self):
        """Test that all loaded functions have consistent signatures."""
        import inspect

        for func_name, func_obj in functions.func_map.items():
            signature = inspect.signature(func_obj)
            params = list(signature.parameters.keys())

            # All IPAM functions should start with root_manifest parameter
            assert len(params) >= 2, f"Function {func_name} should have at least 2 parameters"
            assert params[0] == "root_manifest", f"Function {func_name} first parameter should be 'root_manifest'"


class TestPerformance:
    """Test performance-related aspects."""

    def test_func_map_loading_performance(self):
        """Test that func_map loading is reasonably fast."""
        import time

        start_time = time.time()
        func_map = functions._load_functions()
        end_time = time.time()

        # Should load quickly (less than 1 second even on slow systems)
        load_time = end_time - start_time
        assert load_time < 1.0, f"Function loading took too long: {load_time} seconds"
        assert len(func_map) > 0

    def test_handle_call_performance(self):
        """Test that handle function calls are reasonably fast."""
        import time

        root_manifest = {}

        start_time = time.time()
        result = functions.handle("inet_to_ip", root_manifest, "192.168.1.10/24")
        end_time = time.time()

        call_time = end_time - start_time
        assert call_time < 0.1, f"Function call took too long: {call_time} seconds"
        assert result == "192.168.1.10"
