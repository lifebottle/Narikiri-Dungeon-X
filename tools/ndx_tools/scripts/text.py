import argparse
import sys

from ndx_tools.utils import string

__SCRIPT_CMD = "string"
__SCRIPT_DESC = "String tools"


def add_arguments_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--decode",
        help="Given a hex string, try to decode it",
    )
    parser.add_argument(
        "--encode",
        help="Given a tagged text, try to encode it as a hex string",
    )


def process_arguments(args: argparse.Namespace):
    if args.decode is not None:
        try:
            bt = bytes.fromhex(args.decode) + b"\x00"
        except ValueError:
            print("Couldn't interpret the input as a hex string!")
            sys.exit(-1)

        v = string.bytes_to_text(bt)
        print(v)
    elif args.encode is not None:
        bt = string.text_to_bytes(args.encode)
        print(" ".join([f"{x:02X}" for x in bt]))

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
