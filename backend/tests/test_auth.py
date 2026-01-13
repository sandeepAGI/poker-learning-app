"""Test authentication functions."""
import pytest
from auth import hash_password, verify_password, create_token, verify_token_string
from datetime import datetime, timedelta
import jwt
import os

class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_bcrypt_hash(self):
        """Password should be hashed with bcrypt."""
        password = "test123"
        hashed = hash_password(password)

        assert hashed != password  # Not plaintext
        assert len(hashed) == 60  # bcrypt hash length
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_hash_password_different_each_time(self):
        """Same password should produce different hashes (salt)."""
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Correct password should verify."""
        password = "test123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """Wrong password should not verify."""
        password = "test123"
        wrong = "wrong456"
        hashed = hash_password(password)

        assert verify_password(wrong, hashed) is False

    def test_verify_password_empty(self):
        """Empty password should work (validation elsewhere)."""
        password = ""
        hashed = hash_password(password)

        assert verify_password("", hashed) is True
        assert verify_password("x", hashed) is False

class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_token_returns_jwt(self):
        """Should return valid JWT string."""
        user_id = "test-user-123"
        token = create_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0
        assert len(token.split('.')) == 3  # header.payload.signature

    def test_create_token_includes_user_id(self):
        """Token should contain user_id in 'sub' claim."""
        user_id = "test-user-123"
        token = create_token(user_id)

        # Decode to verify (don't verify signature for test)
        secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        assert payload["sub"] == user_id

    def test_create_token_has_expiration(self):
        """Token should expire in 30 days."""
        user_id = "test-user-123"
        token = create_token(user_id)

        secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(days=30)
        time_diff = abs((exp_time - expected_exp).total_seconds())

        assert time_diff < 10  # Within 10 seconds

    def test_verify_token_string_valid(self):
        """Valid token should return user_id."""
        user_id = "test-user-123"
        token = create_token(user_id)

        result = verify_token_string(token)
        assert result == user_id

    def test_verify_token_string_expired(self):
        """Expired token should raise exception."""
        from fastapi import HTTPException

        # Create expired token
        user_id = "test-user-123"
        secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() - timedelta(days=1)
        }
        expired_token = jwt.encode(payload, secret, algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            verify_token_string(expired_token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_token_string_invalid_signature(self):
        """Token with wrong signature should raise exception."""
        from fastapi import HTTPException

        # Create token with wrong secret
        user_id = "test-user-123"
        wrong_secret = "wrong-secret"
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        invalid_token = jwt.encode(payload, wrong_secret, algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            verify_token_string(invalid_token)

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()

    def test_verify_token_string_malformed(self):
        """Malformed token should raise exception."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            verify_token_string("not-a-jwt-token")

        assert exc_info.value.status_code == 401
