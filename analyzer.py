import requests
import datetime
import base64
import random

GITHUB_API_URL = "https://api.github.com"

def fetch_github_user(username, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API_URL}/users/{username}"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def fetch_user_repos(username, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API_URL}/users/{username}/repos"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def days_since_creation(created_at_str):
    created_at = datetime.datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
    delta = datetime.datetime.utcnow() - created_at
    return delta.days

def fetch_readme(owner, repo, token=None):
    """
    Tries to fetch README.md content from a repo.
    Returns decoded string if found, else None.
    """
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/README.md"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content_json = response.json()
        if content_json.get("content"):
            # README content is base64-encoded
            readme_content = base64.b64decode(content_json["content"]).decode("utf-8", errors="replace")
            return readme_content
    return None

def fetch_commits(owner, repo, token=None):
    """
    Fetch commits from a repo (first page).
    Returns a list of commit messages or empty if error/no commits.
    """
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    # We'll fetch the first page with up to 30 commits
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commits = response.json()
        messages = [c["commit"]["message"] for c in commits]
        return messages
    return []

def analyze_readme_content(readme):
    """
    Basic analysis of README text.
    Returns True if it looks 'meaningful', False if suspicious or empty.
    This is just a demonstration. Real checks might be more elaborate.
    """
    if not readme:
        return False
    # For example, if it's very short or default text
    if len(readme) < 100:
        return False
    return True

def analyze_commit_messages(commit_messages):
    """
    Quick heuristic to see if commit messages are repeated or too generic.
    Returns a suspicious flag (True/False) and some note.
    """
    if not commit_messages:
        return True, "No commits found."
    
    # Sample a few random commits
    sample_size = min(5, len(commit_messages))  # up to 5
    sample_msgs = random.sample(commit_messages, sample_size)

    suspicious_count = 0
    for msg in sample_msgs:
        msg_lower = msg.strip().lower()
        if msg_lower in ["update readme", "fix #123", "test commit"]:
            suspicious_count += 1
        # add more patterns or heuristics here

    if suspicious_count >= (sample_size / 2):
        return True, f"{suspicious_count} out of {sample_size} commits look auto-generated or generic."
    return False, None

def analyze_repo_details(repo, token=None):
    """
    Fetches readme and commits, returns partial score plus warnings if suspicious.
    """
    warnings = []

    owner = repo["owner"]["login"]
    repo_name = repo["name"]

    readme_content = fetch_readme(owner, repo_name, token=token)
    readme_ok = analyze_readme_content(readme_content)
    if not readme_ok:
        warnings.append("README seems too short or missing.")

    commit_msgs = fetch_commits(owner, repo_name, token=token)
    suspicious_commits, note = analyze_commit_messages(commit_msgs)
    if suspicious_commits:
        warnings.append(f"Commit messages suspicious: {note}" if note else "Commit messages suspicious.")

    # Check library usage (e.g., check if there's a main language)
    language = repo.get("language", None)
    library_note = None
    if not language or language in ["HTML", "CSS", "Unknown"]:
        # Just a naive check
        library_note = "No major coding language detected."
    # You could also fetch `package.json` or `requirements.txt` if needed

    if library_note:
        warnings.append(library_note)

    return warnings

def compute_github_score(user_data, repos_data, token=None):
    """
    Compute a 'score' + warnings based on various heuristics,
    returning a dict with sub-scores, final score, and a list of warnings.
    """

    sub_scores = {
        "account_age_score": 0,
        "profile_completeness_score": 0,
        "repo_activity_score": 0,
        "community_interaction_score": 0,
        "external_consistency_score": 0,
        "readme_commit_score": 0,  # new category for readme/commit checks
    }

    max_scores = {
        "account_age": 15,
        "profile_completeness": 20,
        "repo_activity": 25,
        "community_interaction": 25,
        "external_consistency": 15,
        "readme_commit": 20,  # let's allocate 20 points for these new checks
    }

    overall_warnings = []

    # --- 1) Account Age ---
    age_in_days = days_since_creation(user_data["created_at"])
    if age_in_days > 365:
        sub_scores["account_age_score"] = max_scores["account_age"]
    else:
        sub_scores["account_age_score"] = (age_in_days / 365) * max_scores["account_age"]

    # --- 2) Profile Completeness ---
    completeness_points = 0
    if user_data.get("avatar_url"):
        completeness_points += 5
    if user_data.get("bio"):
        completeness_points += 5
    if user_data.get("blog"):
        completeness_points += 5
    # Add more checks as needed (e.g., email, location)
    completeness_points = min(completeness_points, max_scores["profile_completeness"])
    sub_scores["profile_completeness_score"] = completeness_points

    # --- 3) Repository Activity ---
    repo_count = len(repos_data)
    if repo_count >= 20:
        sub_scores["repo_activity_score"] = max_scores["repo_activity"]
    else:
        sub_scores["repo_activity_score"] = (repo_count / 20) * max_scores["repo_activity"]

    # --- 4) Community Interaction ---
    interaction_points = 0
    for repo in repos_data:
        if repo.get("forks_count", 0) > 0:
            interaction_points += 1
        if repo.get("stargazers_count", 0) > 0:
            interaction_points += 1
    interaction_points = min(interaction_points, max_scores["community_interaction"])
    sub_scores["community_interaction_score"] = interaction_points

    # --- 5) External Consistency ---
    external_points = 0
    if user_data.get("blog") or user_data.get("twitter_username"):
        external_points += 10
    sub_scores["external_consistency_score"] = min(external_points, max_scores["external_consistency"])

    # --- 6) Readme/Commit Analysis (new) ---
    # We'll do a quick pass over the user's repos, awarding points if readmes look good & commits are not suspicious.
    # This is simplified: you might want a more thorough approach.
    readme_commit_score = 0
    for repo in repos_data[:5]:  # Limit to first 5 to avoid time-consuming checks
        warnings = analyze_repo_details(repo, token=token)
        if not warnings:
            # If no warnings, award some points
            readme_commit_score += 4
        else:
            overall_warnings.extend([f"{repo['name']}: {w}" for w in warnings])

    # Cap the readme_commit_score
    readme_commit_score = min(readme_commit_score, max_scores["readme_commit"])
    sub_scores["readme_commit_score"] = readme_commit_score

    # --- Summation & Final Score ---
    total_earned_points = sum(sub_scores.values())
    total_max_points = sum(max_scores.values())

    normalized_score = (total_earned_points / total_max_points) * 100

    return {
        "sub_scores": sub_scores,
        "max_scores": max_scores,
        "normalized_score": round(normalized_score, 2),
        "warnings": overall_warnings
    }
