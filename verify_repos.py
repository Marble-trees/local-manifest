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

    # Extract default revision
    default_revision = None
    default_tag = root.find('default')
    if default_tag is not None:
        default_revision = default_tag.get('revision')

    projects = root.findall('project')
    total = len(projects)
    success_count = 0
    failures = []

    print(f"Verifying {total} repositories listed in {manifest_file}...\n")

    for i, project in enumerate(projects, 1):
        path = project.get('path')
        name = project.get('name')
        remote_name = project.get('remote')
        revision = project.get('revision') or default_revision
        
        if not remote_name in remotes:
            print(f"[{i}/{total}] SKIP: {path} (Unknown remote: {remote_name})")
            failures.append(f"{path}: Unknown remote {remote_name}")
            continue

        base_url = remotes[remote_name]
        url = f"{base_url}/{name}"

        print(f"[{i}/{total}] Checking {name}...", end="\r", flush=True)
        
        # Use git ls-remote to check existence and revisions
        try:
            cmd = ["git", "ls-remote", url]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clear line for the result
            print(" " * 80, end="\r")

            if result.returncode == 0:
                if revision:
                    # Check if revision exists as head or tag
                    found = False
                    for line in result.stdout.splitlines():
                        ref = line.split('\t')[1]
                        if ref == f"refs/heads/{revision}" or ref == f"refs/tags/{revision}" or ref == revision:
                            found = True
                            break
                    
                    if found:
                        print(f"[{i}/{total}] OK: {name} (branch: {revision})")
                        success_count += 1
                    else:
                        print(f"[{i}/{total}] FAIL: {name} (Revision '{revision}' not found)")
                        failures.append(f"{name} ({url}): Revision '{revision}' not found")
                else:
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
