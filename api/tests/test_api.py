
import re
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

MOCK_REDIS = MagicMock()

with patch("redis.Redis", return_value=MOCK_REDIS):
    from main import app

client = TestClient(app)

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _reset():
    MOCK_REDIS.reset_mock()


class TestCreateJob:
    def setup_method(self):
        _reset()

    def test_returns_201(self):
        response = client.post("/jobs")
        assert response.status_code == 201

    def test_response_has_job_id(self):
        response = client.post("/jobs")
        assert "job_id" in response.json()

    def test_job_id_is_valid_uuid(self):
        job_id = client.post("/jobs").json()["job_id"]
        assert UUID_RE.match(job_id), f"Not a UUID: {job_id}"

    def test_pushes_to_redis_queue(self):
        job_id = client.post("/jobs").json()["job_id"]
        MOCK_REDIS.lpush.assert_called_once_with("job", job_id)

    def test_sets_queued_status(self):
        job_id = client.post("/jobs").json()["job_id"]
        MOCK_REDIS.hset.assert_called_once_with(f"job:{job_id}", "status", "queued")

    def test_unique_ids(self):
        ids = {client.post("/jobs").json()["job_id"] for _ in range(5)}
        assert len(ids) == 5


class TestGetJob:
    def setup_method(self):
        _reset()

    def test_returns_200_when_found(self):
        job_id = str(uuid.uuid4())
        MOCK_REDIS.hget.return_value = "queued"
        assert client.get(f"/jobs/{job_id}").status_code == 200

    def test_response_shape(self):
        job_id = str(uuid.uuid4())
        MOCK_REDIS.hget.return_value = "queued"
        data = client.get(f"/jobs/{job_id}").json()
        assert data["job_id"] == job_id
        assert data["status"] == "queued"

    def test_returns_404_when_not_found(self):
        job_id = str(uuid.uuid4())
        MOCK_REDIS.hget.return_value = None
        assert client.get(f"/jobs/{job_id}").status_code == 404

    def test_returns_400_for_invalid_uuid(self):
        assert client.get("/jobs/not-a-uuid").status_code == 400

    def test_reflects_completed_status(self):
        job_id = str(uuid.uuid4())
        MOCK_REDIS.hget.return_value = "completed"
        assert client.get(f"/jobs/{job_id}").json()["status"] == "completed"

    def test_queries_correct_redis_key(self):
        job_id = str(uuid.uuid4())
        MOCK_REDIS.hget.return_value = "queued"
        client.get(f"/jobs/{job_id}")
        MOCK_REDIS.hget.assert_called_once_with(f"job:{job_id}", "status")


class TestCors:
    def setup_method(self):
        _reset()

    def test_cors_header_present(self):
        job_id = str(uuid.uuid4())
        MOCK_REDIS.hget.return_value = "queued"
        response = client.get(
            f"/jobs/{job_id}",
            headers={"Origin": "http://localhost:3000"},
        )
        assert "access-control-allow-origin" in response.headers
