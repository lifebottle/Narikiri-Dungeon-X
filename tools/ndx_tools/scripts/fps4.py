import argparse
from pathlib import Path
import sys

from ndx_tools.formats.fps4 import Fps4

__SCRIPT_CMD = "fps4"
__SCRIPT_DESC = "FPS4 tools"


def add_arguments_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--extract",
        help="path to an fps4 file",
        type=Path,
    )
    parser.add_argument(
        "--header",
        help="path to an fps4 header file",
        type=Path,
    )
    parser.add_argument(
        "--pack",
        help="path to input folder",
        type=Path,
    )
    parser.add_argument(
        "--output",
        help="path to output",
        type=Path,
    )


def process_arguments(args: argparse.Namespace):
    if args.extract is not None:
        if args.header is not None:
            fps4 = Fps4.from_file(args.header, args.extract)
        else:
            fps4 = Fps4.from_file(args.extract)

        out_path: Path = args.output
        if out_path.exists():
            if not out_path.is_dir():
                print("Output path is not a folder")
                sys.exit(-1)
        else:
            out_path.mkdir(parents=True)

        for name, data in fps4.files_dict.items():
            p: Path = out_path / name
            p.write_bytes(data)



def add_subparser(subparser: argparse._SubParsersAction):
    parser = subparser.add_parser(
        __SCRIPT_CMD, help=__SCRIPT_DESC, description=__SCRIPT_DESC
    )
    add_arguments_to_parser(parser)
    parser.set_defaults(func=process_arguments)


parser = argparse.ArgumentParser(description=__SCRIPT_DESC)
add_arguments_to_parser(parser)

if __name__ == "__main__":
    args = parser.parse_args()
    process_arguments(args)
