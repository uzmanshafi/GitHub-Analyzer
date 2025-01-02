import requests
import base64
import datetime
from collections import Counter
import logging

GITHUB_API_URL = "https://api.github.com"

def fetch_github_user(username, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API_URL}/users/{username}"
    resp = requests.get(url, headers=headers)
    return resp.json() if resp.status_code == 200 else None

def fetch_repos(username, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API_URL}/users/{username}/repos"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []

def fetch_readme(owner, repo_name, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/contents/README.md"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        if "content" in data:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return None

def fetch_commits(owner, repo_name, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/commits"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []

def fetch_user_events(username, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API_URL}/users/{username}/events/public"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []

def is_deep_readme(readme_text):
    if not readme_text or len(readme_text) < 200:
        return False
    keywords = ["installation", "usage", "getting started", "example", "how to"]
    text_lower = readme_text.lower()
    return any(k in text_lower for k in keywords)

def analyze_commit_frequency(commits):
    from collections import Counter
    day_counts = Counter()
    for c in commits:
        commit_date_str = c["commit"]["committer"]["date"]  # e.g. "2023-04-12T14:20:30Z"
        commit_dt = datetime.datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
        day_str = commit_dt.strftime("%Y-%m-%d")
        day_counts[day_str] += 1

    if len(day_counts) == 1 and sum(day_counts.values()) > 10:
        return day_counts, True
    return day_counts, False

def detect_languages(repos):
    from collections import Counter
    lang_counter = Counter()
    has_ai = False
    has_crypto = False

    ai_keywords = {"tensorflow", "pytorch", "scikit-learn", "torch", "keras", "mxnet"}
    crypto_keywords = {"solidity", "rust", "web3", "web3.js", "ethers.js", "nft", "smart contract"}

    for r in repos:
        lang = r.get("language", None)
        if lang:
            lang_counter[lang] += 1

        desc = (r.get("description") or "").lower()
        if any(kw in desc for kw in ai_keywords):
            has_ai = True
        if any(kw in desc for kw in crypto_keywords):
            has_crypto = True

    if "Solidity" in lang_counter:
        has_crypto = True

    return lang_counter, has_ai, has_crypto

def check_requirements_files(repo, token=None):
    found_deps = set()
    possible_files = ["requirements.txt", "environment.yml", "Pipfile", "package.json"]

    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    for filename in possible_files:
        url = f"{repo['url']}/contents/{filename}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if "content" in data:
                content = base64.b64decode(data["content"]).decode("utf-8", errors="replace").lower()
                for ai_lib in ["tensorflow", "torch", "pytorch", "scikit-learn", "keras"]:
                    if ai_lib in content:
                        found_deps.add(ai_lib)
                for crypto_lib in ["web3", "ethers"]:
                    if crypto_lib in content:
                        found_deps.add(crypto_lib)

    return found_deps

def ascii_bar_chart(counter, title="Language Usage"):
    if not counter:
        return f"{title}\nNo data."

    total = sum(counter.values())
    max_len = max(len(k) for k in counter.keys())

    chart_lines = [f"{title}"]
    for lang, count in counter.most_common():
        bar_len = int((count / total) * 20)
        bars = "█" * bar_len
        chart_lines.append(f"{lang.rjust(max_len)}: {bars} ({count})")
    return "\n".join(chart_lines)

def analyze_pull_requests_and_issues(events):
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    pr_count = 0
    issues_count = 0

    for ev in events:
        created_at = datetime.datetime.fromisoformat(ev["created_at"].replace("Z", "+00:00"))
        if created_at < cutoff:
            continue
        ev_type = ev["type"]
        if ev_type == "PullRequestEvent":
            pr_count += 1
        elif ev_type == "IssuesEvent":
            issues_count += 1

    return pr_count, issues_count

def compute_profile_analysis(username, token=None):
    warnings = []
    user_data = fetch_github_user(username, token=token)
    if not user_data or user_data.get("message") == "Not Found":
        return {"error": "User not found"}

    repos = fetch_repos(username, token=token)

    readme_score = 0
    commit_score = 0
    readme_checks = []
    commit_patterns = []

    # We'll track how many points come from each category
    score_breakdown = {
        "account_age_points": 0,
        "readme_points": 0,
        "commit_points": 0,
        "pr_issues_points": 0,
        "profile_bio_blog_points": 0,
        "ai_crypto_points": 0,
    }

    for r in repos[:5]:
        readme = fetch_readme(r["owner"]["login"], r["name"], token=token)
        if is_deep_readme(readme):
            readme_score += 2
        else:
            warnings.append(f"Repo {r['name']}: shallow or missing README.")

        commits = fetch_commits(r["owner"]["login"], r["name"], token=token)
        day_counts, suspicious = analyze_commit_frequency(commits)
        if suspicious:
            warnings.append(f"Repo {r['name']}: suspicious commit pattern (all commits in 1 day).")
        commit_score += min(len(day_counts), 5)

        found_deps = check_requirements_files(r, token=token)
        if found_deps:
            readme_checks.append(f"{r['name']} dependencies: {', '.join(sorted(found_deps))}")

    events = fetch_user_events(username, token=token)
    pr_count, issues_count = analyze_pull_requests_and_issues(events)

    lang_counter, has_ai, has_crypto = detect_languages(repos)
    ascii_lang_chart = ascii_bar_chart(lang_counter, title="Language Usage")

    base_score = 0
    account_age_points = 0
    pr_issues_points = 0

    # profile age
    account_created_str = user_data.get("created_at")
    if account_created_str:
        created_dt = datetime.datetime.fromisoformat(account_created_str.replace("Z", "+00:00"))
        account_age_days = (datetime.datetime.now(datetime.timezone.utc) - created_dt).days
        if account_age_days > 365:
            account_age_points = 10
        else:
            account_age_points = (account_age_days / 365) * 10

    base_score += account_age_points
    score_breakdown["account_age_points"] = round(account_age_points, 2)

    # readme + commit
    base_score += readme_score
    base_score += commit_score
    score_breakdown["readme_points"] = readme_score
    score_breakdown["commit_points"] = commit_score

    # pr/issues
    pr_issues_points = (pr_count * 2) + issues_count
    base_score += pr_issues_points
    score_breakdown["pr_issues_points"] = pr_issues_points

    # profile bio/blog
    profile_bio_blog_points = 0
    if user_data.get("bio") or user_data.get("blog"):
        profile_bio_blog_points = 5
    base_score += profile_bio_blog_points
    score_breakdown["profile_bio_blog_points"] = profile_bio_blog_points

    # AI/Crypto
    ai_crypto_points = 0
    if has_ai:
        ai_crypto_points += 3
    if has_crypto:
        ai_crypto_points += 3
    base_score += ai_crypto_points
    score_breakdown["ai_crypto_points"] = ai_crypto_points

    # normalize
    final_score = min(base_score, 30) / 30 * 100

    # check user social links
    twitter_user = user_data.get("twitter_username", None)
    blog = user_data.get("blog", None)

    return {
        "user_data": user_data,
        "repo_data": repos,
        "readme_checks": readme_checks,
        "commit_patterns": commit_patterns,
        "pull_requests_30d": pr_count,
        "issues_30d": issues_count,
        "lang_counter": lang_counter,
        "has_ai": has_ai,
        "has_crypto": has_crypto,
        "score": round(final_score, 2),
        "warnings": warnings,
        "ascii_lang_chart": ascii_lang_chart,
        "score_breakdown": score_breakdown,
        "twitter_user": twitter_user,
        "blog": blog,
    }
