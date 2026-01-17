"""Tests for Helm chart validation.

These tests validate that the Helm chart is well-structured and follows
best practices.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

# Path to Helm chart
HELM_DIR = Path(__file__).parent.parent.parent / "infra" / "helm" / "optimal-build"


def helm_available() -> bool:
    """Check if Helm CLI is available."""
    try:
        subprocess.run(
            ["helm", "version", "--short"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class TestHelmChartStructure:
    """Tests for Helm chart structure."""

    def test_chart_yaml_exists(self) -> None:
        """Test Chart.yaml exists."""
        chart_file = HELM_DIR / "Chart.yaml"
        assert chart_file.exists(), "Chart.yaml not found"

    def test_values_yaml_exists(self) -> None:
        """Test values.yaml exists."""
        values_file = HELM_DIR / "values.yaml"
        assert values_file.exists(), "values.yaml not found"

    def test_templates_directory_exists(self) -> None:
        """Test templates directory exists."""
        templates_dir = HELM_DIR / "templates"
        assert templates_dir.exists(), "templates/ directory not found"

    def test_helpers_template_exists(self) -> None:
        """Test _helpers.tpl exists."""
        helpers_file = HELM_DIR / "templates" / "_helpers.tpl"
        assert helpers_file.exists(), "_helpers.tpl not found"


class TestChartYaml:
    """Tests for Chart.yaml content."""

    @pytest.fixture
    def chart(self) -> dict:
        chart_file = HELM_DIR / "Chart.yaml"
        with open(chart_file) as f:
            return yaml.safe_load(f)

    def test_chart_has_api_version(self, chart: dict) -> None:
        """Test Chart.yaml has apiVersion."""
        assert "apiVersion" in chart
        assert chart["apiVersion"] in ("v1", "v2")

    def test_chart_has_name(self, chart: dict) -> None:
        """Test Chart.yaml has name."""
        assert "name" in chart
        assert chart["name"] == "optimal-build"

    def test_chart_has_version(self, chart: dict) -> None:
        """Test Chart.yaml has version."""
        assert "version" in chart
        # Version should follow semver
        version = chart["version"]
        parts = version.split(".")
        assert len(parts) >= 2, "Version should be semver format"

    def test_chart_has_app_version(self, chart: dict) -> None:
        """Test Chart.yaml has appVersion."""
        assert "appVersion" in chart

    def test_chart_has_description(self, chart: dict) -> None:
        """Test Chart.yaml has description."""
        assert "description" in chart
        assert len(chart["description"]) > 10


class TestValuesYaml:
    """Tests for values.yaml content."""

    @pytest.fixture
    def values(self) -> dict:
        values_file = HELM_DIR / "values.yaml"
        with open(values_file) as f:
            return yaml.safe_load(f)

    def test_values_has_global_section(self, values: dict) -> None:
        """Test values has global configuration."""
        assert "global" in values

    def test_values_has_backend_section(self, values: dict) -> None:
        """Test values has backend configuration."""
        assert "backend" in values
        backend = values["backend"]
        assert "replicaCount" in backend
        assert "image" in backend
        assert "resources" in backend

    def test_values_has_frontend_section(self, values: dict) -> None:
        """Test values has frontend configuration."""
        assert "frontend" in values
        frontend = values["frontend"]
        assert "replicaCount" in frontend
        assert "image" in frontend

    def test_values_has_ingress_section(self, values: dict) -> None:
        """Test values has ingress configuration."""
        assert "ingress" in values
        ingress = values["ingress"]
        assert "enabled" in ingress

    def test_backend_has_autoscaling(self, values: dict) -> None:
        """Test backend has autoscaling configuration."""
        backend = values.get("backend", {})
        assert "autoscaling" in backend
        autoscaling = backend["autoscaling"]
        assert "enabled" in autoscaling
        assert "minReplicas" in autoscaling
        assert "maxReplicas" in autoscaling

    def test_backend_resources_have_limits(self, values: dict) -> None:
        """Test backend resources have limits."""
        resources = values.get("backend", {}).get("resources", {})
        assert "limits" in resources
        assert "memory" in resources["limits"]
        assert "cpu" in resources["limits"]

    def test_backend_resources_have_requests(self, values: dict) -> None:
        """Test backend resources have requests."""
        resources = values.get("backend", {}).get("resources", {})
        assert "requests" in resources
        assert "memory" in resources["requests"]
        assert "cpu" in resources["requests"]

    def test_security_settings_present(self, values: dict) -> None:
        """Test security settings are configured."""
        assert "security" in values
        security = values["security"]
        assert "podSecurityContext" in security
        assert "containerSecurityContext" in security

    def test_security_context_is_restrictive(self, values: dict) -> None:
        """Test security context follows best practices."""
        pod_security = values.get("security", {}).get("podSecurityContext", {})
        container_security = values.get("security", {}).get(
            "containerSecurityContext", {}
        )

        # Pod should run as non-root
        assert pod_security.get("runAsNonRoot") is True

        # Container should not allow privilege escalation
        assert container_security.get("allowPrivilegeEscalation") is False


class TestHelmTemplateHelpers:
    """Tests for Helm template helpers."""

    @pytest.fixture
    def helpers_content(self) -> str:
        helpers_file = HELM_DIR / "templates" / "_helpers.tpl"
        with open(helpers_file) as f:
            return f.read()

    def test_helpers_define_name(self, helpers_content: str) -> None:
        """Test helpers define name template."""
        assert "optimal-build.name" in helpers_content

    def test_helpers_define_fullname(self, helpers_content: str) -> None:
        """Test helpers define fullname template."""
        assert "optimal-build.fullname" in helpers_content

    def test_helpers_define_labels(self, helpers_content: str) -> None:
        """Test helpers define labels template."""
        assert "optimal-build.labels" in helpers_content

    def test_helpers_define_selector_labels(self, helpers_content: str) -> None:
        """Test helpers define selectorLabels template."""
        assert "optimal-build.selectorLabels" in helpers_content


@pytest.mark.skipif(not helm_available(), reason="Helm CLI not available")
class TestHelmLint:
    """Tests using Helm CLI for linting."""

    def test_helm_lint_passes(self) -> None:
        """Test helm lint passes without errors."""
        result = subprocess.run(
            ["helm", "lint", str(HELM_DIR)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Helm lint failed: {result.stderr}"

    def test_helm_template_renders(self) -> None:
        """Test helm template renders without errors."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(HELM_DIR)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

    def test_helm_template_renders_valid_yaml(self) -> None:
        """Test helm template output is valid YAML."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(HELM_DIR)],
            capture_output=True,
            text=True,
        )

        # Should be able to parse the output as YAML
        docs = list(yaml.safe_load_all(result.stdout))
        assert len(docs) > 0, "No documents rendered"

        # Each document should have required fields
        for doc in docs:
            if doc is not None:
                assert "apiVersion" in doc
                assert "kind" in doc

    def test_helm_dry_run(self) -> None:
        """Test helm install dry-run succeeds."""
        result = subprocess.run(
            [
                "helm",
                "install",
                "test-release",
                str(HELM_DIR),
                "--dry-run",
                "--debug",
            ],
            capture_output=True,
            text=True,
        )
        # Dry run may fail due to missing cluster, but should not have template errors
        if result.returncode != 0:
            # Check it's not a template error
            assert "error" not in result.stderr.lower() or "cluster" in result.stderr.lower()
