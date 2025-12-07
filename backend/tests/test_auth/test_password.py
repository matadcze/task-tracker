"""Tests for password utilities"""


from src.infrastructure.auth.password import PasswordUtils, hash_password, verify_password


class TestPasswordHashingFunctions:
    """Tests for module-level password functions"""

    def test_hash_password(self):
        """Test password hashing creates valid bcrypt hash"""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_hash_password_consistent(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different hashes due to different salts

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "TestPassword123"
        wrong_password = "WrongPassword123"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self):
        """Test password verification with empty string"""
        hashed = hash_password("TestPassword123")
        assert verify_password("", hashed) is False

    def test_hash_password_long_password(self):
        """Test hashing a very long password (over 72 char limit)"""
        long_password = "A" * 100
        hashed = hash_password(long_password)

        # bcrypt truncates at 72 bytes, verify it still works
        assert verify_password(long_password, hashed) is True
        # Also verify that only first 72 chars matter
        truncated = "A" * 72
        assert verify_password(truncated, hashed) is True


class TestPasswordUtilsClass:
    """Tests for PasswordUtils class"""

    def test_hash_password_method(self):
        """Test PasswordUtils.hash_password()"""
        password = "TestPassword123"
        hashed = PasswordUtils.hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_method_correct(self):
        """Test PasswordUtils.verify_password() with correct password"""
        password = "TestPassword123"
        hashed = PasswordUtils.hash_password(password)

        assert PasswordUtils.verify_password(password, hashed) is True

    def test_verify_password_method_incorrect(self):
        """Test PasswordUtils.verify_password() with incorrect password"""
        password = "TestPassword123"
        hashed = PasswordUtils.hash_password(password)

        assert PasswordUtils.verify_password("WrongPassword123", hashed) is False

    def test_password_utils_are_static(self):
        """Test that PasswordUtils methods are static and don't require instance"""
        password = "TestPassword123"

        # Should work without instantiation
        hashed = PasswordUtils.hash_password(password)
        assert PasswordUtils.verify_password(password, hashed) is True

    def test_hash_special_characters(self):
        """Test hashing password with special characters"""
        password = "P@ssw0rd!#$%^&*()"
        hashed = PasswordUtils.hash_password(password)

        assert PasswordUtils.verify_password(password, hashed) is True

    def test_hash_unicode_characters(self):
        """Test hashing password with unicode characters"""
        password = "Pässwörd123!日本語"
        hashed = PasswordUtils.hash_password(password)

        assert PasswordUtils.verify_password(password, hashed) is True
