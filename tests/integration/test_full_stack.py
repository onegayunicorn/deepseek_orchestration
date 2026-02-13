import unittest
import requests
import json
import os
import time

class TestDeepSeekFullStack(unittest.TestCase):
    BASE_URL = "http://localhost:5000"
    API_KEY = "your-secret-api-key-here" # Matches default config for testing

    def test_01_health_check(self):
        """Test if the Web API is responding"""
        try:
            response = requests.get(f"{self.BASE_URL}/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['status'], 'healthy')
        except requests.exceptions.ConnectionError:
            self.fail("Web API server is not running")

    def test_02_status_endpoint_auth(self):
        """Test authentication on status endpoint"""
        headers = {"X-API-Key": self.API_KEY}
        response = requests.get(f"{self.BASE_URL}/api/v1/status", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_03_command_validation(self):
        """Test if dangerous commands are blocked"""
        headers = {"X-API-Key": self.API_KEY}
        payload = {"command": "rm -rf /"}
        response = requests.post(f"{self.BASE_URL}/api/v1/execute", headers=headers, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("blocked", response.json().get('error', '').lower())

if __name__ == "__main__":
    unittest.main()
