# Tests

Run the starter API smoke tests from the repository root:

```sh
docker compose -f deploy/docker-compose.yml run --rm web pytest -c pytest.ini
```

These tests only cover the health/status endpoints and HTML response. The MVP does not yet have authentication, database persistence, VRM polling, or media uploads.
