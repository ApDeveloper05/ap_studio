"""
------------------------------------------------------------
File: test_scaffolder.py

Module: AP Studio Scaffolder & Wireframe Test Suite

Purpose:
Validate end-to-end project generation via ProjectGenerator:
- Generates a full Django project
- Verifies auth module injection
- Verifies settings.py and urls.py wiring
- Verifies database migrations and seeded roles

Author:
Aryan Parmar

Project:
AP Studio
------------------------------------------------------------
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from source.core.generator.project_generator import ProjectGenerator


class ProjectScaffolderEndToEndTests(unittest.TestCase):
    """
    End-to-End Test for AP Studio Scaffolding Engine.
    """

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="aps_test_scaffold_"))
        self.project_name = "test_scaffolded_app"
        self.app_name = "domain_app"

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_scaffolding(self):
        print("\n[SCAFFOLDER TEST] Running End-to-End Scaffolding Engine...")
        generator = ProjectGenerator(
            project_name=self.project_name,
            app_name=self.app_name,
            target_dir=self.temp_dir,
            python_executable=sys.executable,
        )

        success = generator.create()
        self.assertTrue(success, "ProjectGenerator.create() returned False!")

        scaffolded_root = self.temp_dir / self.project_name
        self.assertTrue(scaffolded_root.exists(), "Scaffolded root directory was not created!")

        # 1. Check manage.py
        manage_py = scaffolded_root / "manage.py"
        self.assertTrue(manage_py.exists(), "manage.py is missing!")
        print("  ✓ manage.py generated.")

        # 2. Check injected source directory
        source_dir = scaffolded_root / "source"
        auth_module = source_dir / "modules" / "auth"
        self.assertTrue(auth_module.exists(), "source.modules.auth was not injected!")
        print("  ✓ Reusable Auth Engine injected into project.")

        # 3. Check settings.py configuration
        settings_file = scaffolded_root / self.project_name / "settings.py"
        self.assertTrue(settings_file.exists(), "settings.py is missing!")
        with open(settings_file, "r", encoding="utf-8") as f:
            settings_text = f.read()

        self.assertIn("source.modules.auth", settings_text)
        self.assertIn("source.modules.auth.middleware.authentication.AuthenticationMiddleware", settings_text)
        self.assertIn(self.app_name, settings_text)
        print("  ✓ settings.py correctly configured with auth module & middleware.")

        # 4. Check urls.py configuration
        urls_file = scaffolded_root / self.project_name / "urls.py"
        self.assertTrue(urls_file.exists(), "urls.py is missing!")
        with open(urls_file, "r", encoding="utf-8") as f:
            urls_text = f.read()

        self.assertIn("source.modules.auth.urls", urls_text)
        self.assertIn("/auth/login/", urls_text)
        print("  ✓ urls.py correctly configured with auth routing & redirect.")

        # 5. Check database & migrations
        db_file = scaffolded_root / "db.sqlite3"
        self.assertTrue(db_file.exists(), "db.sqlite3 was not created by migrations!")
        print("  ✓ Database initialized and migrated.")

        # 6. Verify seeded roles in the generated project database
        verify_cmd = [
            sys.executable,
            "-c",
            f"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{self.project_name}.settings')
django.setup()
from source.modules.auth.models.role import Role
assert Role.objects.filter(role_name='admin').exists()
assert Role.objects.filter(role_name='user').exists()
assert Role.objects.filter(role_name='manager').exists()
print('All default roles successfully verified in generated database.')
""",
        ]
        result = subprocess.run(
            verify_cmd,
            cwd=str(scaffolded_root),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("All default roles successfully verified", result.stdout)
        print("  ✓ Default roles verified in generated project database.")
        print("\n🎉 SCAFFOLDER END-TO-END TEST PASSED 100%!")


if __name__ == "__main__":
    unittest.main()
