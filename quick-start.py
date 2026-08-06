#!/usr/bin/env python3
"""
One-click setup: Extract agents, create GitHub repos, prepare for deployment.
Run: py -3 quick-start.py
"""

import os
import subprocess
import sys
from pathlib import Path

GIT_PATH = r"C:\Program Files\Git\cmd\git.exe"
GITHUB_USERNAME = "Ismail-2001"

AGENTS = [
    ("cs-agent", "Customer Support Agent", "AI-powered customer support automation"),
    ("inventory-agent", "Inventory Agent", "AI demand forecasting and inventory optimization"),
    ("pricing-agent", "Price Optimization Agent", "Dynamic pricing based on competitor analysis"),
    ("reviews-agent", "Review Moderation Agent", "Sentiment analysis and automated review responses"),
    ("marketing-agent", "Marketing Automation Agent", "AI campaign creation and audience segmentation"),
    ("cart-recovery-agent", "Cart Recovery Agent", "Abandoned cart recovery with personalized sequences"),
    ("fraud-agent", "Fraud Detection Agent", "Real-time transaction fraud detection"),
]


def run_cmd(cmd, cwd=None):
    """Run a command and return output."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        executable="C:\\Windows\\System32\\cmd.exe"
    )
    return result.returncode == 0, result.stdout + result.stderr


def create_github_repo(name, description):
    """Create a GitHub repo using the API."""
    print(f"\n  Creating GitHub repo: {name}...")
    
    # Use GitHub CLI if available
    try:
        result = subprocess.run(
            ["gh", "repo", "create", f"{GITHUB_USERNAME}/{name}", 
             "--public", "--description", description],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  ✅ Created: https://github.com/{GITHUB_USERNAME}/{name}")
            return True
    except FileNotFoundError:
        pass
    
    # Manual instructions
    print(f"  ⚠️  Create manually: https://github.com/new")
    print(f"     Name: {name}")
    print(f"     Description: {description}")
    print(f"     Visibility: Public")
    return False


def setup_agent(agent_dir, name, description):
    """Setup a single agent for GitHub."""
    print(f"\n{'='*50}")
    print(f"Setting up: {name}")
    print(f"{'='*50}")
    
    if not Path(agent_dir).exists():
        print(f"  ❌ Directory not found: {agent_dir}")
        return False
    
    # Init git
    run_cmd(f'"{GIT_PATH}" init', cwd=agent_dir)
    run_cmd(f'"{GIT_PATH}" add .', cwd=agent_dir)
    run_cmd(f'"{GIT_PATH}" commit -m "Initial commit: {name} standalone package"', cwd=agent_dir)
    
    # Create GitHub repo
    create_github_repo(name, description)
    
    # Add remote
    remote_url = f"https://github.com/{GITHUB_USERNAME}/{name}.git"
    run_cmd(f'"{GIT_PATH}" remote add origin {remote_url}', cwd=agent_dir)
    run_cmd(f'"{GIT_PATH}" branch -M main', cwd=agent_dir)
    
    print(f"  ✅ Git initialized and committed")
    print(f"  📁 Local: {Path(agent_dir).absolute()}")
    print(f"  🔗 Remote: {remote_url}")
    
    return True


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    AI AGENT QUICK START                      ║
║            Extract, Setup, and Prepare for Selling            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check if agents exist
    if not Path("cs-agent").exists():
        print("⚠️  Agents not extracted yet. Running extraction...")
        os.system("py -3 scripts/extract-agents.py")
    
    print("\n📋 AGENTS TO SETUP:")
    for i, (agent_id, name, desc) in enumerate(AGENTS, 1):
        print(f"  {i}. {name} ({agent_id})")
    
    print("\n" + "="*50)
    print("Setting up each agent...")
    print("="*50)
    
    results = []
    for agent_id, name, desc in AGENTS:
        success = setup_agent(agent_id, name, desc)
        results.append((agent_id, name, success))
    
    # Summary
    print("\n" + "="*50)
    print("SETUP COMPLETE")
    print("="*50)
    
    print("\n✅ Successfully setup:")
    for agent_id, name, success in results:
        if success:
            print(f"  • {name} ({agent_id})")
    
    print("\n⚠️  Next steps:")
    print("1. Create repos on GitHub (if gh CLI not installed)")
    print("2. Push code: cd <agent> && git push -u origin main")
    print("3. Deploy to Railway/Render")
    print("4. Test with: curl <URL>/health")
    print("5. Start outreach!")
    
    print("\n📚 Guide: AGENT_SELLING_GUIDE.md")
    print("\n🎯 Revenue Target:")
    print("   Month 3: $1,500 MRR (1 client)")
    print("   Month 6: $6,000 MRR (3-4 clients)")
    print("   Month 12: $24,000 MRR (8-10 clients)")


if __name__ == "__main__":
    main()
