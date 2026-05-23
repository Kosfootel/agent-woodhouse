# Vigil Credential Vault - Master Key Setup Guide

## Overview

The Credential Vault Service uses AES-256-GCM encryption to protect home automation credentials at rest. This guide explains how to generate and configure the master encryption key.

## Security Model

- **Encryption at Rest**: All credentials are encrypted using AES-256-GCM
- **Master Key**: Derived from a single environment variable (`VIGIL_VAULT_MASTER_KEY`)
- **Key Derivation**: Uses PBKDF2 with 100,000 iterations and a static salt
- **Unique Nonces**: Each encryption operation uses a cryptographically random nonce
- **No Plaintext Storage**: Credential values are never stored in plaintext

## Master Key Generation

### Option 1: Using OpenSSL (Recommended)

```bash
# Generate a 256-bit base64-encoded key
openssl rand -base64 32

# Example output:
# xK7mJQn9vLw3pTcYbR5sHdE8gAfK2mPqRsTuVwXyZaBc=
```

### Option 2: Using Python

```python
import secrets

# Generate a URL-safe base64 key
key = secrets.token_urlsafe(32)
print(key)
```

### Option 3: Using the Vault Service

```python
from app.vault.vault_encryption import VaultEncryptionService

# Generate and print a new key
new_key = VaultEncryptionService.generate_master_key()
print(new_key)
```

## Environment Configuration

### Development

```bash
# Add to .env file or export in shell
export VIGIL_VAULT_MASTER_KEY="your-generated-key-here"

# Example:
export VIGIL_VAULT_MASTER_KEY="xK7mJQn9vLw3pTcYbR5sHdE8gAfK2mPqRsTuVwXyZaBc="
```

### Production (Systemd Service)

Edit `/etc/systemd/system/vigil.service`:

```ini
[Service]
Environment="VIGIL_VAULT_MASTER_KEY=xK7mJQn9vLw3pTcYbR5sHdE8gAfK2mPqRsTuVwXyZaBc="
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart vigil
```

### Production (Docker)

```yaml
# docker-compose.yml
version: '3.8'
services:
  vigil:
    image: vigil:latest
    environment:
      - VIGIL_VAULT_MASTER_KEY=${VIGIL_VAULT_MASTER_KEY}
    env_file:
      - .env.production
```

Create `.env.production` (chmod 600):
```bash
VIGIL_VAULT_MASTER_KEY=xK7mJQn9vLw3pTcYbR5sHdE8gAfK2mPqRsTuVwXyZaBc=
```

### Production (Kubernetes Secret)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: vigil-vault-master-key
type: Opaque
stringData:
  VIGIL_VAULT_MASTER_KEY: "xK7mJQn9vLw3pTcYbR5sHdE8gAfK2mPqRsTuVwXyZaBc="
```

Apply:
```bash
kubectl apply -f vault-master-key-secret.yaml
```

## Security Best Practices

### 1. Key Storage

- **Never commit** the master key to version control
- **Never log** the master key (it will be redacted in logs)
- **Restrict file permissions** on `.env` files: `chmod 600 .env`
- **Use secret management** in production (AWS Secrets Manager, Vault, etc.)

### 2. Key Rotation

Currently, key rotation requires re-encrypting all credentials:

```python
# Example key rotation script (backup first!)
from app.vault.vault_service import VaultService
from app.vault.vault_encryption import VaultEncryptionService
from app.database import get_db

# 1. Backup database
db = next(get_db())

# 2. Decrypt all credentials with old key
old_service = VaultService()
credentials = old_service.list_credentials(db, "admin", limit=10000)

# 3. Switch to new key
os.environ["VIGIL_VAULT_MASTER_KEY"] = "new-master-key"
new_encryption = VaultEncryptionService()
new_service = VaultService(new_encryption)

# 4. Re-encrypt all credentials
for cred in credentials:
    _, decrypted = old_service.get_credential(db, cred.id, "admin", decrypt=True)
    new_service.rotate_credential(db, cred.id, "admin", decrypted)
```

**Note**: Future versions may support transparent key rotation.

### 3. Backup Considerations

- **Database backups** include encrypted credentials - these are safe
- **Master key** must be backed up separately and securely
- **Test restoration** of master key periodically
- **Store key in multiple secure locations** (e.g., password manager + offline backup)

### 4. Monitoring

Monitor for:
- Failed decryption attempts (potential tampering)
- Unusual access patterns in audit logs
- Master key environment variable not set errors

## Troubleshooting

### Error: "VIGIL_VAULT_MASTER_KEY not set"

```
VaultEncryptionError: VIGIL_VAULT_MASTER_KEY not set. Generate with: openssl rand -base64 32
```

**Solution**: Set the environment variable as described above.

### Error: "Failed to decrypt credential"

```
VaultEncryptionError: Failed to decrypt credential: ...
```

**Possible causes**:
1. Wrong master key (check environment)
2. Corrupted database (restore from backup)
3. Tampered data (check system compromise)

**Solution**:
1. Verify `VIGIL_VAULT_MASTER_KEY` matches the key used during encryption
2. Check database integrity
3. Restore from backup if necessary

### Lost Master Key

**If you lose the master key, the credentials cannot be recovered.**

**Recovery steps**:
1. Rotate all credentials at their source (Hue Bridge, Nest, etc.)
2. Generate new master key
3. Delete old encrypted credentials from vault
4. Re-add credentials with new values

**Prevention**:
- Store master key in password manager
- Maintain offline backup of master key
- Document key location for disaster recovery

## Configuration Summary

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VIGIL_VAULT_MASTER_KEY` | Yes | None | Master encryption key (base64) |

## Verification

Test your setup:

```bash
# Set key
export VIGIL_VAULT_MASTER_KEY=$(openssl rand -base64 32)

# Run tests
cd ~/projects/vigil-home/projects/vigil-home/poc-backend
python -m pytest app/vault/tests/test_vault.py -v

# Test encryption directly
python -c "
from app.vault.vault_encryption import VaultEncryptionService

service = VaultEncryptionService()
encrypted = service.encrypt('test-secret')
decrypted = service.decrypt(encrypted)
assert decrypted == 'test-secret'
print('✓ Encryption/decryption working')
"
```

## Related Documentation

- [Credential Vault API](./vault-api.md)
- [Security Hardening Plan](../../SECURITY-HARDENING-PLAN.md)
- [Incident Response Playbooks](../../INCIDENT-RESPONSE-PLAYBOOKS.md)
