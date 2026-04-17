# path: backend/tests/test_query.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.utils.dsa_graphs import compute_dsa_score, code_to_ast_graph


# Unit: DSA Score
def test_dsa_score_identical_code():
    code = "def twoSum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target-n], i]\n        seen[n] = i"
    score, details = compute_dsa_score(code, code, "O(n)", "O(n)")
    assert score >= 80, f"Identical code should score >=80, got {score}"
    assert details["structural"] >= 35


def test_dsa_score_different_code():
    brute = "def twoSum(nums, t):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i]+nums[j]==t: return [i,j]"
    optimal = "def twoSum(nums, t):\n    d={}\n    for i,n in enumerate(nums):\n        if t-n in d: return [d[t-n],i]\n        d[n]=i"
    score_brute, _ = compute_dsa_score(brute, optimal, "O(n^2)", "O(1)")
    score_opt, _ = compute_dsa_score(optimal, optimal, "O(n)", "O(n)")
    assert score_opt > score_brute


def test_ast_graph_not_empty():
    code = "def foo(x):\n    return x + 1"
    G = code_to_ast_graph(code)
    assert len(G.nodes) > 0


# Integration: API health
@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# Integration: Register + Login
@pytest.mark.asyncio
async def test_register_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "Test@1234", "name": "Tester"},
        )
        assert reg.status_code == 200
        token = reg.json()["access_token"]
        assert len(token) > 10