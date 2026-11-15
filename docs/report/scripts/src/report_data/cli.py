"""report-data build --root <repo> --out <thư mục generated>"""

import argparse
from pathlib import Path

from report_data import build, sources


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="report-data")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="sinh numbers.tex, numbers.json, bảng và hình")
    b.add_argument("--root", type=Path, required=True, help="gốc repo nghiên cứu")
    b.add_argument("--out", type=Path, required=True, help="thư mục generated/ của báo cáo")
    args = parser.parse_args(argv)
    data = sources.load(args.root)
    build.write(data, args.out)
    missing = sorted(k for k, v in data.items() if v is None)
    print(f"đã ghi {args.out}; nguồn chưa có: {', '.join(missing) or 'không'}")


if __name__ == "__main__":
    main()
