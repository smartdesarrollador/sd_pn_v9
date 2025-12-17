"""
Master Password Manager
Manages master password for protecting sensitive items and exports
Separate from login password (auth_manager.py)
"""
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv, set_key
import os
import logging

logger = logging.getLogger(__name__)


class MasterPasswordManager:
    """
    Manages master password authentication

    Master password is OPTIONAL and separate from login password.
    Used to protect:
    - Sensitive items (is_sensitive=True)
    - Exports containing sensitive data

    If no master password is configured, system works normally without additional protection.
    """

    def __init__(self, env_file: str = ".env"):
        """
        Initialize MasterPasswordManager

        Args:
            env_file: Path to .env file (default: ".env")
        """
        self.env_file = Path(env_file)

        # Ensure .env file exists
        if not self.env_file.exists():
            self.env_file.touch()

        # Load environment variables
        load_dotenv(self.env_file)

    def _get_env(self, key: str, default: str = "") -> str:
        """Get environment variable value"""
        return os.getenv(key, default)

    def _set_env(self, key: str, value: str):
        """Set environment variable value in .env file"""
        env_path = str(self.env_file)
        set_key(env_path, key, value)
        # Update os.environ immediately
        os.environ[key] = value

    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash password with SHA256 + salt

        Args:
            password: Plain text password
            salt: Optional salt (generates random if None)

        Returns:
            Tuple of (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)  # 64 characters

        # Combine password + salt
        salted = password + salt

        # Hash with SHA256
        hash_obj = hashlib.sha256(salted.encode())
        password_hash = hash_obj.hexdigest()

        return password_hash, salt

    def verify_master_password(self, password: str) -> bool:
        """
        Verify password against stored master password hash

        Args:
            password: Plain text password to verify

        Returns:
            True if password is correct, False otherwise
        """
        stored_hash = self._get_env("MASTER_PASSWORD_HASH")
        stored_salt = self._get_env("MASTER_PASSWORD_SALT")

        if not stored_hash or not stored_salt:
            logger.warning("No master password configured - verification failed")
            return False

        # Hash the provided password with stored salt
        new_hash, _ = self.hash_password(password, stored_salt)

        is_valid = new_hash == stored_hash
        if is_valid:
            logger.info("Master password verified successfully")
        else:
            logger.warning("Master password verification failed - incorrect password")

        return is_valid

    def is_first_time(self) -> bool:
        """
        Check if this is the first time (no master password set)

        Returns:
            True if no master password hash exists, False otherwise
        """
        password_hash = self._get_env("MASTER_PASSWORD_HASH")
        return not password_hash

    def has_master_password(self) -> bool:
        """
        Check if master password is configured

        IMPORTANT: Use this to determine if master password protection is active.
        If False, allow access without asking for password.

        Returns:
            True if master password exists, False otherwise
        """
        password_hash = self._get_env("MASTER_PASSWORD_HASH")
        has_password = bool(password_hash)

        if has_password:
            logger.debug("Master password is configured")
        else:
            logger.debug("Master password is NOT configured - protection disabled")

        return has_password

    def set_master_password(self, password: str):
        """
        Set new master password (hash and save to .env)
        Use this for FIRST TIME creation.

        Args:
            password: Plain text password
        """
        password_hash, salt = self.hash_password(password)

        # Save to .env
        self._set_env("MASTER_PASSWORD_HASH", password_hash)
        self._set_env("MASTER_PASSWORD_SALT", salt)

        logger.info("Master password created successfully")

    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """
        Change master password (verify old password first)

        Args:
            old_password: Current master password
            new_password: New master password

        Returns:
            True if password changed successfully, False if old password incorrect
        """
        # Verify old password
        if not self.verify_master_password(old_password):
            logger.warning("Failed to change master password - old password incorrect")
            return False

        # Set new password
        self.set_master_password(new_password)
        logger.info("Master password changed successfully")
        return True

    def remove_master_password(self):
        """
        Remove master password (disable protection)

        WARNING: This will disable master password protection.
        Sensitive items will be accessible without additional authentication.
        """
        self._set_env("MASTER_PASSWORD_HASH", "")
        self._set_env("MASTER_PASSWORD_SALT", "")
        logger.warning("Master password removed - protection disabled")
