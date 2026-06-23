import json
import pytest
from VibraVid.agent.output import output_json

def test_output_json_success():
    """Test successful JSON output."""
    result = output_json(success=True, data={"test": "value"}, exit_on_call=False)
    assert result["success"] is True
    assert result["data"]["test"] == "value"
    assert result["error"] is None
    assert "metadata" in result
    assert "version" in result["metadata"]
    assert "timestamp" in result["metadata"]

def test_output_json_error():
    """Test error JSON output."""
    result = output_json(success=False, error="Test error", exit_on_call=False)
    assert result["success"] is False
    assert result["data"] is None
    assert result["error"] == "Test error"

def test_output_json_print():
    """Test that output prints valid JSON."""
    import json
    result = output_json(success=True, data={"key": "value"}, exit_on_call=False)
    json_str = json.dumps(result)
    parsed = json.loads(json_str)
    assert parsed["success"] is True
