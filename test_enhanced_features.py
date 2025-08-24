#!/usr/bin/env python3
"""
Comprehensive Testing Script for Enhanced Real Estate RAG Chat System
Tests all new features including role-based personalities, milestone detection, 
African agent recognition, and admin analytics.
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
API_BASE_URL = "http://localhost:8001"
TEST_SESSION_ID = f"test_session_{int(time.time())}"

class EnhancedFeatureTester:
    def __init__(self):
        self.results = []
        self.session_id = TEST_SESSION_ID
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()

    def test_health_check(self):
        """Test basic health check"""
        try:
            response = requests.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", "PASS", f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("Health Check", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Error: {str(e)}")
            return False

    def test_role_based_personalities(self):
        """Test role-based personality system"""
        roles = ['client', 'agent', 'employee', 'admin']
        
        for role in roles:
            try:
                response = requests.post(f"{API_BASE_URL}/chat", json={
                    "message": "Hello, how are you?",
                    "role": role,
                    "session_id": f"{self.session_id}_{role}"
                })
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '')
                    
                    # Check for role-specific greetings
                    expected_greetings = {
                        'client': 'Hi there! 👋',
                        'agent': 'Hi Agent, how can I help you today? 🏠',
                        'employee': 'Hello! 👨‍💼',
                        'admin': 'Greetings! ⚙️'
                    }
                    
                    if expected_greetings[role] in response_text:
                        self.log_test(f"Role-based Personality - {role.title()}", "PASS", 
                                    f"Found expected greeting: {expected_greetings[role]}")
                    else:
                        self.log_test(f"Role-based Personality - {role.title()}", "FAIL", 
                                    f"Expected greeting not found. Response: {response_text[:100]}...")
                else:
                    self.log_test(f"Role-based Personality - {role.title()}", "FAIL", 
                                f"Status code: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Role-based Personality - {role.title()}", "FAIL", f"Error: {str(e)}")

    def test_milestone_detection(self):
        """Test milestone detection and celebration"""
        milestones = [
            {
                'type': 'new_listing',
                'message': 'I just added a new property listing for a 3-bedroom apartment in Dubai Marina',
                'expected_celebration': '🎉 Congratulations on the new listing!'
            },
            {
                'type': 'deal_closed',
                'message': 'Great news! I successfully closed a deal for a villa in Palm Jumeirah',
                'expected_celebration': '💼 Fantastic work on closing that deal!'
            },
            {
                'type': 'viewing_scheduled',
                'message': 'I scheduled a viewing for tomorrow with a potential buyer',
                'expected_celebration': '📅 Excellent! Another viewing in the books.'
            },
            {
                'type': 'client_meeting',
                'message': 'I had a productive meeting with a client today about their investment plans',
                'expected_celebration': '🤝 Great job on the client meeting!'
            }
        ]
        
        for milestone in milestones:
            try:
                response = requests.post(f"{API_BASE_URL}/chat", json={
                    "message": milestone['message'],
                    "role": "agent",
                    "session_id": f"{self.session_id}_milestone_{milestone['type']}"
                })
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '')
                    
                    if milestone['expected_celebration'] in response_text:
                        self.log_test(f"Milestone Detection - {milestone['type']}", "PASS", 
                                    f"Found celebration: {milestone['expected_celebration']}")
                    else:
                        self.log_test(f"Milestone Detection - {milestone['type']}", "FAIL", 
                                    f"Expected celebration not found. Response: {response_text[:100]}...")
                else:
                    self.log_test(f"Milestone Detection - {milestone['type']}", "FAIL", 
                                f"Status code: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Milestone Detection - {milestone['type']}", "FAIL", f"Error: {str(e)}")

    def test_african_agent_recognition(self):
        """Test African agent recognition and celebration"""
        african_messages = [
            "I'm working with clients from Nigeria and Ghana",
            "My team includes agents from Kenya and South Africa",
            "We have strong connections in Ethiopia and Uganda"
        ]
        
        for i, message in enumerate(african_messages):
            try:
                response = requests.post(f"{API_BASE_URL}/chat", json={
                    "message": message,
                    "role": "agent",
                    "session_id": f"{self.session_id}_african_{i}"
                })
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '')
                    
                    # Check for African agent recognition
                    if 'african' in response_text.lower() or 'nigeria' in response_text.lower() or 'ghana' in response_text.lower():
                        self.log_test(f"African Agent Recognition - Test {i+1}", "PASS", 
                                    f"African context detected in response")
                    else:
                        self.log_test(f"African Agent Recognition - Test {i+1}", "FAIL", 
                                    f"No African context found. Response: {response_text[:100]}...")
                else:
                    self.log_test(f"African Agent Recognition - Test {i+1}", "FAIL", 
                                f"Status code: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"African Agent Recognition - Test {i+1}", "FAIL", f"Error: {str(e)}")

    def test_admin_analytics(self):
        """Test admin analytics panel"""
        try:
            # First, generate some activity
            for i in range(3):
                requests.post(f"{API_BASE_URL}/chat", json={
                    "message": f"Test message {i}",
                    "role": "admin",
                    "session_id": f"{self.session_id}_admin_{i}"
                })
            
            # Test admin analytics endpoint
            response = requests.get(f"{API_BASE_URL}/admin/analytics")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required analytics fields
                required_fields = ['total_sessions', 'total_messages', 'role_distribution', 'recent_activity']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Admin Analytics Panel", "PASS", 
                                f"Total sessions: {data['total_sessions']}, Total messages: {data['total_messages']}")
                else:
                    self.log_test("Admin Analytics Panel", "FAIL", 
                                f"Missing fields: {missing_fields}")
            else:
                self.log_test("Admin Analytics Panel", "FAIL", f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Analytics Panel", "FAIL", f"Error: {str(e)}")

    def test_file_upload(self):
        """Test file upload functionality"""
        try:
            # Create a test file
            test_content = "This is a test file for upload functionality."
            files = {'file': ('test_file.txt', test_content, 'text/plain')}
            
            response = requests.post(f"{API_BASE_URL}/upload-file", files=files)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_test("File Upload", "PASS", f"File uploaded: {data.get('filename')}")
                else:
                    self.log_test("File Upload", "FAIL", f"Upload failed: {data}")
            else:
                self.log_test("File Upload", "FAIL", f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("File Upload", "FAIL", f"Error: {str(e)}")

    def test_chat_persistence(self):
        """Test chat persistence across requests"""
        try:
            session_id = f"{self.session_id}_persistence"
            
            # Send first message
            response1 = requests.post(f"{API_BASE_URL}/chat", json={
                "message": "This is my first message",
                "role": "client",
                "session_id": session_id
            })
            
            if response1.status_code != 200:
                self.log_test("Chat Persistence", "FAIL", f"First message failed: {response1.status_code}")
                return
            
            # Send second message
            response2 = requests.post(f"{API_BASE_URL}/chat", json={
                "message": "This is my second message",
                "role": "client",
                "session_id": session_id
            })
            
            if response2.status_code == 200:
                self.log_test("Chat Persistence", "PASS", "Messages processed successfully")
            else:
                self.log_test("Chat Persistence", "FAIL", f"Second message failed: {response2.status_code}")
                
        except Exception as e:
            self.log_test("Chat Persistence", "FAIL", f"Error: {str(e)}")

    def test_conversation_summary(self):
        """Test conversation summary endpoint"""
        try:
            session_id = f"{self.session_id}_summary"
            
            # Send a message first
            requests.post(f"{API_BASE_URL}/chat", json={
                "message": "Test message for summary",
                "role": "agent",
                "session_id": session_id
            })
            
            # Get conversation summary
            response = requests.get(f"{API_BASE_URL}/conversation/{session_id}/summary")
            
            if response.status_code == 200:
                data = response.json()
                if 'session_id' in data and 'role' in data:
                    self.log_test("Conversation Summary", "PASS", 
                                f"Summary retrieved for session: {data['session_id']}")
                else:
                    self.log_test("Conversation Summary", "FAIL", "Missing required fields in summary")
            else:
                self.log_test("Conversation Summary", "FAIL", f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("Conversation Summary", "FAIL", f"Error: {str(e)}")

    def test_user_insights(self):
        """Test user insights endpoint"""
        try:
            session_id = f"{self.session_id}_insights"
            
            # Send a message first
            requests.post(f"{API_BASE_URL}/chat", json={
                "message": "I'm looking for properties in Dubai Marina under 2 million AED",
                "role": "client",
                "session_id": session_id
            })
            
            # Get user insights
            response = requests.get(f"{API_BASE_URL}/user/{session_id}/insights")
            
            if response.status_code == 200:
                data = response.json()
                if 'session_id' in data and 'preferences' in data:
                    self.log_test("User Insights", "PASS", 
                                f"Insights retrieved for session: {data['session_id']}")
                else:
                    self.log_test("User Insights", "FAIL", "Missing required fields in insights")
            else:
                self.log_test("User Insights", "FAIL", f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("User Insights", "FAIL", f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Enhanced Feature Testing Suite")
        print("=" * 50)
        
        # Run tests
        self.test_health_check()
        self.test_role_based_personalities()
        self.test_milestone_detection()
        self.test_african_agent_recognition()
        self.test_admin_analytics()
        self.test_file_upload()
        self.test_chat_persistence()
        self.test_conversation_summary()
        self.test_user_insights()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test_name']}: {result['details']}")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'test_summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {filename}")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! Enhanced features are working correctly.")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Please check the details above.")

if __name__ == "__main__":
    tester = EnhancedFeatureTester()
    tester.run_all_tests()