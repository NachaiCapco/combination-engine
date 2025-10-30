import os, requests

def trigger_workflow(test_name: str) -> tuple[bool, str]:
    repo = os.getenv("GITHUB_REPOSITORY", "owner/TestForge")
    token = os.getenv("GITHUB_TOKEN", "")
    api_url = f"https://api.github.com/repos/{repo}/actions/workflows/run-test.yml/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    body = {"ref": "main", "inputs": {"testName": test_name}}
    resp = requests.post(api_url, headers=headers, json=body, timeout=30)
    if resp.status_code == 204:
        return True, f"Workflow triggered for {test_name}"
    else:
        return False, f"Failed ({resp.status_code}): {resp.text}"
