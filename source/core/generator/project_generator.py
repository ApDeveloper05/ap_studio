"""
------------------------------------------------------------
File: project_generator.py

Module: Core Generator

Purpose:
Generate and initialize new AP Studio production-ready Django projects
with pre-configured Authentication Engine, OTP, and Security Layers.

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from source.core.logger.logger import error, info, success


class ProjectGenerator:
    """
    Handles enterprise Django project creation and auth engine injection.
    """

    def __init__(
        self,
        project_name: str,
        app_name: str = "main",
        target_dir: Path | str | None = None,
        python_executable: str | None = None,
    ):
        self.project_name = project_name.strip()
        self.app_name = app_name.strip()
        self.base_dir = Path(target_dir).resolve() if target_dir else Path.cwd()
        self.project_root = self.base_dir / self.project_name
        self.inner_project = self.project_root / self.project_name
        self.python_exe = python_executable or sys.executable

    def create(self) -> bool:
        """
        Execute full project scaffolding and auth engine injection.
        """
        info(f"Initializing AP Studio Project: {self.project_name}")

        try:
            # 1. Create base project folder
            if not self.project_root.exists():
                self.project_root.mkdir(parents=True, exist_ok=True)

            # 2. Start Django project
            info(f"Generating Django project skeleton: {self.project_name}...")
            subprocess.run(
                [self.python_exe, "-m", "django", "startproject", self.project_name, "."],
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True,
            )

            # 3. Create Main App
            if self.app_name:
                info(f"Generating main domain application: {self.app_name}...")
                subprocess.run(
                    [self.python_exe, "manage.py", "startapp", self.app_name],
                    cwd=str(self.project_root),
                    check=True,
                    capture_output=True,
                    text=True,
                )

            # 4. Inject AP Studio Core Source Engine
            info("Injecting AP Studio Reusable Auth Engine...")
            studio_source = Path(__file__).resolve().parents[3] / "source"
            target_source = self.project_root / "source"

            if target_source.exists():
                shutil.rmtree(target_source)
            shutil.copytree(studio_source, target_source)

            # 5. Configure settings.py
            self._configure_settings()

            # 6. Configure urls.py
            self._configure_urls()

            # 7. Run initial migrations
            self._run_migrations()

            # 8. Seed default roles
            self._seed_roles()

            success(f"Project '{self.project_name}' scaffolded and initialized successfully!")
            return True

        except subprocess.CalledProcessError as e:
            error(f"Command execution failed: {e.cmd}\n{e.stderr or e.stdout}")
            return False
        except Exception as e:
            error(f"Project generation failed: {str(e)}")
            return False

    def _configure_settings(self) -> None:
        """
        Inject auth module, middleware, and settings into Django settings.py.
        """
        info("Configuring project settings.py...")
        settings_file = self.inner_project / "settings.py"
        with open(settings_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Inject INSTALLED_APPS
        apps_to_inject = f"    'source.modules.auth',\n    '{self.app_name}',\n"
        content = re.sub(
            r"INSTALLED_APPS\s*=\s*\[",
            f"INSTALLED_APPS = [\n{apps_to_inject}",
            content,
        )

        # Inject AuthenticationMiddleware after SessionMiddleware
        middleware_to_inject = (
            "    'django.contrib.sessions.middleware.SessionMiddleware',\n"
            "    'source.modules.auth.middleware.authentication.AuthenticationMiddleware',"
        )
        content = re.sub(
            r"    'django\.contrib\.sessions\.middleware\.SessionMiddleware',",
            middleware_to_inject,
            content,
        )

        # Append AP Studio settings
        custom_block = """

# ==========================================================
# AP Studio Configuration Block
# ==========================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST_USER = "testing@apstudio.com"
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/auth/profile/"
"""
        content += custom_block

        with open(settings_file, "w", encoding="utf-8") as f:
            f.write(content)

    def _configure_urls(self) -> None:
        """
        Inject authentication routes and root redirect into urls.py.
        """
        info("Configuring project urls.py...")
        urls_file = self.inner_project / "urls.py"
        with open(urls_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Update imports
        content = content.replace(
            "from django.urls import path",
            "from django.urls import path, include\nfrom django.views.generic import RedirectView",
        )

        # Inject routes
        urls_injection = """
    path('auth/', include('source.modules.auth.urls')),
    path('', RedirectView.as_view(url='/auth/login/', permanent=False)),
"""
        content = re.sub(
            r"urlpatterns\s*=\s*\[",
            f"urlpatterns = [{urls_injection}",
            content,
        )

        with open(urls_file, "w", encoding="utf-8") as f:
            f.write(content)

    def _run_migrations(self) -> None:
        """
        Run database migrations for the new project.
        """
        info("Running database migrations...")
        subprocess.run(
            [self.python_exe, "manage.py", "migrate"],
            cwd=str(self.project_root),
            check=True,
            capture_output=True,
            text=True,
        )

    def _seed_roles(self) -> None:
        """
        Seed standard default roles (admin, user, manager).
        """
        info("Seeding default roles...")
        seed_script = f"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{self.project_name}.settings')
django.setup()

from source.modules.auth.models.role import Role

roles = ['admin', 'user', 'manager']
for r in roles:
    Role.objects.get_or_create(role_name=r, defaults={{'description': f'Default {{r}} role'}})
print("Default roles seeded.")
"""
        seed_path = self.project_root / "_seed.py"
        with open(seed_path, "w", encoding="utf-8") as f:
            f.write(seed_script)

        try:
            subprocess.run(
                [self.python_exe, "_seed.py"],
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True,
            )
        finally:
            if seed_path.exists():
                seed_path.unlink()
