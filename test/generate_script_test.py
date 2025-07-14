# File: test/generate_script_test.py

import sys
import os
import json
import pytest

# Add project root to sys.path to import main.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user'] = 'test'
        yield client

def test_generate_script_with_theme(client):
    data = {
        "theme": "motivation",
        "custom_topic": "",
        "language": "en"
    }
    response = client.post(
        "/generate-script",
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 200
    result = response.get_json()
    assert "script_text" in result
    assert len(result["script_text"].strip()) > 0
    print("✅ Theme-based script generated successfully.")

def test_generate_script_with_custom_topic(client):
    data = {
        "theme": "",
        "custom_topic": "moringa",
        "language": "en"
    }
    response = client.post(
        "/generate-script",
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 200
    result = response.get_json()
    assert "script_text" in result
    assert "moringa" in result["script_text"].lower()
    print("✅ Custom-topic script generated successfully.")

def test_generate_script_hindi(client):
    data = {
        "theme": "motivation",
        "custom_topic": "",
        "language": "hi"
    }
    response = client.post(
        "/generate-script",
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 200
    result = response.get_json()
    assert "script_text" in result
    assert any('\u0900' <= c <= '\u097F' for c in result["script_text"]), "Script should contain Hindi characters"
    print("✅ Hindi script generated successfully.")

def test_generate_script_missing_prompt(client):
    data = {
        "theme": "",
        "custom_topic": "",
        "language": "en"
    }
    response = client.post(
        "/generate-script",
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 400
    result = response.get_json()
    assert result is not None
    assert "error" in result
    print("✅ Missing prompt handled correctly.")
