"""Packaging lifecycle and proxy boundary checks; no remote models."""
import importlib.util
import os
from pathlib import Path
import pytest
from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_container_credential_key_survives_restart(tmp_path, monkeypatch):
    module = load('container_entrypoint_check', 'deployment/container_entrypoint.py')
    monkeypatch.delenv('COMAGENT_CREDENTIAL_KEY', raising=False)
    first = module.credential_key(tmp_path)
    encrypted = Fernet(first.encode()).encrypt(b'private-example')
    second = module.credential_key(tmp_path)
    assert first == second
    assert Fernet(second.encode()).decrypt(encrypted) == b'private-example'
    if os.name != 'nt':
        assert (tmp_path / 'credential.key').stat().st_mode & 0o077 == 0


def test_explicit_key_does_not_write_secret_file(tmp_path, monkeypatch):
    module = load('container_explicit_key_check', 'deployment/container_entrypoint.py')
    key = Fernet.generate_key().decode()
    monkeypatch.setenv('COMAGENT_CREDENTIAL_KEY', key)
    assert module.credential_key(tmp_path) == key
    assert not (tmp_path / 'credential.key').exists()


@pytest.mark.parametrize('value',[0,-1,65536])
def test_invalid_public_port_rejected(value):
    module = load('container_port_check', 'frontend-workbench/run_ui.py')
    with pytest.raises(ValueError):
        module.make_handler('http://127.0.0.1:8000', value)


def test_api_documentation_is_read_only_proxy_route():
    module = load('container_docs_check', 'frontend-workbench/run_ui.py')
    for path in ('/docs','/redoc','/openapi.json'):
        assert module.allowed_api(path,'GET')
        assert not module.allowed_api(path,'POST')
