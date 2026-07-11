import os
import sys
import subprocess
import shutil
import re
from pathlib import Path


def print_success(text):
    print(f"\033[92m[SUCCESS]\033[0m {text}")

def print_info(text):
    print(f"\033[94m[INFO]\033[0m {text}")

def print_error(text):
    print(f"\033[91m[ERROR]\033[0m {text}")

def run_command(cmd, cwd=None):
    try:
        # Use shell=True for convenience, especially on Windows
        subprocess.run(cmd, check=True, shell=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        sys.exit(1)

def main():
    print_info("=========================================")
    print_info("  Welcome to AP Studio Automation Setup  ")
    print_info("=========================================")
    print()
    
    project_name = input("Enter Project Name (e.g., myproject): ").strip()
    if not project_name:
        print_error("Project Name cannot be empty.")
        sys.exit(1)
        
    app_name = input("Enter Main App Name (e.g., myapp): ").strip()
    if not app_name:
        print_error("App Name cannot be empty.")
        sys.exit(1)
        
    base_dir = Path.cwd()
    env_dir = base_dir / f"{project_name}_env"
    
    print_info(f"Creating Virtual Environment: {env_dir.name}...")
    run_command(f"python -m venv {env_dir.name}")
    
    # OS specific paths
    if os.name == 'nt':
        python_exe = env_dir / "Scripts" / "python.exe"
        django_admin = env_dir / "Scripts" / "django-admin.exe"
    else:
        python_exe = env_dir / "bin" / "python"
        django_admin = env_dir / "bin" / "django-admin"
        
    print_info("Installing Django and dependencies...")
    run_command(f'"{python_exe}" -m pip install django pillow')
    
    print_info(f"Creating Django Project: {project_name}...")
    run_command(f'"{django_admin}" startproject {project_name}', cwd=env_dir)
    
    project_root = env_dir / project_name
    inner_project = project_root / project_name
    
    print_info(f"Creating Django App: {app_name}...")
    run_command(f'"{python_exe}" manage.py startapp {app_name}', cwd=project_root)
    
    print_info("Injecting AP Studio Core Engine...")
    source_dir = base_dir / "source"
    target_source_dir = project_root / "source"
    if target_source_dir.exists():
        shutil.rmtree(target_source_dir)
    shutil.copytree(source_dir, target_source_dir)
    
    print_info("Configuring settings.py...")
    settings_file = inner_project / "settings.py"
    with open(settings_file, "r") as f:
        settings_content = f.read()
        
    # Inject INSTALLED_APPS
    apps_to_inject = f"    'source.modules.auth',\n    '{app_name}',\n"
    settings_content = re.sub(
        r"INSTALLED_APPS = \[",
        f"INSTALLED_APPS = [\n{apps_to_inject}",
        settings_content
    )
    
    # Inject MIDDLEWARE after SessionMiddleware
    middleware_to_inject = "    'django.contrib.sessions.middleware.SessionMiddleware',\n    'source.modules.auth.middleware.authentication.AuthenticationMiddleware',"
    settings_content = re.sub(
        r"    'django\.contrib\.sessions\.middleware\.SessionMiddleware',",
        middleware_to_inject,
        settings_content
    )
    
    # Append custom testing configurations
    custom_settings = """

# ==========================================================
# AP Studio Testing Configurations
# ==========================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST_USER = "testing@apstudio.com"
"""
    settings_content += custom_settings
    
    with open(settings_file, "w") as f:
        f.write(settings_content)
        
    print_info("Configuring urls.py...")
    urls_file = inner_project / "urls.py"
    with open(urls_file, "r") as f:
        urls_content = f.read()
        
    urls_content = urls_content.replace(
        "from django.urls import path", 
        "from django.urls import path, include\nfrom django.views.generic import RedirectView"
    )
    
    # Inject auth routes and root redirect
    urls_injection = """
    path('auth/', include('source.modules.auth.urls')),
    path('', RedirectView.as_view(url='/auth/login/', permanent=False)),
"""
    urls_content = re.sub(
        r"urlpatterns = \[",
        f"urlpatterns = [{urls_injection}",
        urls_content
    )
    
    with open(urls_file, "w") as f:
        f.write(urls_content)
        
    print_info("Running Database Migrations...")
    run_command(f'"{python_exe}" manage.py makemigrations', cwd=project_root)
    run_command(f'"{python_exe}" manage.py migrate', cwd=project_root)
    
    print_success("Project Ready! Authentication Pre-Installed.")
    print(f"\nTo start your server:")
    if os.name == 'nt':
        print(f"  cd {env_dir.name}\\{project_name}")
        print(f"  ..\\Scripts\\activate")
    else:
        print(f"  cd {env_dir.name}/{project_name}")
        print(f"  source ../bin/activate")
    print(f"  python manage.py runserver\n")


if __name__ == "__main__":
    main()
