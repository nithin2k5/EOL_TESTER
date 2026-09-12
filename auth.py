"""Password hashing and verification helpers for EOL Tester logins.

Stored passwords are kept as a salted digest, base64 encoded:

    base64( digest(password_utf8 + salt) + salt )

The salt is 4 to 7 cryptographically random non-zero bytes. It is appended
to the plain text before hashing and appended again to the raw digest
afterwards, so verification can recover it from the tail of the decoded
value without storing it in a separate column.

Run this module directly to generate a hash for a password, which is how
the service account credential in .env is produced:

    python auth.py "my password"
"""

import base64
import binascii
import hashlib
import secrets
import sys

DEFAULT_ALGORITHM = 'SHA512'

# Digest length in bytes, keyed by the algorithm name stored alongside it.
_HASH_SIZES = {
    'MD5': 16,
    'SHA384': 48,
    'SHA512': 64,
}

MIN_SALT_SIZE = 4
MAX_SALT_SIZE = 8  # exclusive, so salts are 4-7 bytes long


def _resolve(hash_algorithm):
    """Return the (name, digest size) pair for an algorithm, defaulting to MD5."""
    name = (hash_algorithm or '').upper()
    if name not in _HASH_SIZES:
        name = 'MD5'
    return name, _HASH_SIZES[name]


def _generate_salt():
    """Build a random salt of 4-7 non-zero bytes."""
    size = MIN_SALT_SIZE + secrets.randbelow(MAX_SALT_SIZE - MIN_SALT_SIZE)
    salt = bytearray()
    while len(salt) < size:
        byte = secrets.randbits(8)
        if byte:
            salt.append(byte)
    return bytes(salt)


def compute_hash(plain_text, hash_algorithm=DEFAULT_ALGORITHM, salt_bytes=None):
    """Hash plain_text with the given salt, generating one when not supplied."""
    name, _ = _resolve(hash_algorithm)
    if salt_bytes is None:
        salt_bytes = _generate_salt()

    digest = hashlib.new(name.lower(), plain_text.encode('utf-8') + salt_bytes).digest()
    return base64.b64encode(digest + salt_bytes).decode('ascii')


def _decode(hash_value):
    """Decode a stored hash, returning None when it is not valid base64."""
    if not isinstance(hash_value, str):
        return None
    try:
        return base64.b64decode(hash_value, validate=True)
    except (binascii.Error, ValueError):
        return None


def looks_hashed(stored_value, hash_algorithm=DEFAULT_ALGORITHM):
    """True when stored_value has the shape of a salted hash rather than plain text."""
    _, hash_size = _resolve(hash_algorithm)
    raw = _decode(stored_value)
    # A real hash is the digest plus at least one salt byte.
    return raw is not None and len(raw) > hash_size


def verify_hash(plain_text, hash_algorithm, hash_value):
    """Check plain_text against a salted hash produced by compute_hash."""
    name, hash_size = _resolve(hash_algorithm)
    raw = _decode(hash_value)
    if raw is None or len(raw) < hash_size:
        return False

    salt_bytes = raw[hash_size:]
    return secrets.compare_digest(compute_hash(plain_text, name, salt_bytes), hash_value)


def verify_password(plain_text, stored_value, hash_algorithm=DEFAULT_ALGORITHM):
    """Check a password against a stored value that may be hashed or plain text.

    Employee rows created before hashing was introduced hold the password
    verbatim, so those are compared directly. Anything with the shape of a
    salted hash goes through verify_hash.
    """
    if plain_text is None or stored_value is None:
        return False

    if looks_hashed(stored_value, hash_algorithm):
        return verify_hash(plain_text, hash_algorithm, stored_value)

    return secrets.compare_digest(plain_text, stored_value)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python auth.py "<password>"')
        raise SystemExit(1)
    print(compute_hash(sys.argv[1]))
