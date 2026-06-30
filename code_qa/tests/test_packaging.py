"""Packaging regression tests for the public CLI surface."""
from __future__ import annotations

import importlib
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"


def test_pyproject_declares_installable_console_scripts() -> None:
    assert PYPROJECT.exists(), "phantom-enterprise must be installable with pip -e ."
    with PYPROJECT.open("rb") as fp:
        project = tomllib.load(fp)["project"]

    assert project["name"] == "phantom-enterprise"
    assert project["version"] == "0.1.0a0"
    assert project["scripts"] == {
        "phantom-enterprise": "code_qa.cli:main",
        "phantom-enterprise-demo-loop": "code_qa.demo_loop:main",
        "phantom-enterprise-connector-matrix": "code_qa.connector_matrix:main",
        "phantom-enterprise-knowledge-scenario": "code_qa.knowledge_lookup_scenario:main",
        "phantom-enterprise-mcp": "code_qa.mcp_server:main",
    }


def test_pyproject_declares_public_package_metadata() -> None:
    with PYPROJECT.open("rb") as fp:
        project = tomllib.load(fp)["project"]

    classifiers = set(project["classifiers"])
    urls = project["urls"]

    assert "Development Status :: 3 - Alpha" in classifiers
    assert "License :: OSI Approved :: Apache Software License" in classifiers
    assert "Programming Language :: Python :: 3.11" in classifiers
    assert urls["Homepage"] == "https://github.com/markl-a/phantom-enterprise"
    assert urls["Repository"] == "https://github.com/markl-a/phantom-enterprise"
    assert urls["Issues"] == "https://github.com/markl-a/phantom-enterprise/issues"


def test_console_script_targets_are_importable_and_callable() -> None:
    with PYPROJECT.open("rb") as fp:
        scripts = tomllib.load(fp)["project"]["scripts"]

    for target in scripts.values():
        module_name, _, attr = target.partition(":")
        module = importlib.import_module(module_name)
        entry = getattr(module, attr)
        assert callable(entry), target
