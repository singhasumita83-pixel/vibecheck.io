import unittest
import json
import time
from app import app, repo_jobs

class TestJobsAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_demo_repo_endpoint(self):
        res = self.client.get("/api/demo-repo")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("mode"), "repo")
        self.assertIn("findings", data)
        self.assertGreaterEqual(len(data["findings"]), 5)

    def test_demo_job_patch_download(self):
        res = self.client.get("/api/jobs/demo-repo-vibecheck/patch")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/plain", res.content_type)
        self.assertIn("--- a/", res.data.decode("utf-8"))

    def test_demo_job_filtered_patch(self):
        res = self.client.get("/api/jobs/demo-repo-vibecheck/patch?ids=r1")
        self.assertEqual(res.status_code, 200)
        patch_text = res.data.decode("utf-8")
        self.assertIn("styles.css", patch_text)
        self.assertNotIn("index.html", patch_text)

    def test_demo_job_zip_download(self):
        res = self.client.get("/api/jobs/demo-repo-vibecheck/zip")
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/zip", res.content_type)
        self.assertGreater(len(res.data), 100)

    def test_analyze_repo_invalid_url(self):
        res = self.client.post("/api/analyze-repo", json={"repo_url": "https://notgithub.com/abc/xyz"})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("Invalid GitHub repository URL", data.get("error", ""))

    def test_analyze_repo_ssrf_protection(self):
        res = self.client.post("/api/analyze-repo", json={
            "repo_url": "https://github.com/vibecheck-ui/sample-app",
            "model": {"base_url": "http://169.254.169.254/latest/meta-data/"}
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("not in the allowed", data.get("error", ""))

    def test_analyze_repo_demo_async_flow(self):
        res = self.client.post("/api/analyze-repo", json={
            "repo_url": "https://github.com/vibecheck-ui/sample-flawed-app",
            "persona": "UX Engineer",
            "goal": "Accessibility"
        })
        self.assertEqual(res.status_code, 202)
        data = res.get_json()
        job_id = data.get("job_id")
        self.assertTrue(job_id)

        # Poll until done or timeout
        for _ in range(20):
            status_res = self.client.get(f"/api/jobs/{job_id}")
            self.assertEqual(status_res.status_code, 200)
            status_data = status_res.get_json()
            if status_data.get("status") == "done":
                break
            time.sleep(0.2)

        self.assertEqual(status_data.get("status"), "done")
        self.assertEqual(status_data.get("stage"), "done")
        self.assertIsNotNone(status_data.get("result"))
        self.assertGreaterEqual(len(status_data["result"]["findings"]), 5)

if __name__ == "__main__":
    unittest.main()
