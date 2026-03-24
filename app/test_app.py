import importlib.util
import os
import secrets
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP_PATH = ROOT / "app" / "app.py"


def load_app_module(env_overrides):
    for key, value in env_overrides.items():
        os.environ[key] = str(value)

    module_name = f"beammp_app_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, APP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SecurityRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        base = Path(self.temp_dir.name)
        self.config_dir = base / "config"
        self.backup_dir = base / "backup"
        self.server_dir = base / "server"
        self.config_dir.mkdir()
        self.backup_dir.mkdir()
        self.server_dir.mkdir()
        self.admin_username = "admin"
        self.admin_password = secrets.token_urlsafe(18)

        env = {
            "AUTH_MODE": "BASIC",
            "ADMIN_USERNAME": self.admin_username,
            "ADMIN_PASSWORD": self.admin_password,
            "SECRET_KEY": "test-secret-key",
            "FLASK_ENV": "development",
        }
        self.module = load_app_module(env)
        self.module.app.config.update(
            CONFIG_DIR=str(self.config_dir),
            BACKUP_DIR=str(self.backup_dir),
            SERVER_DIR=str(self.server_dir),
        )
        self.module.refresh_storage_paths()
        self.module.ensure_runtime_directories()
        self.client = self.module.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_login_rejects_missing_csrf(self):
        self.client.get("/")
        response = self.client.post("/login", json={"username": self.admin_username, "password": self.admin_password})
        self.assertEqual(response.status_code, 403)

    def test_backup_restore_is_not_exposed_via_get(self):
        backup_file = self.backup_dir / "ServerConfig_backup_test.toml"
        backup_file.write_text("[General]\nName='Test'\n", encoding="utf-8")
        response = self.client.get(f"/backup/{backup_file.name}")
        self.assertEqual(response.status_code, 405)

    def test_user_config_rejects_path_traversal_log_filename(self):
        self.client.get("/")
        with self.client.session_transaction() as session:
            session["basic_user"] = "admin"
            csrf_token = session["csrf_token"]

        response = self.client.post(
            "/api/user-config",
            json={"serverLogFilename": "../secret.log"},
            headers={"X-CSRF-Token": csrf_token},
        )
        self.assertEqual(response.status_code, 400)

    def test_only_relative_redirect_targets_are_allowed(self):
        with self.module.app.test_request_context("/oauth/login?next=https://evil.example/"):
            self.assertEqual(self.module.get_next_redirect_target(), self.module.url_for("index"))
        with self.module.app.test_request_context("/oauth/login?next=/api/config"):
            self.assertEqual(self.module.get_next_redirect_target(), "/api/config")

    def test_safe_join_blocks_escape_from_base_directory(self):
        allowed = self.module.safe_join(str(self.backup_dir), "test.toml")
        blocked = self.module.safe_join(str(self.backup_dir), "../outside.toml")
        self.assertTrue(str(allowed).startswith(str(self.backup_dir)))
        self.assertIsNone(blocked)

    def test_oauth_redirect_uri_must_be_absolute_http_or_https(self):
        with self.assertRaises(RuntimeError):
            self.module.validate_absolute_http_url("/oauth/callback")


if __name__ == "__main__":
    unittest.main()
