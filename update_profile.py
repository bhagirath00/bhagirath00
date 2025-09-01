import os
import sys
import datetime
import requests
from dateutil import relativedelta

# Configuration - Customize these values!
USER_NAME = "Bhagirath00"
BIRTH_DATE = datetime.datetime(2004, 9, 6) # September 6, 2004
HOST_NAME = "https://gitme.xyz"

# SVGs Output Path
DARK_SVG_PATH = "dark_mode.svg"
LIGHT_SVG_PATH = "light_mode.svg"

# Base colors for the terminal themes (dark bg is transparent to adapt to GitHub dark/dimmed/black; light bg is solid light gray)
THEMES = {
    "dark": {
        "bg": "none",
        "ascii": "#c9d1d9",
        "key": "#ffa657",
        "value": "#a5d6ff",
        "dots": "#485260",
        "add": "#3fb950",
        "del": "#f85149",
        "border": "#30363d",
        "text": "#c9d1d9"
    },
    "light": {
        "bg": "#f6f8fa",
        "ascii": "#24292f",
        "key": "#953800",
        "value": "#0550ae",
        "dots": "#afb8c1",
        "add": "#118020",
        "del": "#d1242f",
        "border": "#d0d7de",
        "text": "#24292f"
    }
}



def escape_xml(text):
    """Escapes special XML/SVG characters to prevent parser errors."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

def get_github_stats():
    """Fetches real stats from GitHub API. Works anonymously or authenticated."""
    token = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    
    # Baseline stats defaults matching user's current counts
    stats = {
        "repos": 81,
        "private_repos": 47,
        "stars": 17,
        "commits": 4304,
        "followers": 18,
        "loc": 2007162,
        "loc_add": 2508952,
        "loc_del": 501790
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    if token:
        print(f"[+] Token found! Querying GitHub API with authorization...")
        headers["Authorization"] = f"token {token}"
        user_url = "https://api.github.com/user" # Endpoint for authenticated user details
    else:
        print(f"[!] No GITHUB_TOKEN environment variable found. Querying publicly...")
        user_url = f"https://api.github.com/users/{USER_NAME}"
        
    try:
        # 1. Fetch user profile info (repos count, followers count)
        res = requests.get(user_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            stats["followers"] = data.get("followers", stats["followers"])
            public_repos = data.get("public_repos", 34)
            
            # Fetch private repos if authenticated, otherwise use baseline of 47
            if "total_private_repos" in data:
                stats["private_repos"] = data.get("total_private_repos", 47)
            else:
                stats["private_repos"] = 47
                
            stats["repos"] = public_repos + stats["private_repos"]
            print(f" -> Repos: {stats['repos']} ({stats['private_repos']} private)")
            print(f" -> Followers: {stats['followers']}")
        elif res.status_code == 403:
            print("[!] API Rate limit exceeded on profile fetch. Using generic placeholders.")
            return stats
            
        # 2. Fetch repos to calculate stars and estimate Lines of Code
        repos_url = f"https://api.github.com/users/{USER_NAME}/repos?per_page=100"
        res = requests.get(repos_url, headers=headers, timeout=10)
        if res.status_code == 200:
            repos_data = res.json()
            
            # Sum stargazers across all repositories
            total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
            stats["stars"] = total_stars
            print(f" -> Stars: {stats['stars']}")
            
            # Realistic LOC estimation based on repository size (in KB)
            total_size_kb = sum(repo.get("size", 0) for repo in repos_data)
            stats["loc"] = int(total_size_kb * 1.5)
            stats["loc_add"] = int(stats["loc"] * 1.25)
            stats["loc_del"] = int(stats["loc"] * 0.25)
            print(f" -> Estimated LOC: {stats['loc']:,}")
            
        # 3. Fetch total commit count from GitHub search API
        commits_url = f"https://api.github.com/search/commits?q=author:{USER_NAME}"
        search_headers = headers.copy()
        search_headers["Accept"] = "application/vnd.github.cloak-preview+json"
        res = requests.get(commits_url, headers=search_headers, timeout=10)
        if res.status_code == 200:
            api_commits = res.json().get("total_count", 0)
            # Ensure we display at least the contribution baseline of 4304
            stats["commits"] = max(4304, api_commits)
            print(f" -> Public Commits: {stats['commits']}")
            
    except Exception as e:
        print(f"[!] Error fetching live data: {e}. Falling back to default values.")
        
    return stats

def load_and_trim_ascii():
    """Reads ascii-art.txt, crops empty margins, and strips uniform indentation."""
    ascii_path = "ascii-art.txt"
    lines = []
    
    if os.path.exists(ascii_path):
        with open(ascii_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        # Fallback to fetching remote ASCII art from GitHub Secrets URL or direct backup link
        url = os.environ.get("ASCII_ART_URL") or "https://github.com/user-attachments/files/29977028/ascii-art.txt"
        if url:

            try:
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    lines = res.text.splitlines()
                else:
                    print(f"[!] Warning: Remote URL returned status code {res.status_code}")
            except Exception as e:
                print(f"[!] Error fetching remote ASCII art: {e}")
                
    if not lines:
        return ["  _____   ", " /  _  \\  ", "|  / \\  | ", "|  \\_/  | ", " \\_____/  "]
        
    # Crucial: strip trailing whitespace/spaces from the right side of the art
    lines = [line.rstrip() for line in lines]

    
    # Find active range (first non-empty to last non-empty line)
    first_idx = 0
    last_idx = len(lines) - 1
    for i, line in enumerate(lines):
        if line.strip():
            first_idx = i
            break
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            last_idx = i
            break
            
    active_lines = lines[first_idx:last_idx + 1]
    if not active_lines:
        return ["(Empty ASCII Art)"]
        
    active_lines = active_lines[:49]
        
    # Find minimum leading indentation spaces across the remaining head/neck lines
    min_spaces = sys.maxsize
    for line in active_lines:
        if line.strip():
            stripped = line.lstrip()
            spaces = len(line) - len(stripped)
            if spaces < min_spaces:
                min_spaces = spaces
                
    # Remove the uniform leading indentation (will remove 32 spaces, aligning the face to the far left)
    trimmed_lines = []
    for line in active_lines:
        if len(line) >= min_spaces:
            trimmed_lines.append(line[min_spaces:])
        else:
            trimmed_lines.append("")
            
    return trimmed_lines

def generate_svg(theme_name, stats, ascii_art):
    """Generates the Neofetch terminal SVG file with right alignment justification."""
    theme = THEMES[theme_name]
    
    # Calculate age/uptime dynamically based on birthday September 6, 2004
    diff = relativedelta.relativedelta(datetime.datetime.today(), BIRTH_DATE)
    uptime = f"{diff.years} years, {diff.months} months, {diff.days} days"
    os_version = f"Human OS v{diff.years}.{diff.months} (Surviving)"
    
    # Header format: hostname followed directly by dashes on the same line
    user_header = f"{USER_NAME.lower()} " + ("-" * 50)
    
    # SVG Dimensions
    svg_width = 925
    svg_height = 530
    
    # Horizontal line separator
    separator_width = 63
    separator = "-" * separator_width
    
    # ASCII Art positions - Restored size to be nice and big (font-size=9.0px)
    ascii_font_size = 9.0
    ascii_line_height = 10.0
    ascii_y_start = 30
    
    # Right column positions - Andrew's exact starting x coordinate
    right_x = 390
    right_font_size = 14
    right_line_height = 19.5
    right_y_start = 30
    
    # Sarcastic Neofetch technical profile fields
    right_lines = [
        ("OS", os_version),
        ("Kernel", "Works on My Machine™"),
        ("Uptime", uptime),
        ("RAM", "2 Tabs Free"),
        ("Daemon", "Spotify"),
        ("SEPARATOR", ""),
        ("Programming", "Java, C++, Python, JavaScript, SQL"),
        ("Tech Stack", "React.js, Node.js, PostgreSQL, MongoDB"),
        ("DevOps", "Docker, Kubernetes, Terraform, AWS, GCP"),
        ("SEPARATOR", ""),
        ("Favorite Command", "git push origin main"),

        ("Compiler", '"Please Work"'),
        ("Firewall", '"It Worked Yesterday"'),
        ("Permissions", "sudo everything"),
        ("Latency", "Depends on College Wi-Fi"),
        ("SEPARATOR_CONTACT", ""),
        ("mail", "patelbhagirath736@gmail.com"),
        ("link", HOST_NAME),
        ("linkedin", "bhagirath00"),
        ("SEPARATOR_STATS", ""),
    ]
    
    svg_content = []
    svg_content.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    svg_content.append(f'<svg xmlns="http://www.w3.org/2000/svg" font-family="Consolas, Monaco, &apos;Courier New&apos;, monospace" width="{svg_width}px" height="{svg_height}px" font-size="{right_font_size}px">')
    svg_content.append(f'<style>')
    svg_content.append(f'  .bg {{ fill: {theme["bg"]}; rx: 15; stroke: {theme["border"]}; stroke-width: 1.5; }}')

    svg_content.append(f'  .ascii {{ font-size: {ascii_font_size}px; fill: {theme["ascii"]}; white-space: pre; }}')
    svg_content.append(f'  .key {{ fill: {theme["key"]}; }}')
    svg_content.append(f'  .value {{ fill: {theme["value"]}; }}')
    svg_content.append(f'  .dots {{ fill: {theme["dots"]}; }}')
    svg_content.append(f'  .text {{ fill: {theme["text"]}; }}')
    svg_content.append(f'  .add {{ fill: {theme["add"]}; }}')
    svg_content.append(f'  .del {{ fill: {theme["del"]}; }}')
    svg_content.append(f'</style>')
    
    # Outer terminal box
    svg_content.append(f'<rect width="{svg_width}px" height="{svg_height}px" class="bg"/>')
    
    # Left Side: Render ASCII Art
    svg_content.append(f'<text x="35" y="{ascii_y_start}" class="ascii">')
    for i, line in enumerate(ascii_art):
        y_pos = ascii_y_start + (i * ascii_line_height)
        escaped_line = escape_xml(line)
        svg_content.append(f'  <tspan x="35" y="{y_pos:.1f}">{escaped_line}</tspan>')

    svg_content.append(f'</text>')
    
    # Right Side: Render Info Panel
    svg_content.append(f'<text x="{right_x}" y="{right_y_start}" class="text">')
    y = right_y_start
    # Total characters to align values neatly to the end
    total_align_length = 65
    
    # Header user and separator line combined (dynamically padded with dashes to match total_align_length)
    header_dashes = "-" * (total_align_length - len(USER_NAME) - 1)
    user_header = f"{USER_NAME.lower()} {header_dashes}"
    svg_content.append(f'  <tspan x="{right_x}" y="{y}">{escape_xml(user_header)}</tspan>')
    y += right_line_height

    
    for key, val in right_lines:
        if key == "SEPARATOR":
            y += right_line_height
            continue
        elif key == "SEPARATOR_CONTACT":
            y += right_line_height / 2
            # Calculate dashes matching total line width
            contact_dashes = "-" * (total_align_length - 10)
            svg_content.append(f'  <tspan x="{right_x}" y="{y}">- Contact {escape_xml(contact_dashes)}</tspan>')
            y += right_line_height
            continue
        elif key == "SEPARATOR_STATS":
            y += right_line_height / 2
            stats_dashes = "-" * (total_align_length - 15)
            svg_content.append(f'  <tspan x="{right_x}" y="{y}">- GitHub Stats {escape_xml(stats_dashes)}</tspan>')
            y += right_line_height
            continue
            
        # Dynamically justify key and value so dots fill up the space in between
        prefix = ". "
        middle_pad = total_align_length - len(key) - len(val) - len(prefix)
        middle_pad = max(1, middle_pad)
        dots_str = "." * middle_pad
        
        svg_content.append(
            f'  <tspan x="{right_x}" y="{y}">{escape_xml(prefix)}<tspan class="key">{escape_xml(key)}</tspan>'
            f'<tspan class="dots">{escape_xml(dots_str)}</tspan><tspan class="value"> {escape_xml(val)}</tspan></tspan>'
        )
        y += right_line_height
        
    # Render final GitHub stats block
    # Repos
    private_repos = stats.get("private_repos", 47)
    repos_str = f"{stats['repos']}"
    private_str = f"({private_repos} private)"
    stars_val = f"{stats['stars']}"
    
    right_val_repos = f"{repos_str} {private_str} | Stars: {stars_val}"
    repos_pad = total_align_length - 5 - len(right_val_repos) - 2
    repos_dots = "." * max(1, repos_pad)
    
    svg_content.append(
        f'  <tspan x="{right_x}" y="{y}">. <tspan class="key">repos</tspan><tspan class="dots">{escape_xml(repos_dots)}</tspan> '
        f'<tspan class="value">{escape_xml(repos_str)}</tspan> <tspan class="key">{escape_xml(private_str)}</tspan> | '
        f'<tspan class="key">stars</tspan>:<tspan class="value"> {escape_xml(stars_val)}</tspan></tspan>'
    )
    y += right_line_height
    
    # Commits
    commits_str = f"{stats['commits']:,}"
    followers_str = f"{stats['followers']}"
    right_val_commits = f"{commits_str} | followers: {followers_str}"
    commits_pad = total_align_length - 8 - len(right_val_commits) - 2
    commits_dots = "." * max(1, commits_pad)
    
    svg_content.append(
        f'  <tspan x="{right_x}" y="{y}">. <tspan class="key">commits</tspan><tspan class="dots">{escape_xml(commits_dots)}</tspan> '
        f'<tspan class="value">{escape_xml(commits_str)}</tspan> | '
        f'<tspan class="key">followers</tspan>:<tspan class="value"> {escape_xml(followers_str)}</tspan></tspan>'
    )
    y += right_line_height
    
    # Lines of code on GitHub
    loc_val = f"{stats['loc']:,}"
    add_val = f"{stats['loc_add']:,}++"
    del_val = f"{stats['loc_del']:,}--"
    right_val_loc = f"{loc_val} ( {add_val}, {del_val} )"
    loc_pad = total_align_length - 23 - len(right_val_loc) - 2
    loc_dots = "." * max(1, loc_pad)
    
    svg_content.append(
        f'  <tspan x="{right_x}" y="{y}">. <tspan class="key">Lines of Code on GitHub</tspan><tspan class="dots">{escape_xml(loc_dots)}</tspan> '
        f'<tspan class="value">{loc_val}</tspan> ('
        f'<tspan class="add"> {escape_xml(add_val)}</tspan>, '
        f'<tspan class="del">{escape_xml(del_val)}</tspan> )</tspan>'
    )
    
    svg_content.append(f'</text>')
    svg_content.append(f'</svg>')
    
    with open(DARK_SVG_PATH if theme_name == "dark" else LIGHT_SVG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_content))

def main():
    print("Loading ASCII art...")
    ascii_art = load_and_trim_ascii()
    print(f"Loaded {len(ascii_art)} lines of ASCII art.")
    
    print("Fetching GitHub Stats...")
    stats = get_github_stats()
    print("GitHub Stats:", stats)
    
    print("Generating Dark Mode SVG...")
    generate_svg("dark", stats, ascii_art)
    
    print("Generating Light Mode SVG...")
    generate_svg("light", stats, ascii_art)
    
    print("Success! Created dark_mode.svg and light_mode.svg")

if __name__ == "__main__":
    main()
