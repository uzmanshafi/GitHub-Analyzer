import requests
import datetime

GITHUB_API_URL = "https://api.github.com"

def fetch_github_user(username, token=None):
    """
    Fetch basic user profile from GitHub API.
    """
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API_URL}/users/{username}"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def fetch_user_repos(username, token=None):
    """
    Fetch public repositories for the user.
    """
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API_URL}/users/{username}/repos"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def days_since_creation(created_at_str):
    """
    Calculate how many days have passed since the GitHub account was created.
    """
    created_at = datetime.datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
    delta = datetime.datetime.utcnow() - created_at
    return delta.days

def compute_github_score(user_data, repos_data):
    """
    Compute a 'score' based on various heuristics.
    """

    # Initialize total score
    total_score = 0

    # 1. Account Age
    #    - if account is more than a year old, award max points (say 15)
    #    - otherwise, partial points
    max_age_points = 15
    age_in_days = days_since_creation(user_data["created_at"])
    if age_in_days > 365:
        total_score += max_age_points
    else:
        # proportionally assign points
        total_score += (age_in_days / 365) * max_age_points

    # 2. Profile Completeness (avatar, bio, blog, etc.)
    max_profile_points = 20
    completeness_points = 0
    if user_data.get("avatar_url"):
        completeness_points += 5
    if user_data.get("bio"):
        completeness_points += 5
    if user_data.get("blog"):  # or user_data.get("html_url")
        completeness_points += 5
    # You can add more checks if needed
    # Cap it at max_profile_points
    completeness_points = min(completeness_points, max_profile_points)
    total_score += completeness_points

    # 3. Repository Activity & Commit Frequency
    #    For simplicity, we look at number of repos and assume more repos = more active
    max_repo_activity_points = 25
    repo_count = len(repos_data)
    # A naive approach: 0 repos = 0 points, 20+ repos = max points
    if repo_count >= 20:
        total_score += max_repo_activity_points
    else:
        total_score += (repo_count / 20) * max_repo_activity_points

    # 4. Community Interaction (forks, watchers, open-source contributions)
    #    We'll sample data from the user's repos
    max_interaction_points = 25
    interaction_points = 0
    for repo in repos_data:
        # Some simplistic checks
        if repo.get("forks_count", 0) > 0:
            interaction_points += 1
        if repo.get("stargazers_count", 0) > 0:
            interaction_points += 1
    # Cap interactions to max_interaction_points
    interaction_points = min(interaction_points, max_interaction_points)
    total_score += interaction_points

    # 5. External Consistency (just an example check)
    max_external_points = 15
    external_points = 0
    if user_data.get("blog") or user_data.get("twitter_username"):
        # If the user links a blog or a Twitter, assume some external presence
        external_points += 10
    total_score += min(external_points, max_external_points)

    # The final score could be out of 100 (or more if you want).
    # If you want to normalize it to 100 explicitly:
    max_score = max_age_points + max_profile_points + max_repo_activity_points + max_interaction_points + max_external_points
    normalized_score = (total_score / max_score) * 100

    return round(normalized_score, 2)
