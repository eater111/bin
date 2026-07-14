import sqlite3
import hashlib
import shutil
import mimetypes
from pathlib import Path
from datetime import datetime

class CASStorage:
    # ---------------------------------------------------------
    # setup
    # ---------------------------------------------------------

    def log(self, msg):
        if not getattr(self, "verbose", False):
            return

        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [CAS] {msg}")
            
    def __init__(self, db_path="cas.db", storage_dir="objects", verbose=True):
        self.verbose = verbose
        self.db_path = db_path
        self.storage_dir = Path(storage_dir)

        self.log(f"Database: {self.db_path}")
        self.log(f"Storage directory: {self.storage_dir}")

        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

        self.log("Connected to database")

        self._init_db()

    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): self.close()

    
    def close(self):
        self.conn.close()

    def _init_db(self):
        self.log("Initializing database schema")
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS objects (
                hash TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER,
                hash TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                size INTEGER NOT NULL,
                mime_type TEXT,
                mtime REAL,
                ctime REAL,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(hash)
                    REFERENCES objects(hash)
                    ON DELETE CASCADE,

                FOREIGN KEY(collection_id)
                    REFERENCES collections(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS tags (
                entry_id INTEGER NOT NULL,
                tag TEXT NOT NULL,

                PRIMARY KEY(entry_id, tag),

                FOREIGN KEY(entry_id)
                    REFERENCES entries(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_entries_hash
                ON entries(hash);

            CREATE INDEX IF NOT EXISTS idx_entries_filename
                ON entries(filename);

            CREATE INDEX IF NOT EXISTS idx_entries_collection
                ON entries(collection_id);
        """)

        self.conn.commit()
        
        self.log("Database ready")

    # ---------------------------------------------------------
    # object storage
    # ---------------------------------------------------------

    def _sha256_file(self, path):
        self.log(f"Hashing: {path}")
        h = hashlib.sha256()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)

        digest = h.hexdigest()

        self.log(f"SHA256: {digest}")

        return digest

    def _object_path(self, hash_value):
        return self.storage_dir / hash_value[:2] / hash_value[2:]

    def _store_file(self, path):
        self.log(f"Processing file: {path}")

        size = path.stat().st_size
        self.log(f"Size: {size:,} bytes")

        file_hash = self._sha256_file(path)

        obj = self._object_path(file_hash)

        self.log(f"Object path: {obj}")

        obj.parent.mkdir(parents=True, exist_ok=True)

        if not obj.exists():
            self.log("Copying object into CAS storage")
            shutil.copy2(path, obj)
        else:
            self.log("Duplicate object detected, skipping copy")

        self.conn.execute("""
            INSERT INTO objects(hash, size)
            VALUES (?, ?)
            ON CONFLICT(hash)
            DO UPDATE SET size=excluded.size
        """, (file_hash, size))

        self.conn.commit()

        self.log(f"Stored object {file_hash}")

        return file_hash

    def retrieve(self, hash_value, output_path):
        self.log(
            f"Restoring object {hash_value[:12]}... "
            f"to {output_path}"
        )
        src = self._object_path(hash_value)

        if not src.exists():
            raise FileNotFoundError(hash_value)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, output_path)
        
        self.log("Restore complete")

    def exists(self, hash_value):
        cur = self.conn.execute(
            "SELECT 1 FROM objects WHERE hash=?",
            (hash_value,)
        )

        return (
            cur.fetchone() is not None and
            self._object_path(hash_value).exists()
        )

    def delete(self, hash_value):
        self.conn.execute(
            "DELETE FROM objects WHERE hash=?",
            (hash_value,)
        )
        self.conn.commit()

        obj = self._object_path(hash_value)

        if obj.exists():
            obj.unlink()

    # ---------------------------------------------------------
    # import
    # ---------------------------------------------------------

    def store(self, path):
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        if path.is_file():
            self.log(f"Importing single file: {path}")
            file_hash = self._store_file(path)

            stat = path.stat()
            mime_type, _ = mimetypes.guess_type(path)

            cur = self.conn.execute("""
                INSERT INTO entries (
                    hash, relative_path, filename,
                    size, mime_type, mtime, ctime
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_hash,
                path.name,
                path.name,
                stat.st_size,
                mime_type,
                stat.st_mtime,
                stat.st_ctime,
            ))

            self.conn.commit()
            self.log(
                f"Entry #{cur.lastrowid} created "
                f"({path.name}) -> {file_hash[:12]}..."
            )
            return {
                "entry_id": cur.lastrowid,
                "hash": file_hash
            }

        self.log(f"Importing directory: {path}")
        
        cur = self.conn.execute(
            "INSERT INTO collections(name) VALUES (?)",
            (path.name,)
        )

        collection_id = cur.lastrowid
        
        self.log(
            f"Created collection #{collection_id} "
            f"({path.name})"
        )

        self.conn.commit()

        results = []

        for file in path.rglob("*"):
            if not file.is_file():
                continue

            self.log(f"Importing {file}")
            
            rel = file.relative_to(path)

            stat = file.stat()
            mime_type, _ = mimetypes.guess_type(file)

            file_hash = self._store_file(file)

            cur = self.conn.execute("""
                INSERT INTO entries (
                    collection_id,
                    hash,
                    relative_path,
                    filename,
                    size,
                    mime_type,
                    mtime,
                    ctime
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection_id,
                file_hash,
                str(rel),
                file.name,
                stat.st_size,
                mime_type,
                stat.st_mtime,
                stat.st_ctime,
            ))

            results.append({
                "entry_id": cur.lastrowid,
                "hash": file_hash,
                "path": str(rel)
            })

        self.conn.commit()

        return {
            "collection_id": collection_id,
            "files": results
        }
        
        self.log(
            f"Imported {len(results)} files "
            f"into collection #{collection_id}"
        )

    # ---------------------------------------------------------
    # queries
    # ---------------------------------------------------------

    def list_objects(self):
        return self.conn.execute("""
            SELECT hash, size, created_at
            FROM objects
            ORDER BY created_at DESC
        """).fetchall()

    def list_collections(self):
        return self.conn.execute("""
            SELECT id, name, created_at
            FROM collections
            ORDER BY created_at DESC
        """).fetchall()

    def list_entries(self):
        return self.conn.execute("""
            SELECT
                e.id,
                e.filename,
                e.relative_path,
                e.hash,
                e.size,
                e.mime_type,
                e.imported_at,
                c.name
            FROM entries e
            LEFT JOIN collections c
                ON c.id = e.collection_id
            ORDER BY e.imported_at DESC
        """).fetchall()

    def find_by_name(self, pattern):
        return self.conn.execute("""
            SELECT
                id,
                filename,
                relative_path,
                hash
            FROM entries
            WHERE filename LIKE ?
        """, (f"%{pattern}%",)).fetchall()

    # ---------------------------------------------------------
    # restore
    # ---------------------------------------------------------

    def retrieve_entry(self, entry_id, output_path):
        row = self.conn.execute("""
            SELECT hash
            FROM entries
            WHERE id=?
        """, (entry_id,)).fetchone()

        if not row:
            raise ValueError(f"Entry {entry_id} not found")

        self.retrieve(row[0], output_path)

    def restore_collection(self, collection_id, output_dir):
        self.log(
            f"Restoring collection #{collection_id} "
            f"into {output_dir}"
        )

        output_dir = Path(output_dir)

        rows = self.conn.execute("""
            SELECT hash, relative_path
            FROM entries
            WHERE collection_id=?
        """, (collection_id,)).fetchall()

        self.log(f"{len(rows)} files found")

        for file_hash, rel in rows:
            self.log(f"Restoring {rel}")

            target = output_dir / rel

            target.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            self.retrieve(file_hash, target)

        self.log("Collection restore complete")