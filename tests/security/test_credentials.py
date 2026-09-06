import pytest
from core.security.credentials import SecureCredentialVault


def test_credential_vault_lifecycle(tmp_path):
    vault_file = str(tmp_path / "test_vault.bin")
    vault = SecureCredentialVault(vault_path=vault_file)

    # Initially empty
    assert vault.list_keys() == []
    assert vault.retrieve_secret("DB_PASSWORD") is None

    # Store secrets
    vault.store_secret("DB_PASSWORD", "SuperSecretCoalIndia2025!")
    vault.store_secret("LOCAL_HMAC_KEY", "789123abcdef")

    assert set(vault.list_keys()) == {"DB_PASSWORD", "LOCAL_HMAC_KEY"}
    assert vault.retrieve_secret("DB_PASSWORD") == "SuperSecretCoalIndia2025!"
    assert vault.retrieve_secret("LOCAL_HMAC_KEY") == "789123abcdef"

    # Reload vault from disk (simulate service restart)
    vault_reloaded = SecureCredentialVault(vault_path=vault_file)
    assert vault_reloaded.retrieve_secret("DB_PASSWORD") == "SuperSecretCoalIndia2025!"
    assert vault_reloaded.retrieve_secret("LOCAL_HMAC_KEY") == "789123abcdef"

    # Delete secret
    assert vault_reloaded.delete_secret("DB_PASSWORD") is True
    assert vault_reloaded.retrieve_secret("DB_PASSWORD") is None
    assert vault_reloaded.list_keys() == ["LOCAL_HMAC_KEY"]
