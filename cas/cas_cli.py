import argparse
from cas import CASStorage


def main():
    p = argparse.ArgumentParser("CAS Storage CLI")
    p.add_argument("--db", default="cas.db")
    p.add_argument("--dir", default="objects")
    p.add_argument("--quiet", action="store_true")

    sp = p.add_subparsers(dest="cmd", required=True)

    sp.add_parser("collections")
    sp.add_parser("entries")

    r = sp.add_parser("restore-collection")
    r.add_argument("collection_id", type=int)
    r.add_argument("output")

    s = sp.add_parser("search")
    s.add_argument("name")

    a = sp.add_parser("store")
    a.add_argument("file")

    b = sp.add_parser("retrieve")
    b.add_argument("hash")
    b.add_argument("output")

    c = sp.add_parser("exists")
    c.add_argument("hash")

    sp.add_parser("list")

    d = sp.add_parser("delete")
    d.add_argument("hash")

    args = p.parse_args()

    with CASStorage(args.db, args.dir, not args.quiet) as cas:
        cmd = args.cmd

        if cmd == "store":
            r = cas.store(args.file)
            if isinstance(r, dict):
                for f, h in r.items(): print(h, f)
            else:
                print(r)

        elif cmd == "retrieve":
            cas.retrieve(args.hash, args.output)
            print("Restored to", args.output)

        elif cmd == "exists":
            print("YES" if cas.exists(args.hash) else "NO")

        elif cmd == "list":
            for h, s, t in cas.list_objects():
                print(h, s, "bytes", t)

        elif cmd == "delete":
            cas.delete(args.hash)
            print("Deleted")

        elif cmd == "collections":
            for r in cas.list_collections():
                print(r)

        elif cmd == "entries":
            for r in cas.list_entries():
                print(r)

        elif cmd == "search":
            for r in cas.find_by_name(args.name):
                print(r)

        elif cmd == "restore-collection":
            cas.restore_collection(args.collection_id, args.output)


if __name__ == "__main__":
    main()