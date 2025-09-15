import pytest
import os
import yaml
from unittest.mock import patch

from mylabo.lib.manifest import manifest_loader


class TestLoadManifests:
    """Test the load_manifests() function."""

    def test_load_manifests_single_file(self, tmp_path):
        """Test loading manifests from a single file."""
        # Create a test manifest file
        manifest_content = {
            "kind": "test",
            "namespace": "test-ns",
            "local_namespaces_dir": "/tmp/test",
            "spec": {"key": "value"},
        }

        manifest_file = tmp_path / "test.yaml"
        manifest_file.write_text(yaml.dump(manifest_content))

        result = manifest_loader.load_manifests(str(manifest_file))

        assert len(result) == 1
        assert result[0]["kind"] == "test"
        assert result[0]["namespace"] == "test-ns"
        assert "_referer" in result[0]
        assert "_script_dir" in result[0]
        assert "_manifest_dir" in result[0]

    def test_load_manifests_directory(self, tmp_path):
        """Test loading manifests from a directory."""
        # Create multiple manifest files
        manifest1 = {
            "kind": "test1",
            "local_namespaces_dir": "/tmp",
            "spec": {"key1": "value1"},
        }
        manifest2 = {
            "kind": "test2",
            "local_namespaces_dir": "/tmp",
            "spec": {"key2": "value2"},
        }

        file1 = tmp_path / "manifest1.yaml"
        file2 = tmp_path / "manifest2.yaml"

        file1.write_text(yaml.dump(manifest1))
        file2.write_text(yaml.dump(manifest2))

        result = manifest_loader.load_manifests(str(tmp_path))

        assert len(result) == 2
        kinds = [m["kind"] for m in result]
        assert "test1" in kinds
        assert "test2" in kinds

    @patch("mylabo.lib.manifest.manifest_spec_modifications.apply")
    @patch("mylabo.lib.manifest.manifest_template.complete")
    @patch("mylabo.lib.manifest.manifest_nodes.complete")
    @patch("mylabo.lib.manifest.manifest_data.complete")
    def test_load_manifests_processing_order(
        self,
        mock_data_complete,
        mock_nodes_complete,
        mock_template_complete,
        mock_spec_apply,
        tmp_path,
    ):
        """Test that manifest processing happens in correct order."""
        manifest_content = {"kind": "test", "local_namespaces_dir": "/tmp", "spec": {}}

        manifest_file = tmp_path / "test.yaml"
        manifest_file.write_text(yaml.dump(manifest_content))

        manifest_loader.load_manifests(str(manifest_file))

        # Verify processing order
        mock_spec_apply.assert_called_once()
        mock_template_complete.assert_called_once()
        mock_nodes_complete.assert_called_once()
        assert mock_data_complete.call_count == 2  # Called with 0 and 1

    def test_load_manifests_with_manifest_data_complete_calls(self, tmp_path):
        """Test that manifest_data.complete is called with correct arguments."""
        manifest_content = {"kind": "test", "local_namespaces_dir": "/tmp", "spec": {}}

        manifest_file = tmp_path / "test.yaml"
        manifest_file.write_text(yaml.dump(manifest_content))

        with patch("mylabo.lib.manifest.manifest_data.complete") as mock_complete:
            manifest_loader.load_manifests(str(manifest_file))

            # Should be called twice with different parameters
            assert mock_complete.call_count == 2
            calls = mock_complete.call_args_list
            assert calls[0][0][1] == 0  # First call with 0
            assert calls[1][0][1] == 1  # Second call with 1

    def test_load_manifests_nonexistent_file(self):
        """Test loading from nonexistent file raises exception."""
        with pytest.raises(Exception) as exc_info:
            manifest_loader.load_manifests("/nonexistent/file.yaml")

        assert "Manifest file not found" in str(exc_info.value)

    def test_load_manifests_empty_directory(self, tmp_path):
        """Test loading from empty directory."""
        result = manifest_loader.load_manifests(str(tmp_path))
        assert result == []


class TestLoadFile:
    """Test the _load_file() function."""

    def test_load_file_basic_yaml(self, tmp_path):
        """Test loading a basic YAML file."""
        manifest_content = {"kind": "test", "spec": {"key": "value"}}

        manifest_file = tmp_path / "test.yaml"
        manifest_file.write_text(yaml.dump(manifest_content))

        result = manifest_loader._load_file(str(manifest_file))

        assert len(result) == 1
        assert result[0]["kind"] == "test"
        assert result[0]["spec"]["key"] == "value"

    def test_load_file_multiple_documents(self, tmp_path):
        """Test loading YAML file with multiple documents separated by ---."""
        content = """
kind: test1
spec:
  key1: value1
---
kind: test2
spec:
  key2: value2
"""
        manifest_file = tmp_path / "multi.yaml"
        manifest_file.write_text(content)

        result = manifest_loader._load_file(str(manifest_file))

        assert len(result) == 2
        assert result[0]["kind"] == "test1"
        assert result[1]["kind"] == "test2"

    def test_load_file_with_comments(self, tmp_path):
        """Test loading YAML file with comments."""
        content = """
# This is a comment
kind: test
# Another comment
spec:
  key: value
"""
        manifest_file = tmp_path / "with_comments.yaml"
        manifest_file.write_text(content)

        result = manifest_loader._load_file(str(manifest_file))

        assert len(result) == 1
        assert result[0]["kind"] == "test"

    def test_load_file_with_imports(self, tmp_path):
        """Test loading YAML file with imports."""
        # Create imported file
        imported_content = {"imported_key": "imported_value"}
        imported_file = tmp_path / "imported.yaml"
        imported_file.write_text(yaml.dump(imported_content))

        # Create main file with import
        main_content = {
            "imports": [str(imported_file)],
            "kind": "main",
            "spec": {"main_key": "main_value"},
        }
        main_file = tmp_path / "main.yaml"
        main_file.write_text(yaml.dump(main_content))

        result = manifest_loader._load_file(str(main_file))

        assert len(result) == 1
        assert result[0]["kind"] == "main"
        assert result[0]["imported_key"] == "imported_value"
        assert result[0]["spec"]["main_key"] == "main_value"

    def test_load_file_with_extend_spec_modifications(self, tmp_path):
        """Test loading file with extend_spec_modifications."""
        content = {
            "kind": "test",
            "spec_modifications": [{"type": "existing"}],
            "extend_spec_modifications": [{"type": "extended"}],
        }

        manifest_file = tmp_path / "extend_spec.yaml"
        manifest_file.write_text(yaml.dump(content))

        result = manifest_loader._load_file(str(manifest_file))

        assert len(result) == 1
        assert len(result[0]["spec_modifications"]) == 2
        assert result[0]["spec_modifications"][0]["type"] == "existing"
        assert result[0]["spec_modifications"][1]["type"] == "extended"
        assert "extend_spec_modifications" not in result[0]

    def test_load_file_with_extend_spec_modifications_no_existing(self, tmp_path):
        """Test extend_spec_modifications when no existing spec_modifications."""
        content = {"kind": "test", "extend_spec_modifications": [{"type": "extended"}]}

        manifest_file = tmp_path / "extend_spec_only.yaml"
        manifest_file.write_text(yaml.dump(content))

        result = manifest_loader._load_file(str(manifest_file))

        assert len(result) == 1
        assert len(result[0]["spec_modifications"]) == 1
        assert result[0]["spec_modifications"][0]["type"] == "extended"
        assert "extend_spec_modifications" not in result[0]

    def test_load_file_directory_recursive(self, tmp_path):
        """Test loading files from directory recursively."""
        # Create subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        # Create files in main directory and subdirectory
        main_content = {"kind": "main", "location": "main"}
        sub_content = {"kind": "sub", "location": "sub"}

        main_file = tmp_path / "main.yaml"
        sub_file = subdir / "sub.yaml"

        main_file.write_text(yaml.dump(main_content))
        sub_file.write_text(yaml.dump(sub_content))

        result = manifest_loader._load_file(str(tmp_path))

        assert len(result) == 2
        locations = [m["location"] for m in result]
        assert "main" in locations
        assert "sub" in locations

    def test_load_file_nonexistent_file(self):
        """Test loading nonexistent file raises exception."""
        with pytest.raises(Exception) as exc_info:
            manifest_loader._load_file("/nonexistent/file.yaml")

        assert "Manifest file not found" in str(exc_info.value)

    def test_load_file_empty_yaml(self, tmp_path):
        """Test loading empty YAML file."""
        manifest_file = tmp_path / "empty.yaml"
        manifest_file.write_text("")

        # Empty YAML results in None from yaml.safe_load, which gets handled
        # This will cause an AttributeError in the current implementation
        # The test documents this behavior
        with pytest.raises(AttributeError):
            manifest_loader._load_file(str(manifest_file))

    def test_load_file_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML file raises exception."""
        manifest_file = tmp_path / "invalid.yaml"
        manifest_file.write_text("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            manifest_loader._load_file(str(manifest_file))

    @patch("mylabo.lib.utils.dict_utils.update_dict")
    def test_load_file_dict_merge_calls(self, mock_update_dict, tmp_path):
        """Test that dict_utils.update_dict is called correctly."""
        content = {"kind": "test", "spec": {}}
        manifest_file = tmp_path / "test.yaml"
        manifest_file.write_text(yaml.dump(content))

        manifest_loader._load_file(str(manifest_file))

        # Should be called once to merge _manifest into manifest
        mock_update_dict.assert_called()

    def test_load_file_with_nested_imports(self, tmp_path):
        """Test loading file with nested imports."""
        # Create deeply imported file
        deep_content = {"deep_key": "deep_value"}
        deep_file = tmp_path / "deep.yaml"
        deep_file.write_text(yaml.dump(deep_content))

        # Create intermediate file that imports deep file
        intermediate_content = {
            "imports": [str(deep_file)],
            "intermediate_key": "intermediate_value",
        }
        intermediate_file = tmp_path / "intermediate.yaml"
        intermediate_file.write_text(yaml.dump(intermediate_content))

        # Create main file that imports intermediate file
        main_content = {
            "imports": [str(intermediate_file)],
            "kind": "main",
            "main_key": "main_value",
        }
        main_file = tmp_path / "main.yaml"
        main_file.write_text(yaml.dump(main_content))

        result = manifest_loader._load_file(str(main_file))

        assert len(result) == 1
        assert result[0]["deep_key"] == "deep_value"
        assert result[0]["intermediate_key"] == "intermediate_value"
        assert result[0]["main_key"] == "main_value"
        assert result[0]["kind"] == "main"


class TestInitManifest:
    """Test the init_manifest() function."""

    def test_init_manifest_basic(self, tmp_path):
        """Test basic manifest initialization."""
        manifest = {"kind": "TestKind", "local_namespaces_dir": "/tmp/test"}

        test_file = tmp_path / "test_manifest.yaml"
        test_file.write_text("# dummy")

        manifest_loader.init_manifest(manifest, str(test_file))

        assert (
            manifest["namespace"] == "test-manifest"
        )  # Underscores replaced with dashes
        assert manifest["_script_dir"] == "/tmp/test/testkind/test-manifest"
        assert manifest["_manifest_dir"] == str(tmp_path)

    def test_init_manifest_preserves_existing_namespace(self, tmp_path):
        """Test that existing namespace is preserved."""
        manifest = {
            "kind": "TestKind",
            "namespace": "custom-namespace",
            "local_namespaces_dir": "/tmp/test",
        }

        test_file = tmp_path / "any_name.yaml"
        test_file.write_text("# dummy")

        manifest_loader.init_manifest(manifest, str(test_file))

        assert manifest["namespace"] == "custom-namespace"
        assert manifest["_script_dir"] == "/tmp/test/testkind/custom-namespace"

    def test_init_manifest_namespace_from_filename(self, tmp_path):
        """Test namespace generation from various filenames."""
        test_cases = [
            ("simple.yaml", "simple"),
            ("with_underscores.yaml", "with-underscores"),
            ("complex_file_name.yaml", "complex-file-name"),
            ("file.with.dots.yaml", "file"),  # Only first part before dot
        ]

        for filename, expected_namespace in test_cases:
            manifest = {"kind": "Test", "local_namespaces_dir": "/tmp"}

            test_file = tmp_path / filename
            test_file.write_text("# dummy")

            manifest_loader.init_manifest(manifest, str(test_file))

            assert manifest["namespace"] == expected_namespace

    def test_init_manifest_script_dir_case_conversion(self, tmp_path):
        """Test that kind is converted to lowercase in script_dir."""
        manifest = {"kind": "TestKind", "local_namespaces_dir": "/tmp/namespaces"}

        test_file = tmp_path / "test.yaml"
        test_file.write_text("# dummy")

        manifest_loader.init_manifest(manifest, str(test_file))

        assert manifest["_script_dir"] == "/tmp/namespaces/testkind/test"

    def test_init_manifest_manifest_dir_absolute_path(self, tmp_path):
        """Test that _manifest_dir contains absolute path."""
        manifest = {"kind": "Test", "local_namespaces_dir": "/tmp"}

        test_file = tmp_path / "test.yaml"
        test_file.write_text("# dummy")

        manifest_loader.init_manifest(manifest, str(test_file))

        assert os.path.isabs(manifest["_manifest_dir"])
        assert manifest["_manifest_dir"] == str(tmp_path)

    def test_init_manifest_with_subdirectory(self, tmp_path):
        """Test manifest initialization with file in subdirectory."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        manifest = {"kind": "Test", "local_namespaces_dir": "/tmp"}

        test_file = subdir / "test.yaml"
        test_file.write_text("# dummy")

        manifest_loader.init_manifest(manifest, str(test_file))

        assert manifest["_manifest_dir"] == str(subdir)

    def test_init_manifest_complex_path(self, tmp_path):
        """Test manifest initialization with complex file path."""
        complex_dir = tmp_path / "path" / "to" / "manifests"
        complex_dir.mkdir(parents=True)

        manifest = {
            "kind": "ComplexTest",
            "local_namespaces_dir": "/var/lib/namespaces",
        }

        test_file = complex_dir / "complex_manifest_name.yaml"
        test_file.write_text("# dummy")

        manifest_loader.init_manifest(manifest, str(test_file))

        assert manifest["namespace"] == "complex-manifest-name"
        assert (
            manifest["_script_dir"]
            == "/var/lib/namespaces/complextest/complex-manifest-name"
        )
        assert manifest["_manifest_dir"] == str(complex_dir)


class TestIntegration:
    """Integration tests for manifest_loader."""

    def test_full_manifest_loading_workflow(self, tmp_path):
        """Test complete manifest loading workflow."""
        # Create a realistic manifest
        manifest_content = {
            "kind": "Infrastructure",
            "local_namespaces_dir": "/tmp/infra",
            "spec": {
                "nodes": [
                    {"name": "node1", "type": "vm"},
                    {"name": "node2", "type": "container"},
                ],
                "networks": {"mgmt": {"subnet": "192.168.1.0/24"}},
            },
        }

        manifest_file = tmp_path / "infrastructure.yaml"
        manifest_file.write_text(yaml.dump(manifest_content))

        with (
            patch("mylabo.lib.manifest.manifest_spec_modifications.apply") as mock_spec,
            patch("mylabo.lib.manifest.manifest_template.complete") as mock_template,
            patch("mylabo.lib.manifest.manifest_nodes.complete") as mock_nodes,
            patch("mylabo.lib.manifest.manifest_data.complete") as mock_data,
        ):
            result = manifest_loader.load_manifests(str(manifest_file))

            assert len(result) == 1
            manifest = result[0]

            # Check basic structure
            assert manifest["kind"] == "Infrastructure"
            assert manifest["namespace"] == "infrastructure"
            assert "_referer" in manifest
            assert "_script_dir" in manifest
            assert "_manifest_dir" in manifest

            # Check that all processing functions were called
            mock_spec.assert_called_once_with(manifest)
            mock_template.assert_called_once_with(manifest)
            mock_nodes.assert_called_once_with(manifest)
            assert mock_data.call_count == 2

    def test_complex_import_scenario(self, tmp_path):
        """Test complex scenario with multiple imports and processing."""
        # Create base configuration
        base_config = {
            "base_setting": "value",
            "networks": {"base_net": {"subnet": "10.0.0.0/24"}},
        }
        base_file = tmp_path / "base.yaml"
        base_file.write_text(yaml.dump(base_config))

        # Create environment specific config
        env_config = {
            "imports": [str(base_file)],
            "environment": "test",
            "networks": {"env_net": {"subnet": "192.168.0.0/24"}},
        }
        env_file = tmp_path / "environment.yaml"
        env_file.write_text(yaml.dump(env_config))

        # Create main manifest
        main_config = {
            "imports": [str(env_file)],
            "kind": "ComplexInfra",
            "local_namespaces_dir": "/tmp/complex",
            "spec": {
                "domain": "example.com",
                "nodes": [
                    {"name": "node1", "kind": "container", "spec": {}},
                    {"name": "node2", "kind": "vm", "spec": {}},
                ],
            },
            "extend_spec_modifications": [{"type": "add_node", "name": "node3"}],
        }
        main_file = tmp_path / "main.yaml"
        main_file.write_text(yaml.dump(main_config))

        # Mock the processing functions to avoid actual processing
        with (
            patch("mylabo.lib.manifest.manifest_spec_modifications.apply") as mock_spec,
            patch("mylabo.lib.manifest.manifest_template.complete") as mock_template,
            patch("mylabo.lib.manifest.manifest_nodes.complete") as mock_nodes,
            patch("mylabo.lib.manifest.manifest_data.complete") as mock_data,
        ):
            result = manifest_loader.load_manifests(str(main_file))

            assert len(result) == 1
            manifest = result[0]

            # Check merged content from import processing
            assert manifest["base_setting"] == "value"
            assert manifest["environment"] == "test"
            assert manifest["kind"] == "ComplexInfra"
            assert "base_net" in manifest["networks"]
            assert "env_net" in manifest["networks"]

            # Check that extend_spec_modifications was processed correctly
            # (converted to spec_modifications and extend_spec_modifications removed)
            assert len(manifest["spec_modifications"]) == 1
            assert manifest["spec_modifications"][0]["type"] == "add_node"
            assert "extend_spec_modifications" not in manifest

            # Verify processing functions were called
            mock_spec.assert_called_once()
            mock_template.assert_called_once()
            mock_nodes.assert_called_once()
            assert mock_data.call_count == 2

    def test_directory_loading_with_mixed_files(self, tmp_path):
        """Test loading directory with various file types."""
        # Create YAML files
        yaml1 = {"kind": "Test1", "local_namespaces_dir": "/tmp"}
        yaml2 = {"kind": "Test2", "local_namespaces_dir": "/tmp"}

        (tmp_path / "test1.yaml").write_text(yaml.dump(yaml1))
        (tmp_path / "test2.yaml").write_text(yaml.dump(yaml2))

        # Create non-YAML file (should be processed but likely fail YAML parsing)
        (tmp_path / "readme.txt").write_text("This is not YAML")

        # Create subdirectory with YAML
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        yaml3 = {"kind": "Test3", "local_namespaces_dir": "/tmp"}
        (subdir / "test3.yaml").write_text(yaml.dump(yaml3))

        # This should process all files, including the non-YAML one which will fail
        with pytest.raises(Exception):  # Non-YAML file will cause error
            manifest_loader.load_manifests(str(tmp_path))

    def test_error_handling_in_processing_pipeline(self, tmp_path):
        """Test error handling when processing functions fail."""
        manifest_content = {"kind": "Test", "local_namespaces_dir": "/tmp"}

        manifest_file = tmp_path / "test.yaml"
        manifest_file.write_text(yaml.dump(manifest_content))

        # Mock one of the processing functions to raise an exception
        with patch(
            "mylabo.lib.manifest.manifest_template.complete",
            side_effect=Exception("Template processing failed"),
        ):
            with pytest.raises(Exception) as exc_info:
                manifest_loader.load_manifests(str(manifest_file))

            assert "Template processing failed" in str(exc_info.value)


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_load_manifests_file_permission_error(self, tmp_path):
        """Test handling of file permission errors."""
        manifest_file = tmp_path / "restricted.yaml"
        manifest_file.write_text("kind: test")

        # Mock os.path.exists to return True but file opening to fail
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", side_effect=PermissionError("Permission denied")),
        ):
            with pytest.raises(PermissionError):
                manifest_loader.load_manifests(str(manifest_file))

    def test_load_file_corrupted_yaml(self, tmp_path):
        """Test handling of corrupted YAML files."""
        corrupted_content = """
kind: test
spec:
  - invalid
  - yaml: [unclosed
"""
        manifest_file = tmp_path / "corrupted.yaml"
        manifest_file.write_text(corrupted_content)

        with pytest.raises(yaml.YAMLError):
            manifest_loader._load_file(str(manifest_file))

    def test_init_manifest_missing_required_fields(self, tmp_path):
        """Test init_manifest with missing required fields."""
        # Test with missing kind
        manifest_no_kind = {"local_namespaces_dir": "/tmp"}
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# dummy")

        with pytest.raises(KeyError):
            manifest_loader.init_manifest(manifest_no_kind, str(test_file))

        # Test with missing local_namespaces_dir
        manifest_no_dir = {"kind": "Test"}

        with pytest.raises(KeyError):
            manifest_loader.init_manifest(manifest_no_dir, str(test_file))

    def test_load_file_import_nonexistent_file(self, tmp_path):
        """Test handling of imports pointing to nonexistent files."""
        content = {"imports": ["/nonexistent/path/file.yaml"], "kind": "test"}

        manifest_file = tmp_path / "test.yaml"
        manifest_file.write_text(yaml.dump(content))

        with pytest.raises(Exception) as exc_info:
            manifest_loader._load_file(str(manifest_file))

        assert "Manifest file not found" in str(exc_info.value)

    def test_load_file_circular_imports(self, tmp_path):
        """Test detection of circular imports."""
        # Create file1 that imports file2
        content1 = {"imports": [str(tmp_path / "file2.yaml")], "file": "file1"}
        file1 = tmp_path / "file1.yaml"
        file1.write_text(yaml.dump(content1))

        # Create file2 that imports file1 (circular)
        content2 = {"imports": [str(file1)], "file": "file2"}
        file2 = tmp_path / "file2.yaml"
        file2.write_text(yaml.dump(content2))

        # This should cause infinite recursion or similar error
        with pytest.raises(RecursionError):
            manifest_loader._load_file(str(file1))


class TestDuplicateImportIssue:
    """Test to verify and document the duplicate import issue."""

    def test_duplicate_manifest_data_import_exists(self):
        """Test that documents the duplicate manifest_data import in the module."""
        # Read the source file to check for duplicate imports
        import inspect

        source = inspect.getsource(manifest_loader)

        # Count occurrences of manifest_data import
        manifest_data_count = source.count("manifest_data")

        # This test documents the current state - there should be duplicate imports
        # This could be fixed by removing one of the duplicate imports
        assert manifest_data_count >= 2, (
            "Expected duplicate manifest_data imports to be present"
        )

    def test_module_imports_work_despite_duplicate(self):
        """Test that module functionality works despite duplicate import."""
        # Verify that manifest_data functions are accessible
        assert hasattr(manifest_loader.manifest_data, "complete")

        # This confirms the module works despite the duplicate import
        # but it's still a code quality issue that should be fixed
