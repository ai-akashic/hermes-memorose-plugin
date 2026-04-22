import argparse

from memorose_cli import register_cli


def test_register_cli_sets_memorose_subcommands():
    parser = argparse.ArgumentParser()
    register_cli(parser)
    assert parser.get_default("func") is not None
