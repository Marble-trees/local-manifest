import xml.etree.ElementTree as ET
import subprocess
import re
import sys

def get_default_branch(url):
    """Fetches the default branch (HEAD) of a remote repository."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--symref", url, "HEAD"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("ref:") and "HEAD" in line:
                    # e.g., "ref: refs/heads/vic	HEAD"
                    return line.split()[1].replace("refs/heads/", "")
        return None
    except Exception:
        return None

def set_explicit_revisions(manifest_file):
    try:
        with open(manifest_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {manifest_file} not found.")
        return

    # Use ET just to easily get remotes and project info
    try:
        tree = ET.parse(manifest_file)
        root = tree.getroot()
    except ET.ParseError:
        print(f"Error: Failed to parse {manifest_file}. Ensure it is valid XML.")
        return

    remotes = {r.get('name'): r.get('fetch').rstrip('/') for r in root.findall('remote')}
    
    # We will search for project tags and update them manually to preserve comments
    # Regex to find project tags (handles multi-line tags)
    project_pattern = re.compile(r'(<project\s+.*?(?:/>|/project>))', re.DOTALL)
    
    def update_project_tag(match):
        tag_content = match.group(1)
        
        # Parse this specific tag to get attributes
        try:
            temp_root = ET.fromstring(tag_content)
        except:
            return tag_content # Skip if it can't be parsed

        name = temp_root.get('name')
        remote_name = temp_root.get('remote')
        current_revision = temp_root.get('revision')
        
        if not name or not remote_name or remote_name not in remotes:
            return tag_content

        url = f"{remotes[remote_name]}/{name}"
        print(f"Checking {name}...", end="\r", flush=True)
        branch = get_default_branch(url)
        
        if branch:
            if current_revision == branch:
                print(f"Checking {name}... Already set to: {branch}")
                return tag_content
            
            if current_revision:
                print(f"Checking {name}... Overwriting {current_revision} -> {branch}")
                # Replace existing revision value while trying to preserve quotes
                return re.sub(r'revision=["\'].*?["\']', f'revision="{branch}"', tag_content)
            else:
                print(f"Checking {name}... Found: {branch}")
                # Detect indentation of the last attribute
                indent = "        " # Default to 8 spaces
                indent_match = re.search(r'\n(\s+)\w+=', tag_content)
                if indent_match:
                    indent = indent_match.group(1)

                # Insert revision before the closing /> or >
                if tag_content.endswith('/>'):
                    new_tag = tag_content[:-2].rstrip() + f'\n{indent}revision="{branch}" />'
                else:
                    new_tag = tag_content.replace('>', f' revision="{branch}">', 1)
                return new_tag
        else:
            print(f"Checking {name}... Failed to find default branch.")
            return tag_content

    print(f"Fetching default branches for projects in {manifest_file}...")
    new_content = project_pattern.sub(update_project_tag, content)
    
    if new_content != content:
        with open(manifest_file, 'w') as f:
            f.write(new_content)
        print(f"\nSuccessfully updated {manifest_file} with explicit revisions.")
    else:
        print("\nNo revisions were updated.")

if __name__ == "__main__":
    set_explicit_revisions('aio.xml')
