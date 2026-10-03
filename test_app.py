from app import app

def run_tests():
    client = app.test_client()

    # Test 0: GET /health (Chunk 0)
    res0 = client.get('/health')
    assert res0.status_code == 200, f"GET /health failed: {res0.status_code}"
    assert res0.get_json() == {"ok": True}, "GET /health payload mismatch"
    print("Test 0: GET /health -> 200 OK ({\"ok\": true})")

    # Test 1: GET /
    res1 = client.get('/')
    assert res1.status_code == 200, f"GET / failed: {res1.status_code}"
    print("Test 1: GET / -> 200 OK")

    # Test 2: GET /api/demo
    res2 = client.get('/api/demo')
    assert res2.status_code == 200, f"GET /api/demo failed: {res2.status_code}"
    data = res2.get_json()
    assert 'findings' in data and len(data['findings']) >= 7, "Demo findings missing"
    print(f"Test 2: GET /api/demo -> 200 OK ({len(data['findings'])} findings)")

    # Test 3: GET /api/demo/screenshot
    res3 = client.get('/api/demo/screenshot')
    assert res3.status_code == 200, f"GET /api/demo/screenshot failed: {res3.status_code}"
    print(f"Test 3: GET /api/demo/screenshot -> 200 OK ({len(res3.data)} bytes)")

    # Test 4: GET /demo
    res4 = client.get('/demo')
    assert res4.status_code == 200, f"GET /demo failed: {res4.status_code}"
    print("Test 4: GET /demo -> 200 OK")

    # Test 5: POST /api/analyze (End-to-End local testing)
    with open('static/demo/bad_app.png', 'rb') as f:
        img_bytes = f.read()

    from io import BytesIO
    data = {
        'image': (BytesIO(img_bytes), 'test.png'),
        'persona': 'First-time user',
        'goal': 'Inspect inventory dashboard'
    }
    import time
    t0 = time.time()
    res5 = client.post('/api/analyze', data=data, content_type='multipart/form-data')
    latency = time.time() - t0
    assert res5.status_code == 200, f"POST /api/analyze failed: {res5.status_code}, {res5.data}"
    res5_json = res5.get_json()
    assert 'findings' in res5_json and len(res5_json['findings']) > 0, "No findings returned"
    assert 'summary' in res5_json, "Summary missing"
    assert 'fix_prompt' in res5_json, "Fix prompt missing"
    print(f"Test 5: POST /api/analyze -> 200 OK ({len(res5_json['findings'])} findings in {latency*1000:.1f}ms!)")

    # Test 6: GET /api/demo-repo
    res6 = client.get('/api/demo-repo')
    assert res6.status_code == 200, f"GET /api/demo-repo failed: {res6.status_code}"
    repo_data = res6.get_json()
    assert repo_data.get('mode') == 'repo', "Mode must be 'repo'"
    assert len(repo_data.get('findings', [])) >= 5, "Demo repo should have at least 5 findings"
    assert repo_data.get('summary', {}).get('verified_fixes', 0) >= 3, "Demo repo should have verified fixes"
    print(f"Test 6: GET /api/demo-repo -> 200 OK ({len(repo_data['findings'])} findings, {repo_data['summary']['verified_fixes']} verified fixes)")

    # Test 7: GET /api/jobs/demo-repo-vibecheck/patch
    res7 = client.get('/api/jobs/demo-repo-vibecheck/patch')
    assert res7.status_code == 200, f"GET /api/jobs/.../patch failed: {res7.status_code}"
    patch_str = res7.data.decode('utf-8')
    assert '--- a/' in patch_str, "Patch should contain standard unified diff headers"
    print(f"Test 7: GET /api/jobs/.../patch -> 200 OK ({len(patch_str)} characters of unified diff)")

    # Test 8: GET /api/jobs/demo-repo-vibecheck/zip
    res8 = client.get('/api/jobs/demo-repo-vibecheck/zip')
    assert res8.status_code == 200, f"GET /api/jobs/.../zip failed: {res8.status_code}"
    assert 'application/zip' in res8.content_type, "Should return zip mimetype"
    print(f"Test 8: GET /api/jobs/.../zip -> 200 OK ({len(res8.data)} bytes zip)")

    # Test 9: POST /api/analyze-repo
    res9 = client.post('/api/analyze-repo', json={
        'repo_url': 'https://github.com/vibecheck-ui/sample-flawed-app',
        'persona': 'Developer'
    })
    assert res9.status_code == 202, f"POST /api/analyze-repo failed: {res9.status_code}"
    job_id = res9.get_json().get('job_id')
    assert job_id, "Job ID should be returned"
    print(f"Test 9: POST /api/analyze-repo -> 202 Accepted (job_id: {job_id})")

    print("\nALL SMOKE, REPO MODE, API & ANALYSIS ENGINE TESTS PASSED!")

if __name__ == "__main__":
    run_tests()

