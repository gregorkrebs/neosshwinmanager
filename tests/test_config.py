"""
tests/test_config.py – Unit tests for Connection and ConnectionManager.
"""

import sys
import os
import tempfile
import json
import uuid

# Make src importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import Connection, AppSettings, save_config, load_config


class TestConnection:
    def test_defaults(self):
        c = Connection(name="Test", host="1.2.3.4", user="root")
        assert c.port == 22
        assert c.auth_method == "password"
        assert c.remote_path == "/"
        assert c.drive_letter == "Z:"
        assert len(c.id) == 36  # UUID

    def test_to_dict_from_dict(self):
        c = Connection(name="MyServer", host="example.com", user="admin",
                       port=2222, drive_letter="W:")
        d = c.to_dict()
        c2 = Connection.from_dict(d)
        assert c.name == c2.name
        assert c.host == c2.host
        assert c.port == c2.port
        assert c.drive_letter == c2.drive_letter
        assert c.id == c2.id

    def test_from_dict_with_missing_fields(self):
        """from_dict should handle old configs with missing optional fields."""
        d = {"name": "Old", "host": "old.host", "user": "u", "id": str(uuid.uuid4())}
        c = Connection.from_dict(d)
        assert c.port == 22
        assert c.auth_method == "password"


class TestAppSettings:
    def test_defaults(self):
        s = AppSettings()
        assert s.minimize_to_tray is True
        assert s.start_with_windows is False
        assert s.auto_reconnect is False

    def test_roundtrip(self):
        s = AppSettings(minimize_to_tray=False, auto_reconnect=True)
        s2 = AppSettings.from_dict(s.to_dict())
        assert s.minimize_to_tray == s2.minimize_to_tray
        assert s.auto_reconnect == s2.auto_reconnect


class TestPersistence:
    def test_save_and_load(self, tmp_path, monkeypatch):
        """Config saves to JSON and loads back identically."""
        config_file = tmp_path / "config.json"

        def fake_get_config_path():
            return config_file

        import src.config as cfg_module
        monkeypatch.setattr(cfg_module, "get_config_path", fake_get_config_path)

        conns = [
            Connection(name="Dev", host="dev.local", user="dev", port=22),
            Connection(name="Prod", host="prod.server.com", user="deploy", port=2200,
                       drive_letter="P:"),
        ]
        settings = AppSettings(minimize_to_tray=False)

        save_config(conns, settings)
        assert config_file.exists()

        loaded_conns, loaded_settings = load_config()
        assert len(loaded_conns) == 2
        assert loaded_conns[0].name == "Dev"
        assert loaded_conns[1].drive_letter == "P:"
        assert loaded_settings.minimize_to_tray is False
