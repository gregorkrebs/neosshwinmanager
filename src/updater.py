import os
import sys
import json
import urllib.request
import urllib.error
import threading
import tempfile
import subprocess
from packaging import version
from PyQt6.QtCore import QObject, pyqtSignal
from src.app_logger import logger

GITHUB_API_URL = "https://api.github.com/repos/gregorkrebs/neosshwinmanager/releases/latest"

class UpdaterManager(QObject):
    update_available = pyqtSignal(str, str, str, str)  # version, changelog, download_url, obj_type
    no_update_available = pyqtSignal()
    check_failed = pyqtSignal(str)
    download_progress = pyqtSignal(int)
    download_finished = pyqtSignal(bool, str) # success, msg/path

    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
        self.update_file_path = None
        self._is_downloading = False

    def check_for_updates_async(self):
        """Checks in the background whether a new version is available."""
        def _worker():
            try:
                req = urllib.request.Request(GITHUB_API_URL, headers={"User-Agent": "NeoSSHWinManager-Updater"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                
                latest_version_tag = data.get("tag_name", "").lstrip("v")
                if not latest_version_tag:
                    self.check_failed.emit("GitHub API returned no tag_name")
                    return

                # Compare versions using packaging.version for proper semantic versioning
                if version.parse(latest_version_tag) > version.parse(self.current_version):
                    changelog = data.get("body", "No changelog available.")
                    download_url = ""
                    obj_type = "browser"

                    # Search for .exe release asset, prefer CLI version if available
                    for asset in data.get("assets", []):
                        if asset.get("name", "").endswith(".exe") and "cli" not in asset.get("name", "").lower():
                            download_url = asset.get("browser_download_url", "")
                            obj_type = "exe"
                            break

                    if not download_url:
                        # Fallback to the release page if no direct .exe asset is found
                        download_url = data.get("html_url", "")
                        obj_type = "browser"

                    self.update_available.emit(latest_version_tag, changelog, download_url, obj_type)
                else:
                    self.no_update_available.emit()

            except Exception as e:
                logger.warning(f"Failed to check for updates: {e}")
                try:
                    self.check_failed.emit(str(e))
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()

    def download_update_async(self, download_url: str):
        if self._is_downloading:
            return
        self._is_downloading = True

        def _worker():
            try:
                temp_dir = tempfile.gettempdir()
                self.update_file_path = os.path.join(temp_dir, "NeoSSHWinManager_update.exe")

                # urllib für den Download mit Progress
                req = urllib.request.Request(download_url, headers={"User-Agent": "NeoSSHWinManager-Updater"})
                with urllib.request.urlopen(req, timeout=15) as response:
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded = 0
                    chunk_size = 8192
                    
                    with open(self.update_file_path, "wb") as f:
                        while True:
                            buffer = response.read(chunk_size)
                            if not buffer:
                                break
                            f.write(buffer)
                            downloaded += len(buffer)
                            if total_size > 0:
                                percent = int((downloaded / total_size) * 100)
                                self.download_progress.emit(percent)
                
                self.download_finished.emit(True, self.update_file_path)
            except Exception as e:
                logger.error(f"Download failed: {e}")
                self.download_finished.emit(False, str(e))
            finally:
                self._is_downloading = False

        threading.Thread(target=_worker, daemon=True).start()

    def install_on_exit(self):
        """Creates a batch file that will be executed when the app closes."""
        if not self.update_file_path or not os.path.exists(self.update_file_path):
            return

        current_exe = sys.executable
        # Only perform the swap if we are actually running as a compiled .exe
        if not getattr(sys, 'frozen', False):
            logger.info("Not running as frozen exe, skipping physical replace.")
            return

        bat_path = os.path.join(tempfile.gettempdir(), "neosshwinmanager_updater.bat")
        
        # Batch script that waits for the main process to exit, then replaces the file
        bat_content = f"""@echo off
echo Warte auf das Beenden von NeoSSHWinManager...
timeout /t 3 /nobreak >nul
del "{current_exe}" /f /q
move /y "{self.update_file_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        try:
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)
        except Exception as e:
            logger.error(f"Failed to write updater.bat: {e}")
            return

        # Start Batch file hidden and detached
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(["cmd.exe", "/c", bat_path], startupinfo=startupinfo, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        logger.info("Updater batch scheduled for exit.")
