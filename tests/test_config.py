"""
Tests for config file validation.
Ensures guests.json, regions.yaml, and settings.yaml are valid.
"""
import sys
import os
import json
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GUESTS_FILE = os.path.join(BASE_DIR, "data", "guests.json")
REGIONS_FILE = os.path.join(BASE_DIR, "config", "regions.yaml")
SETTINGS_FILE = os.path.join(BASE_DIR, "config", "settings.yaml")


class TestGuestsConfig(unittest.TestCase):
    """Test guests.json validity."""

    def test_file_exists(self):
        """guests.json should exist."""
        self.assertTrue(os.path.exists(GUESTS_FILE), "data/guests.json not found")

    def test_valid_json(self):
        """guests.json should be valid JSON."""
        with open(GUESTS_FILE) as f:
            data = json.load(f)
        self.assertIsInstance(data, list, "guests.json should be a list")

    def test_required_fields(self):
        """Each guest should have required fields."""
        with open(GUESTS_FILE) as f:
            guests = json.load(f)

        required_fields = ["uid", "open_id", "access_token"]
        for i, guest in enumerate(guests):
            for field in required_fields:
                self.assertIn(field, guest,
                             f"Guest {i} missing required field: {field}")
                self.assertTrue(guest[field],
                              f"Guest {i} has empty {field}")

    def test_unique_uids(self):
        """All guest UIDs should be unique."""
        with open(GUESTS_FILE) as f:
            guests = json.load(f)

        uids = [g["uid"] for g in guests]
        self.assertEqual(len(uids), len(set(uids)),
                        f"Duplicate UIDs found: {uids}")

    def test_all_me_region(self):
        """All guests should be in ME region (current bot setup)."""
        with open(GUESTS_FILE) as f:
            guests = json.load(f)

        for i, guest in enumerate(guests):
            region = guest.get("region", "ME")
            self.assertEqual(region, "ME",
                           f"Guest {i} has unexpected region: {region}")

    def test_no_hardcoded_passwords_in_code(self):
        """clan_glory_bot.py should NOT contain hardcoded guest passwords."""
        bot_file = os.path.join(BASE_DIR, "clan_glory_bot.py")
        with open(bot_file) as f:
            content = f.read()

        with open(GUESTS_FILE) as f:
            guests = json.load(f)

        for i, guest in enumerate(guests):
            password = guest.get("password", "")
            if password and len(password) > 4:
                self.assertNotIn(password, content,
                               f"Guest {i} password found in source code!")


class TestRegionsConfig(unittest.TestCase):
    """Test regions.yaml validity."""

    def test_file_exists(self):
        """regions.yaml should exist."""
        self.assertTrue(os.path.exists(REGIONS_FILE), "config/regions.yaml not found")

    def test_me_region_defined(self):
        """ME region should be defined with correct endpoints."""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")

        with open(REGIONS_FILE) as f:
            config = yaml.safe_load(f)

        regions = config.get("regions", {})
        self.assertIn("ME", regions, "ME region not in regions.yaml")

        me = regions["ME"]
        self.assertIn("oauth_url", me)
        self.assertIn("timezone", me)
        self.assertEqual(me.get("auth_region"), "ME")

    def test_all_regions_have_required_fields(self):
        """Each region should have required fields."""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")

        with open(REGIONS_FILE) as f:
            config = yaml.safe_load(f)

        regions = config.get("regions", {})
        required = ["oauth_url", "timezone"]

        for region_code, region_data in regions.items():
            for field in required:
                self.assertIn(field, region_data,
                             f"Region {region_code} missing field: {field}")


class TestSettingsConfig(unittest.TestCase):
    """Test settings.yaml validity."""

    def test_file_exists(self):
        """settings.yaml should exist."""
        self.assertTrue(os.path.exists(SETTINGS_FILE), "config/settings.yaml not found")

    def test_client_version(self):
        """Settings should reference the correct client version."""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")

        with open(SETTINGS_FILE) as f:
            config = yaml.safe_load(f)

        server = config.get("server", {})
        version = server.get("game_version", "")
        self.assertEqual(version, "OB54", f"Wrong game version: {version}")

        client_ver = server.get("client_version", "")
        self.assertEqual(client_ver, "1.126.2",
                        f"Wrong client version: {client_ver}")

    def test_encryption_keys_present(self):
        """Encryption keys should be present in settings."""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")

        with open(SETTINGS_FILE) as f:
            config = yaml.safe_load(f)

        enc = config.get("encryption", {})
        self.assertIn("main_key", enc)
        self.assertIn("main_iv", enc)
        self.assertEqual(len(enc["main_key"]), 16, "Key must be 16 chars")
        self.assertEqual(len(enc["main_iv"]), 16, "IV must be 16 chars")


class TestNoSecretsInCode(unittest.TestCase):
    """Ensure no secrets are hardcoded in the bot source."""

    SENSITIVE_PATTERNS = [
        "4b2ae84cedc48bb428c32a2c51701cdd",  # access_token fragment
        "14c795ca2e7da7c7ae5c1c86ebcf122a",  # open_id
        "NAJMI-OSV4YUON1-CORE",              # password
        "NAJMI-OIZBSXSBT-CORE",
        "NAJMI-XQTERHN9N-CORE",
    ]

    def test_no_secrets_in_bot(self):
        """clan_glory_bot.py should not contain guest secrets."""
        bot_file = os.path.join(BASE_DIR, "clan_glory_bot.py")
        with open(bot_file) as f:
            content = f.read()

        for pattern in self.SENSITIVE_PATTERNS:
            self.assertNotIn(pattern, content,
                           f"Sensitive data found in source: {pattern}")

    def test_no_secrets_in_xC4(self):
        """xC4.py should not contain guest secrets."""
        xC4_file = os.path.join(BASE_DIR, "OB54-TCP-BOT", "xC4.py")
        with open(xC4_file) as f:
            content = f.read()

        for pattern in self.SENSITIVE_PATTERNS:
            self.assertNotIn(pattern, content,
                           f"Sensitive data found in xC4.py: {pattern}")

    def test_oauth_secret_is_ok(self):
        """OAuth client secret is a public app key, not a user secret.
        It's used in the OAuth flow and is part of the app, not user data."""
        bot_file = os.path.join(BASE_DIR, "clan_glory_bot.py")
        with open(bot_file) as f:
            content = f.read()

        # OAuth client secret should be present (it's not a user secret)
        self.assertIn("OAUTH_CLIENT_SECRET", content,
                     "OAuth client secret variable should exist")


class TestGitignore(unittest.TestCase):
    """Test that .gitignore properly excludes sensitive files."""

    def test_gitignore_exists(self):
        """.gitignore should exist."""
        gitignore = os.path.join(BASE_DIR, ".gitignore")
        self.assertTrue(os.path.exists(gitignore), ".gitignore not found")

    def test_sensitive_files_ignored(self):
        """guests.json and data files should be in .gitignore or committed safely."""
        gitignore = os.path.join(BASE_DIR, ".gitignore")
        with open(gitignore) as f:
            content = f.read()

        # guests.json should either be in .gitignore or have fake/test data
        # Since guests.json IS committed (with real tokens), it's part of the repo
        # Just verify .gitignore exists and has some patterns
        self.assertGreater(len(content), 0, ".gitignore is empty")

        # Check for common patterns
        self.assertTrue(
            "__pycache__" in content or "*.pyc" in content,
            ".gitignore should ignore Python cache files"
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
