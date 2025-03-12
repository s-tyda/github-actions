from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


@app.get("/")
def root():
    return {
        "msg": "Hello World!"
    }


test_client = TestClient(app)

# requirements.txt
# .github/workflows/test.yml
def test_root():
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "msg": "Hello World!"
    }
