import os
from pathlib import Path
from datetime import datetime

ARCHIVE_ROOT = "."


def format_size(size):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.0f} PB"


def folder_stats(path):

    total_size = 0
    file_count = 0
    folder_count = 0

    for root, dirs, files in os.walk(path):

        folder_count += len(dirs)

        for f in files:
            if f == "index.html":
                continue
            p = os.path.join(root, f)
            total_size += os.path.getsize(p)
            file_count += 1

    return total_size, file_count, folder_count


def read_checksums(folder, filename):

    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        return {}

    hashes = {}

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.strip().split(None, 1)

            if len(parts) >= 2:
                hashes[parts[1]] = parts[0]

    return hashes


def build_breadcrumbs(rel_path):
    parts = rel_path.split(" / ")

    crumbs = []
    path_accum = []

    for i, part in enumerate(parts):
        path_accum.append(part)

        # build relative link
        if i == 0:
            href = "/"
        else:
            href = "/" + "/".join(parts[1 : i + 1]) + "/index.html"

        crumbs.append(f"<a href='{href}'>{part}</a>")

    return " / ".join(crumbs)


def generate_html(folder, rel_path):

    md5s = read_checksums(folder, "checksums.md5")
    sha256s = read_checksums(folder, "checksums.sha256")

    total_size, file_count, folder_count = folder_stats(folder)

    html = []

    html.append("<html>")
    html.append("<head>")
    html.append("<meta charset='utf-8'>")
    html.append("</head>")

    html.append("<style>")
    html.append("</style>")

    html.append("<body>")
    html.append("<pre>")

    html.append(build_breadcrumbs(rel_path))
    html.append("=" * 55)
    html.append("")

    html.append(f"archive_size: {format_size(total_size)} ({total_size:,} bytes)")
    html.append(f"file_count: {file_count}")
    html.append(f"folder_count: {folder_count}")
    html.append("")

    if os.path.exists(os.path.join(folder, "checksums.md5")):
        html.append("<a href='checksums.md5'>checksums.md5</a>")

    if os.path.exists(os.path.join(folder, "checksums.sha256")):
        html.append("<a href='checksums.sha256'>checksums.sha256</a><br>")

    html.append("=" * 55)
    html.append("")

    entries = os.listdir(folder)

    dirs = []
    files = []

    for name in entries:
        if name in ("index.html", "checksums.md5", "checksums.sha256"):
            continue

        path = os.path.join(folder, name)

        if os.path.isdir(path):
            dirs.append(name)
        else:
            files.append(name)

    # sort separately
    dirs.sort()
    files.sort()

    # ---- DIRECTORIES FIRST ----
    for name in dirs:
        sub_path = os.path.relpath(os.path.join(folder, name), ARCHIVE_ROOT)

        html.append(
            f"Dir  <a href='{name}/index.html'>{name}</a> "
        )

    # ---- THEN FILES ----
    for name in files:
        path = os.path.join(folder, name)

        try:
            stat = os.stat(path)
        except OSError:
            continue

        size = format_size(stat.st_size)
        dt = datetime.fromtimestamp(stat.st_mtime)
        date = dt.strftime("%Y-%m-%d")
        time = dt.strftime("%H:%M:%S")

        md5 = md5s.get(name, "N/A")
        sha = sha256s.get(name, "N/A")

        html.append(f"File <a href='{name}'>{name}</a>")
        html.append(f"     {size:<6} {date}  {time}")
        html.append(f"     MD5    : {md5}")
        html.append(f"     SHA256 : {sha}")

    html.append("</pre>")
    html.append("</body>")
    html.append("</html>")

    return "\n".join(html)


def build():

    root = Path(ARCHIVE_ROOT)

    for current, dirs, files in os.walk(root):

        rel = os.path.relpath(current, root)
        rel_path = "root" if rel == "." else f"root / {rel.replace(os.sep, ' / ')}"

        html = generate_html(current, rel_path)

        with open(Path(current) / "index.html", "w", encoding="utf8") as f:
            f.write(html)

        print("HTML generated:", Path(current) / "index.html")


if __name__ == "__main__":
    build()
