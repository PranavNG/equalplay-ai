
from unittest.mock import patch

from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


@patch("src.api.main.generate_analysis")
def test_recap_endpoint(mock_generate):
    mock_generate.return_value = "Mocked match recap"

    response = client.get("/api/ai/analyse?mode=recap")

    assert response.status_code == 200
    assert response.json()["analysis"] == "Mocked match recap"
    mock_generate.assert_called_once_with("recap", None)


@patch("src.api.main.generate_analysis")
def test_simplified_endpoint(mock_generate):
    mock_generate.return_value = "Simple match explanation"

    response = client.get("/api/ai/analyse?mode=simplified")

    assert response.status_code == 200
    assert response.json()["analysis_type"] == "simplified"


@patch("src.api.main.generate_analysis")
def test_team_focus_endpoint(mock_generate):
    mock_generate.return_value = "Chelsea-focused analysis"

    response = client.get(
        "/api/ai/analyse",
        params={"mode": "team_focus", "team": "HOME"}
    )

    assert response.status_code == 200
    assert response.json()["team"] == "HOME"
    mock_generate.assert_called_once_with("team_focus", "HOME")


@patch("src.api.main.generate_analysis")
def test_invalid_mode(mock_generate):
    mock_generate.side_effect = ValueError("Unsupported analysis mode")

    response = client.get("/api/ai/analyse?mode=invalid")

    assert response.status_code == 400
