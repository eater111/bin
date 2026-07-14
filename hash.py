import os
import json
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


ARCHIVE_ROOT = "."
CACHE_FILE = ".checksum_cache.json"
MAX_WORKERS = os.cpu_count() or 4




def load_cache():
    if Path(CACHE_FILE).exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}




def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)




def hash_file(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()




def hash_both(path):
    """Compute both hashes for a file."""
    return (
        hash_file(path, "md5"),
        hash_file(path, "sha256"),
    )




def get_file_info(path):
    stat = path.stat()
    return {
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }




def process_folder(folder, cache, executor):
    md5_lines = []
    sha_lines = []


    folder_path = Path(folder)


    try:
        entries = sorted(folder_path.iterdir())
    except Exception as e:
        print(f"[ERROR] Could not list directory {folder}: {e}")
        return


    futures = {}
    results = {}


    for entry in entries:
        name = entry.name


        if name in ("index.html", "checksums.md5", "checksums.sha256"):
            continue
        if entry.is_dir():
            continue
        if entry.is_symlink():
            print(f"[SKIP] Symlink skipped: {entry}")
            continue


        key = str(entry.resolve())
        file_info = get_file_info(entry)
        cached = cache.get(key)


        # unchanged → reuse cache
        if cached and cached["size"] == file_info["size"] and cached["mtime"] == file_info["mtime"]:
            results[key] = {
                "name": name,
                "md5": cached["md5"],
                "sha256": cached["sha256"],
                "info": file_info,
                "cached": True,
            }
        else:
            # changed → submit hashing job
            future = executor.submit(hash_both, entry)
            futures[future] = (key, name, file_info, entry)


    # collect parallel results
    for future in as_completed(futures):
        key, name, file_info, entry = futures[future]
        try:
            md5, sha = future.result()
            cache[key] = {
                **file_info,
                "md5": md5,
                "sha256": sha,
            }
            results[key] = {
                "name": name,
                "md5": md5,
                "sha256": sha,
                "info": file_info,
                "cached": False,
            }
            print(f"[HASHED] {entry}")
        except Exception as e:
            print(f"[ERROR] Could not hash file {entry}: {e}")


    # build output lines
    for key, data in results.items():
        if data["cached"]:
            print(f"[CACHE] {data['name']}")
        md5_lines.append(f"{data['md5']}  {data['name']}")
        sha_lines.append(f"{data['sha256']}  {data['name']}")


    # write checksum files
    if md5_lines:
        try:
            with open(folder_path / "checksums.md5", "w", encoding="utf-8") as f:
                f.write("\n".join(sorted(md5_lines)))
            print(f"[OK] MD5 written: {folder}")
        except Exception as e:
            print(f"[ERROR] Could not write MD5 for {folder}: {e}")


    if sha_lines:
        try:
            with open(folder_path / "checksums.sha256", "w", encoding="utf-8") as f:
                f.write("\n".join(sorted(sha_lines)))
            print(f"[OK] SHA256 written: {folder}")
        except Exception as e:
            print(f"[ERROR] Could not write SHA256 for {folder}: {e}")




def cleanup_cache(cache):
    """Remove entries for files that no longer exist."""
    to_delete = []
    for path in cache:
        if not Path(path).exists():
            to_delete.append(path)


    for path in to_delete:
        del cache[path]


    if to_delete:
        print(f"[CLEANUP] Removed {len(to_delete)} stale cache entries")




def build():
    cache = load_cache()


    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for root, dirs, files in os.walk(ARCHIVE_ROOT):
            process_folder(root, cache, executor)
            print("Checksums generated:", root)


    cleanup_cache(cache)
    save_cache(cache)




if __name__ == "__main__":
    build()