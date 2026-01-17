"""Tests for Kubernetes manifest validation.

These tests validate that Kubernetes manifests are syntactically correct
and follow best practices.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

# Path to infrastructure directory
INFRA_DIR = Path(__file__).parent.parent.parent / "infra"
K8S_DIR = INFRA_DIR / "kubernetes"


def load_yaml_file(filepath: Path) -> list[dict]:
    """Load a YAML file, handling multi-document files."""
    with open(filepath) as f:
        docs = list(yaml.safe_load_all(f))
    return [doc for doc in docs if doc is not None]


def get_k8s_manifests() -> list[tuple[str, dict]]:
    """Get all Kubernetes manifest files."""
    manifests = []
    if K8S_DIR.exists():
        for filepath in K8S_DIR.glob("*.yaml"):
            docs = load_yaml_file(filepath)
            for doc in docs:
                manifests.append((filepath.name, doc))
    return manifests


class TestKubernetesManifestStructure:
    """Tests for basic Kubernetes manifest structure."""

    @pytest.fixture
    def manifests(self) -> list[tuple[str, dict]]:
        return get_k8s_manifests()

    def test_manifests_exist(self, manifests: list) -> None:
        """Test that Kubernetes manifests exist."""
        assert len(manifests) > 0, "No Kubernetes manifests found"

    @pytest.mark.parametrize(
        "filename,manifest",
        get_k8s_manifests(),
        ids=lambda x: x if isinstance(x, str) else "",
    )
    def test_manifest_has_api_version(
        self, filename: str, manifest: dict
    ) -> None:
        """Test all manifests have apiVersion."""
        assert "apiVersion" in manifest, f"{filename} missing apiVersion"

    @pytest.mark.parametrize(
        "filename,manifest",
        get_k8s_manifests(),
        ids=lambda x: x if isinstance(x, str) else "",
    )
    def test_manifest_has_kind(self, filename: str, manifest: dict) -> None:
        """Test all manifests have kind."""
        assert "kind" in manifest, f"{filename} missing kind"

    @pytest.mark.parametrize(
        "filename,manifest",
        get_k8s_manifests(),
        ids=lambda x: x if isinstance(x, str) else "",
    )
    def test_manifest_has_metadata(self, filename: str, manifest: dict) -> None:
        """Test all manifests have metadata."""
        assert "metadata" in manifest, f"{filename} missing metadata"

    @pytest.mark.parametrize(
        "filename,manifest",
        get_k8s_manifests(),
        ids=lambda x: x if isinstance(x, str) else "",
    )
    def test_manifest_has_name(self, filename: str, manifest: dict) -> None:
        """Test all manifests have a name in metadata."""
        if manifest.get("kind") != "List":
            assert (
                "name" in manifest.get("metadata", {})
            ), f"{filename} missing metadata.name"


class TestDeploymentManifests:
    """Tests for Deployment manifests."""

    @pytest.fixture
    def deployments(self) -> list[tuple[str, dict]]:
        return [
            (f, m)
            for f, m in get_k8s_manifests()
            if m.get("kind") == "Deployment"
        ]

    def test_deployments_have_replicas(
        self, deployments: list[tuple[str, dict]]
    ) -> None:
        """Test deployments specify replica count."""
        for filename, manifest in deployments:
            spec = manifest.get("spec", {})
            assert "replicas" in spec, f"{filename} missing spec.replicas"

    def test_deployments_have_selector(
        self, deployments: list[tuple[str, dict]]
    ) -> None:
        """Test deployments have selector."""
        for filename, manifest in deployments:
            spec = manifest.get("spec", {})
            assert "selector" in spec, f"{filename} missing spec.selector"

    def test_deployments_have_containers(
        self, deployments: list[tuple[str, dict]]
    ) -> None:
        """Test deployments have containers defined."""
        for filename, manifest in deployments:
            containers = (
                manifest.get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
            )
            assert len(containers) > 0, f"{filename} has no containers"

    def test_containers_have_resource_limits(
        self, deployments: list[tuple[str, dict]]
    ) -> None:
        """Test containers have resource limits for production readiness."""
        for filename, manifest in deployments:
            containers = (
                manifest.get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
            )
            for container in containers:
                resources = container.get("resources", {})
                assert "limits" in resources, (
                    f"{filename} container {container.get('name')} "
                    "missing resource limits"
                )

    def test_containers_have_resource_requests(
        self, deployments: list[tuple[str, dict]]
    ) -> None:
        """Test containers have resource requests."""
        for filename, manifest in deployments:
            containers = (
                manifest.get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
            )
            for container in containers:
                resources = container.get("resources", {})
                assert "requests" in resources, (
                    f"{filename} container {container.get('name')} "
                    "missing resource requests"
                )

    def test_containers_have_probes(
        self, deployments: list[tuple[str, dict]]
    ) -> None:
        """Test containers have health probes."""
        for filename, manifest in deployments:
            containers = (
                manifest.get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
            )
            for container in containers:
                has_liveness = "livenessProbe" in container
                has_readiness = "readinessProbe" in container
                assert has_liveness or has_readiness, (
                    f"{filename} container {container.get('name')} "
                    "missing health probes"
                )

    def test_containers_have_security_context(
        self, deployments: list[tuple[str, dict]]
    ) -> None:
        """Test containers have security context."""
        for filename, manifest in deployments:
            containers = (
                manifest.get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
            )
            for container in containers:
                assert "securityContext" in container, (
                    f"{filename} container {container.get('name')} "
                    "missing securityContext"
                )


class TestServiceManifests:
    """Tests for Service manifests."""

    @pytest.fixture
    def services(self) -> list[tuple[str, dict]]:
        return [
            (f, m) for f, m in get_k8s_manifests() if m.get("kind") == "Service"
        ]

    def test_services_have_selector(
        self, services: list[tuple[str, dict]]
    ) -> None:
        """Test services have selector."""
        for filename, manifest in services:
            spec = manifest.get("spec", {})
            assert "selector" in spec, f"{filename} missing spec.selector"

    def test_services_have_ports(
        self, services: list[tuple[str, dict]]
    ) -> None:
        """Test services have ports defined."""
        for filename, manifest in services:
            spec = manifest.get("spec", {})
            assert "ports" in spec, f"{filename} missing spec.ports"
            assert len(spec["ports"]) > 0, f"{filename} has no ports"


class TestIngressManifests:
    """Tests for Ingress manifests."""

    @pytest.fixture
    def ingresses(self) -> list[tuple[str, dict]]:
        return [
            (f, m) for f, m in get_k8s_manifests() if m.get("kind") == "Ingress"
        ]

    def test_ingresses_have_rules(
        self, ingresses: list[tuple[str, dict]]
    ) -> None:
        """Test ingresses have rules defined."""
        for filename, manifest in ingresses:
            spec = manifest.get("spec", {})
            assert "rules" in spec, f"{filename} missing spec.rules"

    def test_ingresses_have_tls(
        self, ingresses: list[tuple[str, dict]]
    ) -> None:
        """Test ingresses have TLS configured for production."""
        for filename, manifest in ingresses:
            spec = manifest.get("spec", {})
            assert "tls" in spec, f"{filename} missing spec.tls for HTTPS"


class TestHPAManifests:
    """Tests for HorizontalPodAutoscaler manifests."""

    @pytest.fixture
    def hpas(self) -> list[tuple[str, dict]]:
        return [
            (f, m)
            for f, m in get_k8s_manifests()
            if m.get("kind") == "HorizontalPodAutoscaler"
        ]

    def test_hpas_have_scale_target(self, hpas: list[tuple[str, dict]]) -> None:
        """Test HPAs have scale target reference."""
        for filename, manifest in hpas:
            spec = manifest.get("spec", {})
            assert "scaleTargetRef" in spec, f"{filename} missing scaleTargetRef"

    def test_hpas_have_min_replicas(
        self, hpas: list[tuple[str, dict]]
    ) -> None:
        """Test HPAs have minimum replicas defined."""
        for filename, manifest in hpas:
            spec = manifest.get("spec", {})
            assert "minReplicas" in spec, f"{filename} missing minReplicas"
            assert spec["minReplicas"] >= 2, (
                f"{filename} minReplicas should be >= 2 for HA"
            )

    def test_hpas_have_max_replicas(
        self, hpas: list[tuple[str, dict]]
    ) -> None:
        """Test HPAs have maximum replicas defined."""
        for filename, manifest in hpas:
            spec = manifest.get("spec", {})
            assert "maxReplicas" in spec, f"{filename} missing maxReplicas"


class TestNamespaceConsistency:
    """Tests for namespace consistency across manifests."""

    def test_all_resources_in_same_namespace(self) -> None:
        """Test all resources are in the optimal-build namespace."""
        manifests = get_k8s_manifests()
        namespaces = set()

        for filename, manifest in manifests:
            ns = manifest.get("metadata", {}).get("namespace")
            if ns:
                namespaces.add(ns)

        # Should only have one namespace (plus possibly logging, monitoring)
        app_namespaces = {ns for ns in namespaces if "optimal" in ns}
        assert len(app_namespaces) <= 1, (
            f"Multiple app namespaces found: {app_namespaces}"
        )


class TestLabelConsistency:
    """Tests for label consistency."""

    def test_resources_have_app_label(self) -> None:
        """Test resources have app label."""
        manifests = get_k8s_manifests()

        for filename, manifest in manifests:
            kind = manifest.get("kind")
            if kind in ("Deployment", "Service", "Ingress"):
                labels = manifest.get("metadata", {}).get("labels", {})
                assert "app" in labels or "app.kubernetes.io/name" in labels, (
                    f"{filename} missing app label"
                )
