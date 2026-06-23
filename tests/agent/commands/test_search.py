import pytest
from argparse import Namespace
from VibraVid.agent.commands.search import register, execute

def test_search_register():
    """Test that search command registers correctly."""
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    register(subparsers)
    
    args = parser.parse_args(['search', '--query', 'test', '--provider', 'streamingcommunity'])
    assert args.query == 'test'
    assert args.provider == 'streamingcommunity'

def test_search_execute_missing_query():
    """Test search with missing query."""
    args = Namespace(command='search', query=None, provider='streamingcommunity',
                     year=None, category=None, auto_first=False, global_search=False)
    with pytest.raises(SystemExit) as exc_info:
        execute(args)
    assert exc_info.value.code == 1

def test_search_execute_invalid_provider():
    """Test search with invalid provider."""
    args = Namespace(command='search', query='test', provider='nonexistent_provider_xyz',
                     year=None, category=None, auto_first=False, global_search=False)
    with pytest.raises(SystemExit) as exc_info:
        execute(args)
    assert exc_info.value.code == 1
