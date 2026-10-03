import unittest
from analyzer.repo_ingest import validate_github_url, score_file_relevance

class TestRepoIngest(unittest.TestCase):
    def test_url_validation_valid(self):
        valid, url, owner, repo = validate_github_url("https://github.com/facebook/react")
        self.assertTrue(valid)
        self.assertEqual(url, "https://github.com/facebook/react")
        self.assertEqual(owner, "facebook")
        self.assertEqual(repo, "react")

        valid2, url2, owner2, repo2 = validate_github_url("https://github.com/vuejs/core.git")
        self.assertTrue(valid2)
        self.assertEqual(repo2, "core")

    def test_url_validation_invalid(self):
        # Non-github domain
        valid, _, _, _ = validate_github_url("https://gitlab.com/owner/repo")
        self.assertFalse(valid)

        # Invalid path format
        valid2, _, _, _ = validate_github_url("https://github.com/onlyowner")
        self.assertFalse(valid2)

        # Non-http
        valid3, _, _, _ = validate_github_url("git@github.com:owner/repo.git")
        self.assertFalse(valid3)

    def test_relevance_scoring(self):
        # Entry HTML and main components score highest
        score_html = score_file_relevance("index.html")
        score_comp = score_file_relevance("src/components/Button.jsx")
        score_css = score_file_relevance("styles/main.css")
        score_util = score_file_relevance("src/utils/math.js")

        self.assertGreater(score_html, score_css)
        self.assertGreater(score_comp, score_util)

if __name__ == "__main__":
    unittest.main()
