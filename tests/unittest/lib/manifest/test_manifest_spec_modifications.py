"""
Test module for manifest_spec_modifications.py

This test suite provides comprehensive coverage for the manifest specification
modifications functionality, including:

1. Node overwriting with various property types
2. Node extension (adding new nodes)
3. Step extension handling
4. Error handling for invalid configurations
5. Edge cases and boundary conditions
6. Multiple modifications in sequence

The tests ensure all functionality of the spec modifications system used in
manifest processing.
"""

import pytest
import copy
from mylabo.lib.manifest import manifest_spec_modifications


class TestManifestSpecModifications:
    """Test cases for manifest_spec_modifications module"""

    def test_apply_with_no_modifications(self):
        """Test that apply() works correctly when no spec_modifications exist"""
        spec = {"spec": {"nodes": [{"name": "web", "kind": "container"}]}}

        original_spec = copy.deepcopy(spec)
        manifest_spec_modifications.apply(spec)

        # Should remain unchanged
        assert spec == original_spec

    def test_apply_with_empty_modifications(self):
        """Test apply() with empty spec_modifications list"""
        spec = {"spec": {"nodes": [{"name": "web", "kind": "container"}]}, "spec_modifications": []}

        manifest_spec_modifications.apply(spec)

        # Should remove empty spec_modifications
        assert "spec_modifications" not in spec
        assert len(spec["spec"]["nodes"]) == 1
        assert spec["spec"]["nodes"][0]["name"] == "web"

    def test_overwrite_node_basic_properties(self):
        """Test basic node property overwriting"""
        spec = {
            "spec": {"nodes": [{"name": "web", "kind": "container", "image": "nginx:latest"}]},
            "spec_modifications": [
                {"overwrite_node": {"web": {"image": "nginx:1.20", "ports": [80, 443], "env": {"LOG_LEVEL": "debug"}}}}
            ],
        }

        manifest_spec_modifications.apply(spec)

        node = spec["spec"]["nodes"][0]
        assert node["name"] == "web"
        assert node["kind"] == "container"
        assert node["image"] == "nginx:1.20"  # Overridden
        assert node["ports"] == [80, 443]  # Added
        assert node["env"]["LOG_LEVEL"] == "debug"  # Added

        # spec_modifications should be removed
        assert "spec_modifications" not in spec

    def test_overwrite_node_with_extend_steps(self):
        """Test node overwriting with step extension"""
        spec = {
            "spec": {"nodes": [{"name": "api", "kind": "container", "spec": {"steps": ["install", "configure"]}}]},
            "spec_modifications": [{"overwrite_node": {"api": {"extend_steps": ["test", "deploy"], "timeout": 300}}}],
        }

        manifest_spec_modifications.apply(spec)

        node = spec["spec"]["nodes"][0]
        assert node["name"] == "api"
        assert node["spec"]["steps"] == ["install", "configure", "test", "deploy"]
        assert node["timeout"] == 300

        # extend_steps should be removed after processing
        assert "extend_steps" not in node

    def test_overwrite_multiple_nodes(self):
        """Test overwriting multiple nodes in one modification"""
        spec = {
            "spec": {
                "nodes": [
                    {"name": "web", "kind": "container", "replicas": 1},
                    {"name": "api", "kind": "container", "replicas": 1},
                    {"name": "db", "kind": "vm", "replicas": 1},
                ]
            },
            "spec_modifications": [
                {
                    "overwrite_node": {
                        "web": {"replicas": 3, "ports": [80]},
                        "api": {"replicas": 2, "ports": [8080]},
                        "db": {"memory": "4GB"},
                    }
                }
            ],
        }

        manifest_spec_modifications.apply(spec)

        nodes = {node["name"]: node for node in spec["spec"]["nodes"]}

        assert nodes["web"]["replicas"] == 3
        assert nodes["web"]["ports"] == [80]

        assert nodes["api"]["replicas"] == 2
        assert nodes["api"]["ports"] == [8080]

        assert nodes["db"]["replicas"] == 1  # Unchanged
        assert nodes["db"]["memory"] == "4GB"  # Added

    def test_overwrite_node_nonexistent_node(self):
        """Test that overwriting non-existent nodes doesn't cause errors"""
        spec = {
            "spec": {"nodes": [{"name": "web", "kind": "container"}]},
            "spec_modifications": [{"overwrite_node": {"nonexistent": {"ports": [8080]}, "web": {"ports": [80]}}}],
        }

        manifest_spec_modifications.apply(spec)

        # Should only modify existing nodes
        assert len(spec["spec"]["nodes"]) == 1
        assert spec["spec"]["nodes"][0]["name"] == "web"
        assert spec["spec"]["nodes"][0]["ports"] == [80]

    def test_extend_nodes_basic(self):
        """Test basic node extension functionality"""
        spec = {
            "spec": {"nodes": [{"name": "web", "kind": "container"}]},
            "spec_modifications": [
                {
                    "extend_nodes": [
                        {"name": "api", "kind": "container", "ports": [8080]},
                        {"name": "db", "kind": "vm", "memory": "2GB"},
                    ]
                }
            ],
        }

        manifest_spec_modifications.apply(spec)

        nodes = spec["spec"]["nodes"]
        assert len(nodes) == 3

        # Check original node is preserved
        assert nodes[0]["name"] == "web"
        assert nodes[0]["kind"] == "container"

        # Check new nodes are added
        assert nodes[1]["name"] == "api"
        assert nodes[1]["kind"] == "container"
        assert nodes[1]["ports"] == [8080]

        assert nodes[2]["name"] == "db"
        assert nodes[2]["kind"] == "vm"
        assert nodes[2]["memory"] == "2GB"

    def test_multiple_modifications_in_sequence(self):
        """Test applying multiple spec_modifications in sequence"""
        spec = {
            "spec": {"nodes": [{"name": "web", "kind": "container", "replicas": 1}]},
            "spec_modifications": [
                {"overwrite_node": {"web": {"replicas": 2, "ports": [80]}}},
                {"extend_nodes": [{"name": "api", "kind": "container"}]},
                {"overwrite_node": {"web": {"env": {"DEBUG": "true"}}, "api": {"ports": [8080]}}},
            ],
        }

        manifest_spec_modifications.apply(spec)

        nodes = {node["name"]: node for node in spec["spec"]["nodes"]}

        # Web node should have all modifications applied
        assert nodes["web"]["replicas"] == 2
        assert nodes["web"]["ports"] == [80]
        assert nodes["web"]["env"]["DEBUG"] == "true"

        # API node should be added and modified
        assert nodes["api"]["kind"] == "container"
        assert nodes["api"]["ports"] == [8080]

    def test_deep_nested_property_modification(self):
        """Test modification of deeply nested properties"""
        spec = {
            "spec": {
                "nodes": [
                    {
                        "name": "app",
                        "kind": "container",
                        "spec": {
                            "resources": {"cpu": "100m", "memory": "128Mi"},
                            "config": {"database": {"host": "localhost", "port": 5432}},
                        },
                    }
                ]
            },
            "spec_modifications": [
                {
                    "overwrite_node": {
                        "app": {
                            "spec": {
                                "resources": {"memory": "256Mi", "disk": "1Gi"},  # Override  # Add new
                                "config": {
                                    "database": {"port": 3306, "username": "admin"},  # Override  # Add new
                                    "cache": {"host": "redis", "port": 6379},  # Add new section
                                },
                            }
                        }
                    }
                }
            ],
        }

        manifest_spec_modifications.apply(spec)

        node = spec["spec"]["nodes"][0]
        resources = node["spec"]["resources"]
        database = node["spec"]["config"]["database"]
        cache = node["spec"]["config"]["cache"]

        # Check resource modifications
        assert resources["cpu"] == "100m"  # Preserved
        assert resources["memory"] == "256Mi"  # Overridden
        assert resources["disk"] == "1Gi"  # Added

        # Check database config modifications
        assert database["host"] == "localhost"  # Preserved
        assert database["port"] == 3306  # Overridden
        assert database["username"] == "admin"  # Added

        # Check new cache config
        assert cache["host"] == "redis"
        assert cache["port"] == 6379

    def test_error_overwrite_node_missing_nodes_section(self):
        """Test error when trying to overwrite nodes but nodes section is missing"""
        spec = {"spec": {}, "spec_modifications": [{"overwrite_node": {"web": {"ports": [80]}}}]}  # No nodes section

        with pytest.raises(Exception, match="nodes is not found in spec"):
            manifest_spec_modifications.apply(spec)

    def test_error_extend_nodes_missing_nodes_section(self):
        """Test error when trying to extend nodes but nodes section is missing"""
        spec = {
            "spec": {},  # No nodes section
            "spec_modifications": [{"extend_nodes": [{"name": "api", "kind": "container"}]}],
        }

        with pytest.raises(Exception, match="nodes is not found in spec"):
            manifest_spec_modifications.apply(spec)

    def test_mixed_modification_types(self):
        """Test that only one modification type is processed per spec_modification due to if/elif logic"""
        spec = {
            "spec": {"nodes": [{"name": "web", "kind": "container"}]},
            "spec_modifications": [
                {"overwrite_node": {"web": {"ports": [80]}}, "extend_nodes": [{"name": "api", "kind": "container"}]}
            ],
        }

        manifest_spec_modifications.apply(spec)

        nodes = {node["name"]: node for node in spec["spec"]["nodes"]}

        # Only overwrite_node should be processed (due to if/elif logic)
        assert nodes["web"]["ports"] == [80]
        assert "api" not in nodes  # extend_nodes is not processed

    def test_extend_steps_without_existing_steps(self):
        """Test extend_steps when node doesn't have existing steps"""
        spec = {
            "spec": {"nodes": [{"name": "worker", "kind": "container", "spec": {}}]},  # No existing steps
            "spec_modifications": [{"overwrite_node": {"worker": {"extend_steps": ["initialize", "start"]}}}],
        }

        # This should raise a KeyError since there are no existing steps to extend
        with pytest.raises(KeyError):
            manifest_spec_modifications.apply(spec)

    def test_complex_real_world_scenario(self):
        """Test a complex real-world scenario with multiple modification types"""
        spec = {
            "spec": {
                "domain": "example.com",
                "nodes": [
                    {
                        "name": "web",
                        "kind": "container",
                        "spec": {
                            "image": "nginx:latest",
                            "steps": ["install", "configure"],
                            "resources": {"cpu": "100m"},
                        },
                    },
                    {"name": "app", "kind": "container", "spec": {"image": "app:latest", "steps": ["build", "test"]}},
                ],
            },
            "spec_modifications": [
                # First modification: Update web server for production
                {
                    "overwrite_node": {
                        "web": {
                            "spec": {"image": "nginx:1.20-alpine", "resources": {"cpu": "200m", "memory": "256Mi"}},
                            "replicas": 3,
                            "extend_steps": ["ssl-setup", "monitoring"],  # Must be at top level
                        }
                    }
                },
                # Second modification: Add load balancer and update app
                {
                    "extend_nodes": [
                        {
                            "name": "lb",
                            "kind": "vm",
                            "spec": {"image": "haproxy:latest", "steps": ["install", "configure", "start"]},
                        }
                    ]
                },
                # Third modification: Update app (separate because of if/elif logic)
                {
                    "overwrite_node": {
                        "app": {
                            "spec": {"resources": {"memory": "512Mi"}},
                            "extend_steps": ["deploy"],  # Must be at top level
                        }
                    }
                },
            ],
        }

        manifest_spec_modifications.apply(spec)

        nodes = {node["name"]: node for node in spec["spec"]["nodes"]}

        # Check web node modifications
        web = nodes["web"]
        assert web["spec"]["image"] == "nginx:1.20-alpine"
        assert web["spec"]["steps"] == ["install", "configure", "ssl-setup", "monitoring"]
        assert web["spec"]["resources"]["cpu"] == "200m"
        assert web["spec"]["resources"]["memory"] == "256Mi"
        assert web["replicas"] == 3

        # Check app node modifications
        app = nodes["app"]
        assert app["spec"]["image"] == "app:latest"  # Unchanged
        assert app["spec"]["steps"] == ["build", "test", "deploy"]
        assert app["spec"]["resources"]["memory"] == "512Mi"

        # Check new load balancer node
        lb = nodes["lb"]
        assert lb["kind"] == "vm"
        assert lb["spec"]["image"] == "haproxy:latest"
        assert lb["spec"]["steps"] == ["install", "configure", "start"]

        # Check cleanup
        assert "spec_modifications" not in spec

    def test_separate_modifications_for_different_types(self):
        """Test that different modification types need separate spec_modification entries"""
        spec = {
            "spec": {"nodes": [{"name": "web", "kind": "container"}]},
            "spec_modifications": [
                {"overwrite_node": {"web": {"ports": [80]}}},
                {"extend_nodes": [{"name": "api", "kind": "container"}]},
            ],
        }

        manifest_spec_modifications.apply(spec)

        nodes = {node["name"]: node for node in spec["spec"]["nodes"]}

        # Both modifications should be applied when in separate entries
        assert nodes["web"]["ports"] == [80]
        assert "api" in nodes
        assert nodes["api"]["kind"] == "container"

    def test_modification_with_various_data_types(self):
        """Test modifications with various data types (bool, int, float, None)"""
        spec = {
            "spec": {
                "nodes": [{"name": "service", "kind": "container", "enabled": False, "replicas": 1, "timeout": 30.0}]
            },
            "spec_modifications": [
                {
                    "overwrite_node": {
                        "service": {
                            "enabled": True,  # Boolean
                            "replicas": 5,  # Integer
                            "timeout": 60.5,  # Float
                            "description": None,  # None
                            "tags": ["prod", "web"],  # List
                        }
                    }
                }
            ],
        }

        manifest_spec_modifications.apply(spec)

        node = spec["spec"]["nodes"][0]
        assert node["enabled"] is True
        assert node["replicas"] == 5
        assert node["timeout"] == 60.5
        assert node["description"] is None
        assert node["tags"] == ["prod", "web"]
