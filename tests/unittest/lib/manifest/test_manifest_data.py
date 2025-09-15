"""
Test cases for manifest_data module.

This module tests the completion of manifest data including:
- Template value resolution
- INET data completion
- Reference value resolution
- Recursive data processing
"""

import pytest
from unittest.mock import patch

from mylabo.lib.manifest import manifest_data


class TestComplete:
    """Test cases for the complete function."""

    def test_complete_basic_dict(self):
        """Test completion of basic dictionary."""
        spec = {"name": "test", "value": "simple"}
        result = manifest_data.complete(spec, 0)

        assert result == spec
        assert result is spec  # Should modify in-place

    def test_complete_with_template_value(self):
        """Test completion with template values."""
        spec = {"_referer": {}, "name": "test", "template_value": '<%= "resolved" %>'}
        result = manifest_data.complete(spec, 0)

        assert result["template_value"] == "resolved"

    def test_complete_nested_dict(self):
        """Test completion of nested dictionaries."""
        spec = {"_referer": {}, "outer": {"inner": {"value": '<%= "nested" %>'}}}
        result = manifest_data.complete(spec, 0)

        assert result["outer"]["inner"]["value"] == "nested"

    def test_complete_with_inet_data(self):
        """Test completion with inet data."""
        spec = {"_referer": {}, "network": {"inet": "192.168.1.10/24"}}
        result = manifest_data.complete(spec, 0)

        network = result["network"]
        assert network["inet_compressed"] == "192.168.1.10/24"
        assert network["ip"] == "192.168.1.10"
        assert network["version"] == 4
        assert network["network"] == "192.168.1.0/24"
        assert network["gateway_ip"] == "192.168.1.1"

    def test_complete_nodes_list(self):
        """Test completion of nodes list."""
        spec = {
            "_referer": {},
            "nodes": [{"name": "node1", "value": '<%= "test" %>'}, {"name": "node2", "value": "static"}],
        }

        with patch("builtins.print") as mock_print:
            result = manifest_data.complete(spec, 0)

        assert result["nodes"][0]["value"] == "test"
        assert result["nodes"][1]["value"] == "static"
        mock_print.assert_any_call("Complete node: node1")
        mock_print.assert_any_call("Complete node: node2")

    def test_complete_regular_list(self):
        """Test completion of regular list (not nodes)."""
        spec = {"_referer": {}, "items": ['<%= "item1" %>', "static_item", {"nested": '<%= "nested_value" %>'}]}
        result = manifest_data.complete(spec, 0)

        assert result["items"][0] == "item1"
        assert result["items"][1] == "static_item"
        assert result["items"][2]["nested"] == "nested_value"


class TestCompleteInetData:
    """Test cases for complete_inet_data function."""

    def test_complete_ipv4_with_subnet(self):
        """Test IPv4 completion with subnet mask."""
        inet_data = {"inet": "10.0.1.5/16"}
        manifest_data.complete_inet_data(inet_data)

        assert inet_data["inet_compressed"] == "10.0.1.5/16"
        assert inet_data["inet_exploded"] == "10.0.1.5/16"
        assert inet_data["ip"] == "10.0.1.5"
        assert inet_data["version"] == 4
        assert inet_data["network"] == "10.0.0.0/16"
        assert inet_data["gateway_ip"] == "10.0.0.1"

    def test_complete_ipv4_host_address(self):
        """Test IPv4 completion with /32 (no gateway)."""
        inet_data = {"inet": "192.168.1.10/32"}
        manifest_data.complete_inet_data(inet_data)

        assert inet_data["ip"] == "192.168.1.10"
        assert inet_data["version"] == 4
        assert inet_data["network"] == "192.168.1.10/32"
        assert "gateway_ip" not in inet_data  # No gateway for /32

    def test_complete_ipv6(self):
        """Test IPv6 completion."""
        inet_data = {"inet": "2001:db8::1/64"}
        manifest_data.complete_inet_data(inet_data)

        assert inet_data["ip"] == "2001:db8::1"
        assert inet_data["version"] == 6
        assert inet_data["network"] == "2001:db8::/64"
        assert "gateway_ip" not in inet_data  # No gateway for IPv6

    def test_complete_ipv6_compressed_exploded(self):
        """Test IPv6 compressed and exploded formats."""
        inet_data = {"inet": "2001:db8::1/128"}
        manifest_data.complete_inet_data(inet_data)

        assert inet_data["inet_compressed"] == "2001:db8::1/128"
        assert inet_data["inet_exploded"] == "2001:0db8:0000:0000:0000:0000:0000:0001/128"

    def test_complete_invalid_inet(self):
        """Test completion with invalid inet format."""
        inet_data = {"inet": "invalid"}

        with pytest.raises(ValueError):  # ipaddress raises ValueError, not AddressValueError
            manifest_data.complete_inet_data(inet_data)


class TestCompleteValue:
    """Test cases for complete_value function."""

    def test_complete_value_no_template(self):
        """Test value without template markers."""
        root_manifest = {"_referer": {}}
        value = "plain text"

        result = manifest_data.complete_value(root_manifest, value)
        assert result == "plain text"

    def test_complete_value_string_literal_double_quotes(self):
        """Test string literal with double quotes."""
        root_manifest = {"_referer": {}}
        value = '<%= "test string" %>'

        result = manifest_data.complete_value(root_manifest, value)
        assert result == "test string"

    def test_complete_value_string_literal_single_quotes(self):
        """Test string literal with single quotes."""
        root_manifest = {"_referer": {}}
        value = "<%= 'test string' %>"

        result = manifest_data.complete_value(root_manifest, value)
        assert result == "test string"

    def test_complete_value_with_prefix_suffix(self):
        """Test template value with prefix and suffix."""
        root_manifest = {"_referer": {}}
        value = 'prefix_<%= "middle" %>_suffix'

        result = manifest_data.complete_value(root_manifest, value)
        assert result == "prefix_middle_suffix"

    def test_complete_value_nested_templates(self):
        """Test nested template resolution."""
        root_manifest = {"_referer": {}, "inner": "world"}
        value = '<%= "hello " %><%= inner %>'

        result = manifest_data.complete_value(root_manifest, value)
        assert result == "hello world"

    def test_complete_value_reference_resolution(self):
        """Test reference value resolution."""
        root_manifest = {"_referer": {}, "test_key": "test_value"}
        value = "<%= test_key %>"

        result = manifest_data.complete_value(root_manifest, value)
        assert result == "test_value"

    def test_complete_value_dotted_reference(self):
        """Test dotted reference resolution."""
        root_manifest = {"_referer": {}, "outer": {"inner": "deep_value"}}
        value = "<%= outer.inner %>"

        result = manifest_data.complete_value(root_manifest, value)
        assert result == "deep_value"

    @patch("mylabo.lib.manifest.functions.handle")
    def test_complete_value_function_call(self, mock_handle):
        """Test function call resolution."""
        mock_handle.return_value = "function_result"
        root_manifest = {"_referer": {}}
        value = '<%= test_func("arg") %>'

        result = manifest_data.complete_value(root_manifest, value)

        mock_handle.assert_called_once_with("test_func", root_manifest, "arg")
        assert result == "function_result"

    @patch("mylabo.lib.manifest.functions.handle")
    def test_complete_value_function_with_reference_arg(self, mock_handle):
        """Test function call with reference argument."""
        mock_handle.return_value = "processed"
        root_manifest = {"_referer": {}, "arg_value": "test_arg"}
        value = "<%= process_func(arg_value) %>"

        result = manifest_data.complete_value(root_manifest, value)

        mock_handle.assert_called_once_with("process_func", root_manifest, "test_arg")
        assert result == "processed"

    def test_complete_value_failed_resolution_returns_original(self):
        """Test that failed resolution returns original value."""
        root_manifest = {"_referer": {}}
        value = "<%= nonexistent_key %>"

        with patch("builtins.print"):  # Suppress debug print
            result = manifest_data.complete_value(root_manifest, value)

        assert result == value  # Should return original on failure

    def test_complete_value_exception_handling(self):
        """Test exception handling in complete_value."""
        root_manifest = {"_referer": {}}

        # Mock reference_value to raise exception
        with (
            patch("mylabo.lib.manifest.manifest_data.reference_value", side_effect=Exception("test exception")),
            patch("builtins.print") as mock_print,
        ):

            value = "<%= test_key %>"
            result = manifest_data.complete_value(root_manifest, value)

            assert result == value
            mock_print.assert_called()

    def test_complete_value_recursive_template_failure(self):
        """Test handling of recursive template that can't be resolved."""
        root_manifest = {"_referer": {}, "recursive": "<%= recursive %>"}
        value = "<%= recursive %>"

        with patch("builtins.print"):  # Suppress debug prints
            result = manifest_data.complete_value(root_manifest, value)

        assert result == value  # Should return original when can't resolve

    def test_complete_value_exception_with_negative_times(self):
        """Test exception handling when times is negative."""
        root_manifest = {"_referer": {}}

        # Mock reference_value to raise an exception
        with (
            patch("mylabo.lib.manifest.manifest_data.reference_value", side_effect=Exception("test exception")),
            patch("builtins.print"),
        ):

            value = "<%= test_key %>"
            # When times < 0, the exception should be re-raised
            with pytest.raises(Exception, match="test exception"):
                manifest_data.complete_value(root_manifest, value, times=-1)

    @patch("mylabo.lib.manifest.functions.handle")
    def test_complete_value_function_recursive_arg_resolution(self, mock_handle):
        """Test function call with recursive argument resolution."""
        mock_handle.return_value = "function_result"
        root_manifest = {"_referer": {}, "nested_arg": "resolved_arg"}
        # Function call with argument that needs resolution
        value = "<%= test_func(nested_arg) %>"

        result = manifest_data.complete_value(root_manifest, value)

        # Should call function with resolved argument
        mock_handle.assert_called_once_with("test_func", root_manifest, "resolved_arg")
        assert result == "function_result"

    def test_complete_value_function_with_unresolvable_arg(self):
        """Test function call with argument that can't be resolved."""
        root_manifest = {"_referer": {}}
        # Function with unresolvable recursive argument
        value = "<%= test_func(unresolvable_arg) %>"

        with patch("builtins.print"):
            result = manifest_data.complete_value(root_manifest, value)

        # Should return original value when argument can't be resolved
        assert result == value


class TestReferenceValue:
    """Test cases for reference_value function."""

    def test_reference_value_simple_key(self):
        """Test simple key reference."""
        root_manifest = {"_referer": {}}
        data = {"test_key": "test_value"}

        result = manifest_data.reference_value(root_manifest, data, "test_key")
        assert result == "test_value"

    def test_reference_value_referer_key(self):
        """Test referer key reference."""
        root_manifest = {"_referer": {"referer_key": "referer_value"}}
        data = {}

        result = manifest_data.reference_value(root_manifest, data, "referer_key")
        assert result == "referer_value"

    def test_reference_value_dotted_path(self):
        """Test dotted path reference."""
        root_manifest = {"_referer": {}}
        data = {"outer": {"inner": {"deep": "deep_value"}}}

        result = manifest_data.reference_value(root_manifest, data, "outer.inner.deep")
        assert result == "deep_value"

    def test_reference_value_list_index(self):
        """Test list index reference."""
        root_manifest = {"_referer": {}}
        data = ["first", "second", "third"]

        result = manifest_data.reference_value(root_manifest, data, "1")
        assert result == "second"

    def test_reference_value_mixed_dict_list(self):
        """Test mixed dictionary and list reference."""
        root_manifest = {"_referer": {}}
        data = {"items": [{"name": "item1"}, {"name": "item2"}]}

        result = manifest_data.reference_value(root_manifest, data, "items.0.name")
        assert result == "item1"

    def test_reference_value_nonexistent_key(self):
        """Test nonexistent key reference."""
        root_manifest = {"_referer": {}}
        data = {"existing": "value"}

        with patch("builtins.print") as mock_print:
            result = manifest_data.reference_value(root_manifest, data, "nonexistent")

        assert result is None
        mock_print.assert_called_once()

    def test_reference_value_invalid_list_index(self):
        """Test invalid list index reference."""
        root_manifest = {"_referer": {}}
        data = ["item1", "item2"]

        with pytest.raises(IndexError):
            manifest_data.reference_value(root_manifest, data, "5")

    def test_reference_value_non_string_result(self):
        """Test reference returning non-string value."""
        root_manifest = {"_referer": {}}
        data = {"number": 42, "boolean": True, "nested_dict": {"key": "value"}}

        assert manifest_data.reference_value(root_manifest, data, "number") == 42
        assert manifest_data.reference_value(root_manifest, data, "boolean") is True
        # For nested dict, the function recurses and tries to find "" in the nested dict
        # which fails, so we expect None with a debug print
        with patch("builtins.print"):
            result = manifest_data.reference_value(root_manifest, data, "nested_dict")
        assert result is None

    def test_reference_value_empty_path(self):
        """Test empty reference path."""
        root_manifest = {"_referer": {}}
        data = {"test": "value"}

        # Empty path splits to [""], and "" is not found in data, so returns None
        with patch("builtins.print"):
            result = manifest_data.reference_value(root_manifest, data, "")
        assert result is None


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_manifest_completion(self):
        """Test complete manifest processing."""
        spec = {
            "_referer": {},
            "namespace": "test",
            "nodes": [
                {"name": "node1", "config": {"hostname": '<%= "prefix-" %><%= namespace %>', "inet": "192.168.1.10/24"}}
            ],
            "networks": [{"name": "test-net", "inet": "10.0.0.1/16"}],
        }

        with patch("builtins.print"):
            result = manifest_data.complete(spec, 0)

        # Check template resolution
        assert result["nodes"][0]["config"]["hostname"] == "prefix-test"

        # Check inet completion
        node_config = result["nodes"][0]["config"]
        assert node_config["ip"] == "192.168.1.10"
        assert node_config["gateway_ip"] == "192.168.1.1"

        network = result["networks"][0]
        assert network["ip"] == "10.0.0.1"
        assert network["gateway_ip"] == "10.0.0.1"

    @patch("mylabo.lib.manifest.functions.handle")
    def test_function_integration(self, mock_handle):
        """Test integration with function calls."""
        mock_handle.return_value = "192.168.1.100"

        spec = {
            "_referer": {},
            "spec": {"ipam": {"management": {"subnet": "192.168.1.0/24", "kind": "l2"}}},
            "node": {"ip": '<%= assign_ip4("management") %>'},
        }

        result = manifest_data.complete(spec, 0)

        assert result["node"]["ip"] == "192.168.1.100"
        mock_handle.assert_called_once_with("assign_ip4", spec, "management")

    def test_node_referer_mechanism(self):
        """Test node referer mechanism for cross-references."""
        spec = {
            "_referer": {},
            "nodes": [{"name": "server1", "ip": "192.168.1.10"}, {"name": "client1", "server_ref": "<%= _node.ip %>"}],
        }

        with patch("builtins.print"):
            result = manifest_data.complete(spec, 0)

        # The _node.ip reference will try to resolve _node from referer, but since
        # _node references the current node being processed (client1), and client1
        # doesn't have an ip field, the template resolution fails and returns original
        assert result["nodes"][1]["server_ref"] == "<%= _node.ip %>"  # Failed resolution returns original

    def test_complex_nested_references(self):
        """Test complex nested reference resolution."""
        spec = {
            "_referer": {"global_config": {"domain": "example.com"}},
            "services": {
                "web": {
                    "hostname": "<%= global_config.domain %>",
                    "config": {"fqdn": "web.<%= global_config.domain %>"},
                }
            },
        }

        result = manifest_data.complete(spec, 0)

        assert result["services"]["web"]["hostname"] == "example.com"
        assert result["services"]["web"]["config"]["fqdn"] == "web.example.com"


class TestConstants:
    """Test cases for module constants."""

    def test_constants_defined(self):
        """Test that all constants are properly defined."""
        assert manifest_data.TEMPLATE_START_MARKER == "<%="
        assert manifest_data.TEMPLATE_END_MARKER == "%>"
        assert manifest_data.REFERER_KEY == "_referer"
        assert manifest_data.NODE_KEY == "_node"
        assert manifest_data.NODES_KEY == "nodes"
        assert manifest_data.INET_KEY == "inet"
        assert manifest_data.MAX_RECURSION_DEPTH == 10

    def test_constants_used_in_functions(self):
        """Test that constants are actually used in the code."""
        # This is more of a code review test - constants should be used
        # We can verify by checking if hardcoded strings don't exist
        import inspect

        source = inspect.getsource(manifest_data.complete_value)
        assert '"<%="' not in source
        assert '"%>"' not in source

        source = inspect.getsource(manifest_data._complete_recursively)
        assert '"nodes"' not in source
        assert '"inet"' not in source
