
import requests
import sys
import time
import uuid
from datetime import datetime

class LockedInAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check endpoint"""
        return self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )

    def test_user_signup(self):
        """Test user signup endpoint"""
        # Generate unique test user
        test_id = str(uuid.uuid4())[:8]
        test_phone = f"+1234567{test_id[-4:]}"
        test_email = f"test.user.{test_id}@example.com"
        
        user_data = {
            "name": f"Test User {test_id}",
            "email": test_email,
            "phone": test_phone,
            "goals": ["Exercise daily", "Read 30 minutes", "Drink more water"],
            "reminder_times": ["09:00", "14:00", "20:00"]
        }
        
        success, response = self.run_test(
            "User Signup",
            "POST",
            "users/signup",
            200,
            data=user_data
        )
        
        if success:
            self.test_user = response
            print(f"Created test user with phone: {test_phone}")
        
        return success, response

    def test_get_user(self):
        """Test get user by phone endpoint"""
        if not self.test_user:
            print("❌ Cannot test get user - no test user created")
            return False, {}
        
        return self.run_test(
            "Get User by Phone",
            "GET",
            f"users/{self.test_user['phone']}",
            200
        )

    def test_update_reminder_times(self):
        """Test update reminder times endpoint"""
        if not self.test_user:
            print("❌ Cannot test update reminder times - no test user created")
            return False, {}
        
        update_data = {
            "phone": self.test_user['phone'],
            "reminder_times": ["08:00", "13:00", "19:00"]
        }
        
        return self.run_test(
            "Update Reminder Times",
            "PUT",
            "users/reminder-times",
            200,
            data=update_data
        )

    def test_send_message(self):
        """Test send WhatsApp message endpoint"""
        if not self.test_user:
            print("❌ Cannot test send message - no test user created")
            return False, {}
        
        return self.run_test(
            "Send Test WhatsApp Message",
            "POST",
            "test/send-message",
            200,
            params={"phone": self.test_user['phone'], "message": "This is a test message from LockedIn API test"}
        )

    def test_scheduler_jobs(self):
        """Test get scheduled jobs endpoint"""
        return self.run_test(
            "Get Scheduled Jobs",
            "GET",
            "scheduler/jobs",
            200
        )

def main():
    # Get the backend URL from the environment or use the provided URL
    backend_url = "https://684f9f5f-0c49-4fb5-af51-b02ce5e77239.preview.emergentagent.com"
    
    print(f"🚀 Starting LockedIn API Tests against {backend_url}")
    
    # Setup tester
    tester = LockedInAPITester(backend_url)
    
    # Run tests
    tester.test_health_check()
    tester.test_user_signup()
    tester.test_get_user()
    tester.test_update_reminder_times()
    tester.test_send_message()
    tester.test_scheduler_jobs()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
