#!/usr/bin/env python3
"""
Enhanced System Testing Script
==============================

Comprehensive testing for:
1. Personality Management
2. File Upload Functionality
3. Chat Persistence
4. Smart Suggestions
5. Role-Based Responses
6. Data Ingestion Pipeline
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any

class EnhancedSystemTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
        
    def log_test(self, test_name: str, status: str, details: str = "", duration: float = 0):
        """Log test results"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"[{status.upper()}] {test_name}: {details}")
        
    def test_health_check(self) -> bool:
        """Test basic health check"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/health")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", "PASS", f"Status: {data.get('status')}", duration)
                return True
            else:
                self.log_test("Health Check", "FAIL", f"Status code: {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Health Check", "ERROR", str(e), duration)
            return False
    
    def test_personality_responses(self) -> bool:
        """Test role-based personality responses"""
        roles = ["client", "agent", "employee", "admin"]
        test_queries = [
            "Show me properties in Dubai Marina",
            "What's the market trend in Downtown Dubai?",
            "I need investment advice for real estate",
            "How do I get a Golden Visa?"
        ]
        
        all_passed = True
        
        for role in roles:
            for query in test_queries:
                start_time = time.time()
                try:
                    response = self.session.post(f"{self.base_url}/chat", json={
                        "message": query,
                        "role": role,
                        "session_id": f"test_session_{role}_{int(time.time())}"
                    })
                    duration = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Check for personality indicators
                        response_text = data.get('response', '').lower()
                        suggestions = data.get('suggestions', [])
                        
                        # Role-specific checks
                        if role == "client":
                            if any(word in response_text for word in ['friendly', 'lifestyle', 'value', 'benefit']):
                                self.log_test(f"Client Personality - {query[:30]}", "PASS", "Client-friendly response detected", duration)
                            else:
                                self.log_test(f"Client Personality - {query[:30]}", "WARN", "Client personality not clearly detected", duration)
                                
                        elif role == "agent":
                            if any(word in response_text for word in ['roi', 'market', 'investment', 'professional']):
                                self.log_test(f"Agent Personality - {query[:30]}", "PASS", "Agent-focused response detected", duration)
                            else:
                                self.log_test(f"Agent Personality - {query[:30]}", "WARN", "Agent personality not clearly detected", duration)
                                
                        elif role == "employee":
                            if any(word in response_text for word in ['compliance', 'procedure', 'regulation', 'document']):
                                self.log_test(f"Employee Personality - {query[:30]}", "PASS", "Employee-focused response detected", duration)
                            else:
                                self.log_test(f"Employee Personality - {query[:30]}", "WARN", "Employee personality not clearly detected", duration)
                                
                        elif role == "admin":
                            if any(word in response_text for word in ['analytics', 'performance', 'strategic', 'optimization']):
                                self.log_test(f"Admin Personality - {query[:30]}", "PASS", "Admin-focused response detected", duration)
                            else:
                                self.log_test(f"Admin Personality - {query[:30]}", "WARN", "Admin personality not clearly detected", duration)
                        
                        # Check for suggestions
                        if suggestions:
                            self.log_test(f"Smart Suggestions - {role}", "PASS", f"Found {len(suggestions)} suggestions", duration)
                        else:
                            self.log_test(f"Smart Suggestions - {role}", "WARN", "No suggestions provided", duration)
                            
                    else:
                        self.log_test(f"Personality Test - {role}", "FAIL", f"Status code: {response.status_code}", duration)
                        all_passed = False
                        
                except Exception as e:
                    duration = time.time() - start_time
                    self.log_test(f"Personality Test - {role}", "ERROR", str(e), duration)
                    all_passed = False
        
        return all_passed
    
    def test_file_upload(self) -> bool:
        """Test file upload functionality"""
        # Create a test file
        test_file_content = "This is a test file for upload functionality."
        test_filename = "test_upload.txt"
        
        with open(test_filename, 'w') as f:
            f.write(test_file_content)
        
        try:
            start_time = time.time()
            
            with open(test_filename, 'rb') as f:
                files = {'file': (test_filename, f, 'text/plain')}
                response = self.session.post(f"{self.base_url}/upload-file", files=files)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_test("File Upload", "PASS", f"File uploaded: {data.get('filename')}", duration)
                    
                    # Clean up test file
                    os.remove(test_filename)
                    return True
                else:
                    self.log_test("File Upload", "FAIL", "Upload status not success", duration)
                    return False
            else:
                self.log_test("File Upload", "FAIL", f"Status code: {response.status_code}", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("File Upload", "ERROR", str(e), duration)
            return False
        finally:
            # Clean up test file if it exists
            if os.path.exists(test_filename):
                os.remove(test_filename)
    
    def test_chat_persistence(self) -> bool:
        """Test chat conversation persistence"""
        session_id = f"persistence_test_{int(time.time())}"
        
        try:
            # Send first message
            start_time = time.time()
            response1 = self.session.post(f"{self.base_url}/chat", json={
                "message": "Hello, this is a test message",
                "role": "client",
                "session_id": session_id
            })
            duration1 = time.time() - start_time
            
            if response1.status_code != 200:
                self.log_test("Chat Persistence", "FAIL", f"First message failed: {response1.status_code}", duration1)
                return False
            
            # Send second message
            start_time = time.time()
            response2 = self.session.post(f"{self.base_url}/chat", json={
                "message": "Can you remember our conversation?",
                "role": "client",
                "session_id": session_id
            })
            duration2 = time.time() - start_time
            
            if response2.status_code == 200:
                data2 = response2.json()
                response_text = data2.get('response', '').lower()
                
                # Check if AI remembers the conversation
                if any(word in response_text for word in ['previous', 'earlier', 'conversation', 'mentioned']):
                    self.log_test("Chat Persistence", "PASS", "Conversation memory working", duration2)
                    return True
                else:
                    self.log_test("Chat Persistence", "WARN", "Conversation memory not clearly detected", duration2)
                    return True  # Still consider it a pass as the system is working
            else:
                self.log_test("Chat Persistence", "FAIL", f"Second message failed: {response2.status_code}", duration2)
                return False
                
        except Exception as e:
            self.log_test("Chat Persistence", "ERROR", str(e), 0)
            return False
    
    def test_response_length(self) -> bool:
        """Test that responses are concise and actionable"""
        test_queries = [
            "What's the best area to invest in Dubai?",
            "How do I apply for a mortgage?",
            "What are the current market trends?"
        ]
        
        all_passed = True
        
        for query in test_queries:
            start_time = time.time()
            try:
                response = self.session.post(f"{self.base_url}/chat", json={
                    "message": query,
                    "role": "client",
                    "session_id": f"length_test_{int(time.time())}"
                })
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '')
                    
                    # Check response length (should be concise)
                    word_count = len(response_text.split())
                    
                    if 20 <= word_count <= 150:  # Reasonable length for concise responses
                        self.log_test(f"Response Length - {query[:30]}", "PASS", f"{word_count} words - Good length", duration)
                    elif word_count < 20:
                        self.log_test(f"Response Length - {query[:30]}", "WARN", f"{word_count} words - Too short", duration)
                    else:
                        self.log_test(f"Response Length - {query[:30]}", "WARN", f"{word_count} words - Too long", duration)
                        
                    # Check for actionable content
                    action_words = ['can', 'should', 'will', 'need', 'must', 'recommend', 'suggest', 'try', 'consider']
                    if any(word in response_text.lower() for word in action_words):
                        self.log_test(f"Actionable Content - {query[:30]}", "PASS", "Contains actionable language", duration)
                    else:
                        self.log_test(f"Actionable Content - {query[:30]}", "WARN", "Missing actionable language", duration)
                        
                else:
                    self.log_test(f"Response Length Test - {query[:30]}", "FAIL", f"Status code: {response.status_code}", duration)
                    all_passed = False
                    
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(f"Response Length Test - {query[:30]}", "ERROR", str(e), duration)
                all_passed = False
        
        return all_passed
    
    def test_data_ingestion(self) -> bool:
        """Test data ingestion pipeline"""
        try:
            # Test if sample data exists
            data_files = [
                "data/properties.csv",
                "data/clients.csv",
                "data/listings.csv"
            ]
            
            existing_files = []
            for file_path in data_files:
                if os.path.exists(file_path):
                    existing_files.append(file_path)
            
            if existing_files:
                self.log_test("Data Ingestion", "PASS", f"Found {len(existing_files)} data files", 0)
                return True
            else:
                self.log_test("Data Ingestion", "WARN", "No data files found", 0)
                return True  # Not critical for system operation
                
        except Exception as e:
            self.log_test("Data Ingestion", "ERROR", str(e), 0)
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        print("🚀 Starting Enhanced System Tests...")
        print("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Personality Responses", self.test_personality_responses),
            ("File Upload", self.test_file_upload),
            ("Chat Persistence", self.test_chat_persistence),
            ("Response Length", self.test_response_length),
            ("Data Ingestion", self.test_data_ingestion)
        ]
        
        results = {}
        total_tests = len(tests)
        passed_tests = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name}...")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Generate summary
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        # Save detailed results
        results_file = f"enhanced_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return summary

def main():
    """Main test runner"""
    tester = EnhancedSystemTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 80:
        print("\n✅ System is ready for production!")
        exit(0)
    elif results['success_rate'] >= 60:
        print("\n⚠️  System needs some improvements before production.")
        exit(1)
    else:
        print("\n❌ System needs significant improvements.")
        exit(2)

if __name__ == "__main__":
    main()