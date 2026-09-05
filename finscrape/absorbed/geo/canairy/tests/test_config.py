"""Test configuration loading and validation."""

import pytest
import yaml
from pathlib import Path

def test_config_file_exists():
    """Test that main config file exists and is valid YAML."""
    config_path = Path("config/config.yaml")
    assert config_path.exists()
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    assert "trip_wires" in config
    assert "alerts" in config
    assert len(config["trip_wires"]) == 6  # H1-H6 metrics

def test_trip_wire_thresholds():
    """Test that all trip-wires have proper thresholds."""
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)
    
    for name, trip_wire in config["trip_wires"].items():
        assert "thresholds" in trip_wire
        thresholds = trip_wire["thresholds"]
        
        # Each trip-wire should have green, amber, red thresholds
        assert "green" in thresholds
        assert "amber" in thresholds
        assert "red" in thresholds
