#!/usr/bin/env python3

from pathlib import Path
from html import escape
import json
import re
import sys

aports = Path(sys.argv[1])
output = Path(sys.argv[2])

identities = (
    "Francesco Colista",
    "fcolista",
    "fcolista@",
)

maintainer_re = re.compile(
    r"^\s*maintainer\s*=\s*[\"']([^\"']+)[\"']",
    re.MULTILINE | re.IGNORECASE,
)

legacy_re = re.compile(
    r"^\s*#\s*Maintainer:\s*(.+)$",
    re.MULTILINE | re.IGNORECASE,
)

packages = []

for apkbuild in sorted(aports.glob("*/*/APKBUILD")):
    relative = apkbuild.relative_to(aports)
    repository = relative.parts[0]
    package = relative.parts[1]

    text = apkbuild.read_text(errors="replace")
    match = maintainer_re.search(text) or legacy_re.search(text)

    if not match:
        continue

    maintainer = match.group(1).strip().lower()

    if not any(identity.lower() in maintainer for identity in identities):
        continue

    packages.append({
        "repository": repository,
        "package": package,
        "path": str(relative.parent),
        "apkbuild": f"https://github.com/alpinelinux/aports/tree/master/{relative.parent}",
        "maintainer": match.group(1).strip(),
    })

packages.sort(key=lambda item: (item["repository"], item["package"]))

output.mkdir(parents=True, exist_ok=True)
(output / "packages.json").write_text(
    json.dumps(packages, indent=2) + "\n"
)

rows = "\n".join(
    f"""
    <tr>
      <td>{escape(item["repository"])}</td>
      <td><a href="{escape(item["apkbuild"])}">{escape(item["package"])}</a></td>
      <td>{escape(item["maintainer"])}</td>
    </tr>
    """
    for item in packages
)

html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Francesco Colista — Alpine Linux packages</title>
  <style>
    body {{
      font-family: system-ui, sans-serif;
      max-width: 1100px;
      margin: 2rem auto;
      padding: 0 1rem;
      color: #222;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
    }}
    th, td {{
      border-bottom: 1px solid #ddd;
      padding: .55rem;
      text-align: left;
    }}
    th {{
      background: #f4f4f4;
    }}
    input {{
      width: 100%;
      max-width: 500px;
      padding: .6rem;
      margin: 1rem 0;
      font-size: 1rem;
    }}
  </style>
</head>
<body>
  <h1>Alpine Linux package maintenance</h1>

  <p>
    I am an individual Alpine Linux package maintainer contributing to the
    shared <code>aports</code> repository.
  </p>

  <p>
    Current packages listed: <strong>{len(packages)}</strong>
  </p>

  <p>
    <a href="https://github.com/sponsors/fcolista">Support me on GitHub Sponsors</a>
  </p>

  <input id="filter" type="search" placeholder="Filter packages...">

  <table id="packages">
    <thead>
      <tr>
        <th>Repository</th>
        <th>Package</th>
        <th>Maintainer metadata</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>

  <script>
    const filter = document.getElementById("filter");
    filter.addEventListener("input", () => {{
      const query = filter.value.toLowerCase();
      document.querySelectorAll("#packages tbody tr").forEach(row => {{
        row.hidden = !row.textContent.toLowerCase().includes(query);
      }});
    }});
  </script>
</body>
</html>
"""

(output / "index.html").write_text(html)
