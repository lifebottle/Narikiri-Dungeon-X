import ndx_tools as tools

from .utils import argparser_ext as argparse


def tools_main():
    parser = argparse.ArgumentParser(
        description="Tools to manipulate files from Tales of Phantasia: Narikiri Dungeon X",
        prog="ndx-tools",
    )

    subparsers = parser.add_subparsers(
        description="tool", help="The utility to run", required=True
    )

    proj_group = subparsers.add_parser_group("Project tools:")  # type: ignore
    tools.project.extract.add_subparser(proj_group)
    tools.project.rebuild.add_subparser(proj_group)

    file_group = subparsers.add_parser_group("Single File tools:")  # type: ignore
    tools.scripts.text.add_subparser(file_group)
    tools.scripts.cab.add_subparser(file_group)
    tools.scripts.fps4.add_subparser(file_group)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    tools_main()
