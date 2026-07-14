import os
import tarfile
from flask import Flask, Response, request, abort
import io
import threading
import subprocess

ARCHIVE_ROOT = os.path.abspath(".")

app = Flask(__name__)


def safe_join(base, path):
    full = os.path.abspath(os.path.join(base, path))
    if not full.startswith(base):
        raise ValueError("Invalid path")
    return full


@app.route("/download")
def download_folder():
    rel_path = request.args.get("path", "")

    try:
        folder = safe_join(ARCHIVE_ROOT, rel_path)
    except ValueError:
        abort(403)

    if not os.path.isdir(folder):
        abort(404)

    def generate_tar(folder):
        proc = subprocess.Popen(
            ["tar", "-cf", "-", "-C", folder, "."],
            stdout=subprocess.PIPE
        )

        while True:
            chunk = proc.stdout.read(8192)
            if not chunk:
                break
            yield chunk

    response = Response(generate_tar(folder), mimetype="application/x-tar")
    response.headers["Content-Disposition"] = f"attachment; filename={os.path.basename(folder)}.tar"

    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
