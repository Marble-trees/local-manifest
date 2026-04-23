import xml.etree.ElementTree as ET
import subprocess
import sys

def verify_repositories(manifest_file):
    try:
        tree = ET.parse(manifest_file)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: {manifest_file} not found.")
        return
    except ET.ParseError:
        print(f"Error: Failed to parse {manifest_file}. Ensure it is valid XML.")
        return

    # Extract remotes
    remotes = {}
    for remote in root.findall('remote'):
        name = remote.get('name')
        fetch = remote.get('fetch')
        if name and fetch:
            remotes[name] = fetch.rstrip('/')

    projects = root.findall('project')
    total = len(projects)
    success_count = 0
    failures = []

    print(f"Verifying {total} repositories listed in {manifest_file}...\n")

    for i, project in enumerate(projects, 1):
        path = project.get('path')
        name = project.get('name')
        remote_name = project.get('remote')
        
        if not remote_name in remotes:
            print(f"[{i}/{total}] SKIP: {path} (Unknown remote: {remote_name})")
            failures.append(f"{path}: Unknown remote {remote_name}")
            continue

        base_url = remotes[remote_name]
        # Construct URL. Google's repo tool handles this by appending name to fetch.
        # Most of the time it's fetch + / + name.
        url = f"{base_url}/{name}"
        if not url.endswith(".git") and "github" in url:
             # git ls-remote works fine without .git on github, but some others might need it.
             pass

        print(f"[{i}/{total}] Checking {name}...", end="\r")
        
        # Use git ls-remote to check existence without cloning
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--heads", url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"[{i}/{total}] OK: {name}")
                success_count += 1
            else:
                print(f"[{i}/{total}] FAIL: {name}")
                error_msg = result.stderr.split('\n')[0] if result.stderr else "Access denied or not found"
                failures.append(f"{name} ({url}): {error_msg}")
        except subprocess.TimeoutExpired:
            print(f"[{i}/{total}] TIMEOUT: {name}")
            failures.append(f"{name}: Timeout")
        except Exception as e:
            print(f"[{i}/{total}] ERROR: {name}")
            failures.append(f"{name}: {str(e)}")

    print(f"\nVerification Complete!")
    print(f"Passed: {success_count}/{total}")
    
    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print("\nAll repositories are valid and accessible.")
        sys.exit(0)

if __name__ == "__main__":
    verify_repositories('aio.xml')
