import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app import app


def test_garbled_token():
    with app.test_client() as client:
        resp = client.get('/api/my-results', headers={'Authorization': 'Bearer notajwt'})
        assert resp.status_code == 401
        assert resp.get_json()['msg'] == 'token invalid'
