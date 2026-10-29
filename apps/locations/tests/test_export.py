import csv
import json

import pytest

from apps.categories.tests.factories import CategoryFactory

from .factories import LocationFactory

pytestmark = pytest.mark.django_db

EXPORT_URL = "/api/v1/locations/export/"


def test_export_csv_with_filter(api_client):
    parks = CategoryFactory(name="Parks")
    LocationFactory(title="Park", category=parks)
    LocationFactory(title="Museum")

    response = api_client.get(EXPORT_URL, {"export_format": "csv", "category": parks.pk})

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert "attachment" in response["Content-Disposition"]
    rows = list(csv.reader(response.content.decode("utf-8-sig").splitlines()))
    assert rows[0][:3] == ["id", "title", "description"]
    assert len(rows) == 2
    assert rows[1][1] == "Park"


def test_export_json(api_client):
    LocationFactory(title="Park")

    response = api_client.get(EXPORT_URL, {"export_format": "json"})

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json; charset=utf-8"
    data = json.loads(response.content)
    assert len(data) == 1
    assert data[0]["title"] == "Park"


def test_export_unknown_format_returns_400(api_client):
    response = api_client.get(EXPORT_URL, {"export_format": "xml"})

    assert response.status_code == 400
