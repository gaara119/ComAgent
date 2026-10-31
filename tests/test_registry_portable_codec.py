"""Portable credential protection is tested offline, without real secrets."""
import base64
import json

from cryptography.fernet import Fernet
import pytest

from qa_agent import database_registry as registry


@pytest.fixture(autouse=True)
def no_inherited_key(monkeypatch):
    monkeypatch.delenv("COMAGENT_CREDENTIAL_KEY", raising=False)


def test_fernet_roundtrip_is_authenticated_and_not_plaintext():
    key = Fernet.generate_key()
    codec = registry.FernetCredentialCodec(key)
    plain = b'{"password":"offline-fixture-only","database":"sample"}'
    ciphertext = codec.encrypt(plain)
    assert ciphertext != plain and b"offline-fixture-only" not in ciphertext
    assert registry.FernetCredentialCodec(key.decode()).decrypt(ciphertext) == plain
    assert codec.encrypt(plain) != ciphertext  # Random IV, not a fixed obfuscation.


@pytest.mark.parametrize("fault", ["wrong_key", "tampered", "plaintext"])
def test_wrong_key_tamper_or_plaintext_is_never_accepted(fault):
    key = Fernet.generate_key()
    codec = registry.FernetCredentialCodec(key)
    secret = b"offline-fixture-only"
    ciphertext = codec.encrypt(secret)
    if fault == "wrong_key":
        codec = registry.FernetCredentialCodec(Fernet.generate_key())
    elif fault == "tampered":
        decoded = bytearray(base64.urlsafe_b64decode(ciphertext))
        decoded[-1] ^= 1
        ciphertext = base64.urlsafe_b64encode(decoded)
    else:
        ciphertext = secret
    with pytest.raises(registry.DatabaseRegistryError) as error:
        codec.decrypt(ciphertext)
    assert error.value.code == "CREDENTIAL_PROTECTION_FAILED"
    assert key.decode() not in str(error.value)
    assert secret.decode() not in str(error.value)


@pytest.mark.parametrize("invalid", ["not-a-key", " ", "a" * 43, "a" * 44, "中" * 44])
def test_invalid_key_is_rejected_without_disclosing_it(monkeypatch, invalid):
    monkeypatch.setenv("COMAGENT_CREDENTIAL_KEY", invalid)
    for platform in ("nt", "posix"):
        with pytest.raises(registry.DatabaseRegistryError) as error:
            registry._default_credential_codec(platform)
        assert error.value.code == "CREDENTIAL_KEY_INVALID"
        if invalid.strip():
            assert invalid not in str(error.value)
        assert error.value.status_code == 503


def test_windows_still_defaults_to_dpapi_with_no_portable_key():
    assert isinstance(registry._default_credential_codec("nt"), registry.WindowsDPAPICodec)


def test_non_windows_requires_key_for_both_encrypt_and_decrypt():
    codec = registry._default_credential_codec("posix")
    assert isinstance(codec, registry.UnavailableCredentialCodec)
    for action, value in ((codec.encrypt, b"fixture-password"), (codec.decrypt, b"ciphertext")):
        with pytest.raises(registry.DatabaseRegistryError) as error:
            action(value)
        assert error.value.code == "CREDENTIAL_PROTECTION_UNAVAILABLE"
        assert error.value.status_code == 503


@pytest.mark.parametrize("platform", ["nt", "posix"])
def test_configured_key_selects_authenticated_codec_on_either_platform(monkeypatch, platform):
    monkeypatch.setenv("COMAGENT_CREDENTIAL_KEY", Fernet.generate_key().decode())
    codec = registry._default_credential_codec(platform)
    assert isinstance(codec, registry.FernetCredentialCodec)
    assert codec.decrypt(codec.encrypt(b"roundtrip")) == b"roundtrip"


def test_no_key_still_allows_public_registration_listing(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "_default_credential_codec", lambda: registry.UnavailableCredentialCodec())
    store = registry.DatabaseRegistry(root=tmp_path)
    assert store.list_registered() == []
    # A persisted public record can be listed without decrypting credentials.
    db_id = "pg-" + "a" * 32
    version = "b" * 32
    record = {"version": 1, "db_id": db_id, "name": "Offline public catalog",
              "protected_connection": base64.b64encode(b"not-decrypted-for-listing").decode(),
              "catalog_version": version, "catalog_summary": {"table_count": 0},
              "connection": {"host": "localhost", "port": 5432, "database": "sample",
                             "user": "reader", "sslmode": "prefer", "schemas": []},
              "created_at": "2026-10-31T00:00:00+00:00", "updated_at": "2026-10-31T00:00:00+00:00"}
    (tmp_path / (db_id + ".json")).write_text(json.dumps(record), encoding="utf-8")
    (tmp_path / (db_id + "-" + version + ".yaml")).write_text("tables: []\n", encoding="utf-8")
    public = store.list_registered()
    assert public[0]["name"] == "Offline public catalog"
    assert "protected_connection" not in public[0]
    with pytest.raises(registry.DatabaseRegistryError) as error:
        store.get_connection(db_id)
    assert error.value.code == "CREDENTIAL_PROTECTION_UNAVAILABLE"


def test_registry_factory_keeps_explicit_codec_injection(tmp_path, monkeypatch):
    monkeypatch.setenv("COMAGENT_CREDENTIAL_KEY", "invalid-nonempty-key")
    explicit = registry.UnavailableCredentialCodec()
    assert registry.DatabaseRegistry(root=tmp_path, codec=explicit).codec is explicit
