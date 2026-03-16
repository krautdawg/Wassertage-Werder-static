#!/usr/bin/env python3
"""Deploy static site to STRATO via SFTP using pexpect."""

import os
import sys
import pexpect

HOST = "51851574.ssh.w1.strato.hosting"
PORT = "22"
USER = "stu428205240"
PASSWORD = os.environ.get("STRATO_PASSWORD")

# Files and directories to upload (relative to this script's directory)
UPLOAD_ITEMS = [
    "index.html",
    "impressum.html",
    "datenschutz.html",
    ".htaccess",
    "robots.txt",
    "css/style.css",
    "assets/logo.png",
    "assets/hero.webp",
    "assets/ki-klub-logo.png",
]


def main():
    if not PASSWORD:
        print("ERROR: Set STRATO_PASSWORD environment variable first.")
        print("  export STRATO_PASSWORD='your-password-here'")
        sys.exit(1)

    local_dir = os.path.dirname(os.path.abspath(__file__))
    explore_mode = "--explore" in sys.argv

    print(f"Connecting to {USER}@{HOST}:{PORT} ...")
    child = pexpect.spawn(f"sftp -oPort={PORT} {USER}@{HOST}", encoding="utf-8", timeout=30)

    # Handle host key confirmation
    idx = child.expect(["password:", "Are you sure you want to continue connecting", pexpect.TIMEOUT], timeout=15)
    if idx == 1:
        child.sendline("yes")
        child.expect("password:")
    elif idx == 2:
        print("ERROR: Connection timed out.")
        sys.exit(1)

    child.sendline(PASSWORD)
    child.expect("sftp>")
    print("Connected.")

    if explore_mode:
        print("\n--- Exploring remote directory structure ---")
        child.sendline("pwd")
        child.expect("sftp>")
        print(child.before.strip())
        child.sendline("ls -la")
        child.expect("sftp>")
        print(child.before.strip())
        # Try common document roots
        for d in [".", "www", "public_html", "htdocs"]:
            child.sendline(f"ls -la {d}")
            child.expect("sftp>")
            output = child.before.strip()
            if "No such file" not in output and "not found" not in output:
                print(f"\n[{d}/]")
                print(output)
        child.sendline("bye")
        child.expect(pexpect.EOF)
        print("\nDone exploring. Update REMOTE_ROOT in this script if needed.")
        return

    # Upload files — default to current remote directory (STRATO typically lands in doc root)
    remote_root = "."

    # Create remote directories
    for d in ["css", "assets"]:
        child.sendline(f"mkdir {remote_root}/{d}")
        child.expect("sftp>")

    # Upload each file
    for item in UPLOAD_ITEMS:
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_root}/{item}"
        if not os.path.exists(local_path):
            print(f"  SKIP (not found): {item}")
            continue
        print(f"  Uploading {item} ...")
        child.sendline(f"put {local_path} {remote_path}")
        child.expect("sftp>", timeout=60)

    child.sendline("bye")
    child.expect(pexpect.EOF)
    print("\nAll files uploaded successfully.")


if __name__ == "__main__":
    main()
