import importlib.util
import os
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

        env = {
            "CONFIG_DIR": self.config_dir,
            "BACKUP_DIR": self.backup_dir,
            "SERVER_DIR": self.server_dir,
            "AUTH_MODE": "BASIC",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "password123",
            "SECRET_KEY": "test-secret-key",
            "FLASK_ENV": "development",
        }
        self.module = load_app_module(env)
        self.client = self.module.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_login_rejects_missing_csrf(self):
        self.client.get("/")
        response = self.client.post("/login", json={"username": "admin", "password": "password123"})
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


if __name__ == "__main__":
    unittest.main()
