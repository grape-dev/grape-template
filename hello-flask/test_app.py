"""心情追踪器单元测试"""
import unittest
from app import app


class TestMoodTracker(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    def test_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)

    def test_record_and_get_moods(self):
        r = self.client.post("/api/moods", json={"score": 5, "note": "great day"})
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        self.assertEqual(data["score"], 5)
        self.assertEqual(data["note"], "great day")

        r = self.client.get("/api/moods")
        self.assertEqual(r.status_code, 200)
        moods = r.get_json()
        self.assertTrue(len(moods) >= 1)

    def test_invalid_score(self):
        r = self.client.post("/api/moods", json={"score": 99})
        self.assertEqual(r.status_code, 400)

    def test_stats(self):
        self.client.post("/api/moods", json={"score": 3})
        r = self.client.get("/api/stats")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("total", data)
        self.assertIn("avg", data)
        self.assertIn("distribution", data)


if __name__ == "__main__":
    unittest.main()
