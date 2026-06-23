import pytest
from argparse import Namespace
from VibraVid.agent.commands.providers import register, execute

def test_providers_register():
    """Test that providers command registers correctly."""
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    register(subparsers)
    
    args = parser.parse_args(['providers'])
    assert hasattr(args, 'command')
    assert args.command == 'providers'

def test_providers_execute():
    """Test that providers command executes without error."""
    args = Namespace(command='providers', available=False)
    try:
        execute(args)
    except SystemExit as e:
        assert e.code == 0
