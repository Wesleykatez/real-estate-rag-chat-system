import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from collections import defaultdict
import uuid

class EnhancedAIManager:
    def __init__(self, model, db_url: str = None):
        self.model = model
        self.db_url = db_url
        self.user_sessions = {}
        self.milestone_tracker = defaultdict(lambda: {
            'new_listings': 0,
            'deals_closed': 0,
            'viewings_scheduled': 0,
            'client_meetings': 0,
            'african_leads': 0,
            'last_african_celebration': None
        })
        self.user_preferences = defaultdict(dict)
        self.conversation_history = defaultdict(list)
        
        # Role-based personality configurations
        self.personalities = {
            'client': {
                'greeting': "Hi there! 👋",
                'tone': 'friendly',
                'formality': 'casual',
                'technical_depth': 'basic',
                'focus': ['property benefits', 'lifestyle', 'investment potential'],
                'response_length': 'concise',
                'emoji_usage': 'frequent'
            },
            'agent': {
                'greeting': "Hi Agent, how can I help you today? 🏠",
                'tone': 'professional',
                'formality': 'semi-formal',
                'technical_depth': 'intermediate',
                'focus': ['ROI', 'market trends', 'sales techniques', 'client management'],
                'response_length': 'moderate',
                'emoji_usage': 'moderate'
            },
            'employee': {
                'greeting': "Hello! 👨‍💼",
                'tone': 'technical',
                'formality': 'formal',
                'technical_depth': 'advanced',
                'focus': ['processes', 'regulations', 'compliance', 'internal procedures'],
                'response_length': 'detailed',
                'emoji_usage': 'minimal'
            },
            'admin': {
                'greeting': "Greetings! ⚙️",
                'tone': 'analytical',
                'formality': 'formal',
                'technical_depth': 'expert',
                'focus': ['system metrics', 'performance', 'analytics', 'strategic insights'],
                'response_length': 'comprehensive',
                'emoji_usage': 'minimal'
            }
        }
        
        # Milestone detection patterns
        self.milestone_patterns = {
            'new_listing': [
                r'\b(?:new|added|created|listed)\s+(?:property|listing|home|apartment|villa)\b',
                r'\b(?:just|recently)\s+(?:added|listed|created)\b',
                r'\b(?:property|listing)\s+(?:is|has been)\s+(?:added|listed|created)\b'
            ],
            'deal_closed': [
                r'\b(?:deal|sale|transaction)\s+(?:closed|completed|finalized|sold)\b',
                r'\b(?:sold|closed)\s+(?:the|a)\s+(?:property|deal|transaction)\b',
                r'\b(?:successfully)\s+(?:closed|completed|finalized)\b'
            ],
            'viewing_scheduled': [
                r'\b(?:viewing|showing|appointment)\s+(?:scheduled|booked|arranged)\b',
                r'\b(?:scheduled|booked)\s+(?:a|the)\s+(?:viewing|showing|appointment)\b',
                r'\b(?:client|buyer)\s+(?:wants|requested)\s+(?:to see|viewing)\b'
            ],
            'client_meeting': [
                r'\b(?:meeting|consultation|appointment)\s+(?:with|for)\s+(?:client|customer)\b',
                r'\b(?:met|meeting)\s+(?:with)\s+(?:client|customer|buyer|seller)\b',
                r'\b(?:client|customer)\s+(?:meeting|consultation)\b'
            ]
        }
        
        # African agent recognition patterns
        self.african_patterns = [
            r'\b(?:african|nigeria|ghana|kenya|south africa|ethiopia|uganda|tanzania)\b',
            r'\b(?:nigerian|ghanaian|kenyan|ethiopian|ugandan|tanzanian)\b'
        ]
        
        # Admin panel access patterns
        self.admin_access_patterns = [
            r'\b(?:admin|analytics|dashboard|metrics|system)\s+(?:panel|access|view)\b',
            r'\b(?:show|display|get)\s+(?:analytics|metrics|statistics|data)\b'
        ]

    def process_chat_request(self, message: str, session_id: str, role: str, file_upload: Dict = None) -> Dict[str, Any]:
        """Process chat request with enhanced features"""
        
        # Initialize session if new
        if session_id not in self.user_sessions:
            self.user_sessions[session_id] = {
                'role': role,
                'created_at': datetime.now(),
                'message_count': 0,
                'preferences': {},
                'milestones': defaultdict(int)
            }
        
        # Update session
        self.user_sessions[session_id]['message_count'] += 1
        self.user_sessions[session_id]['last_activity'] = datetime.now()
        
        # Analyze message for milestones and special features
        analysis = self._analyze_message(message, session_id, role)
        
        # Check for admin panel access
        if self._is_admin_access_request(message, role):
            return self._generate_admin_response(session_id)
        
        # Generate personalized response
        response = self._generate_personalized_response(message, session_id, role, analysis, file_upload)
        
        # Update user preferences based on interaction
        self._update_user_preferences(session_id, message, response, role)
        
        return {
            'response': response,
            'analysis': analysis,
            'user_preferences': self.user_sessions[session_id]['preferences'],
            'milestones_detected': analysis.get('milestones', []),
            'session_id': session_id
        }

    def _analyze_message(self, message: str, session_id: str, role: str) -> Dict[str, Any]:
        """Analyze message for milestones, patterns, and special features"""
        analysis = {
            'intent': 'general',
            'sentiment': 'neutral',
            'milestones': [],
            'african_agent_detected': False,
            'admin_access_requested': False
        }
        
        message_lower = message.lower()
        
        # Check for milestone patterns
        for milestone_type, patterns in self.milestone_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    analysis['milestones'].append(milestone_type)
                    self._record_milestone(session_id, milestone_type)
                    break
        
        # Check for African agent patterns
        for pattern in self.african_patterns:
            if re.search(pattern, message_lower):
                analysis['african_agent_detected'] = True
                self._record_african_activity(session_id)
                break
        
        # Check for admin access patterns
        for pattern in self.admin_access_patterns:
            if re.search(pattern, message_lower) and role == 'admin':
                analysis['admin_access_requested'] = True
                break
        
        return analysis

    def _record_milestone(self, session_id: str, milestone_type: str):
        """Record milestone achievement"""
        if session_id not in self.milestone_tracker:
            self.milestone_tracker[session_id] = defaultdict(int)
        
        self.milestone_tracker[session_id][milestone_type] += 1
        self.user_sessions[session_id]['milestones'][milestone_type] += 1

    def _record_african_activity(self, session_id: str):
        """Record African agent activity for special celebration"""
        tracker = self.milestone_tracker[session_id]
        tracker['african_leads'] += 1
        
        # Check if we should celebrate (3+ leads in a day)
        today = datetime.now().date()
        if tracker['last_african_celebration'] != today and tracker['african_leads'] >= 3:
            tracker['last_african_celebration'] = today

    def _generate_personalized_response(self, message: str, session_id: str, role: str, analysis: Dict, file_upload: Dict) -> str:
        """Generate personalized response based on role and analysis"""
        
        personality = self.personalities.get(role, self.personalities['client'])
        
        # Build context for AI
        context = self._build_context(message, session_id, role, analysis, file_upload)
        
        # Generate AI response
        prompt = self._create_prompt(message, context, personality, analysis)
        
        try:
            response = self.model.generate_content(prompt)
            ai_response = response.text
        except Exception as e:
            ai_response = f"I apologize, but I'm having trouble processing your request right now. Please try again."
        
        # Enhance response with personality and milestones
        enhanced_response = self._enhance_response(ai_response, personality, analysis, session_id, role)
        
        return enhanced_response

    def _build_context(self, message: str, session_id: str, role: str, analysis: Dict, file_upload: Dict) -> str:
        """Build context for AI response"""
        context_parts = []
        
        # Add role-specific context
        if role == 'agent':
            context_parts.append("You are a professional real estate agent assistant. Focus on ROI, market trends, and sales techniques.")
        elif role == 'employee':
            context_parts.append("You are an internal employee assistant. Focus on processes, regulations, and compliance.")
        elif role == 'admin':
            context_parts.append("You are a system administrator assistant. Focus on analytics, performance, and strategic insights.")
        else:
            context_parts.append("You are a friendly real estate assistant. Focus on property benefits and lifestyle.")
        
        # Add Dubai market context
        context_parts.append("You have extensive knowledge of Dubai real estate market, including areas like Dubai Marina, Downtown Dubai, Palm Jumeirah, and other popular locations.")
        
        # Add file context if present
        if file_upload:
            context_parts.append(f"User has uploaded a file: {file_upload.get('filename', 'Unknown file')}. Consider this in your response.")
        
        # Add user preferences
        user_prefs = self.user_sessions[session_id].get('preferences', {})
        if user_prefs:
            context_parts.append(f"User preferences: {json.dumps(user_prefs)}")
        
        return " ".join(context_parts)

    def _create_prompt(self, message: str, context: str, personality: Dict, analysis: Dict) -> str:
        """Create AI prompt with personality and context"""
        
        prompt_parts = [
            f"Context: {context}",
            f"Personality: {personality['tone']}, {personality['formality']}, {personality['technical_depth']}",
            f"Response style: {personality['response_length']}, emoji usage: {personality['emoji_usage']}",
            f"Focus areas: {', '.join(personality['focus'])}",
            f"User message: {message}",
            "Provide a helpful, accurate response that matches the personality and context."
        ]
        
        return "\n".join(prompt_parts)

    def _enhance_response(self, ai_response: str, personality: Dict, analysis: Dict, session_id: str, role: str) -> str:
        """Enhance AI response with personality and milestone celebrations"""
        
        enhanced_parts = []
        
        # Add greeting for first message or role change
        if self.user_sessions[session_id]['message_count'] <= 1:
            enhanced_parts.append(personality['greeting'])
        
        # Add milestone celebrations
        for milestone in analysis.get('milestones', []):
            celebration = self._get_milestone_celebration(milestone, role)
            if celebration:
                enhanced_parts.append(celebration)
        
        # Add African agent celebration
        if analysis.get('african_agent_detected'):
            tracker = self.milestone_tracker[session_id]
            if tracker['african_leads'] >= 3 and tracker['last_african_celebration'] == datetime.now().date():
                enhanced_parts.append("🎵 Steadily, we are getting leads! 🎵")
        
        # Add AI response
        enhanced_parts.append(ai_response)
        
        return " ".join(enhanced_parts)

    def _get_milestone_celebration(self, milestone_type: str, role: str) -> str:
        """Get milestone celebration message"""
        celebrations = {
            'new_listing': "🎉 Congratulations on the new listing! This is a great addition to your portfolio.",
            'deal_closed': "💼 Fantastic work on closing that deal! Your negotiation skills are paying off.",
            'viewing_scheduled': "📅 Excellent! Another viewing in the books. This shows great client engagement.",
            'client_meeting': "🤝 Great job on the client meeting! Building those relationships is key."
        }
        
        return celebrations.get(milestone_type, "")

    def _is_admin_access_request(self, message: str, role: str) -> bool:
        """Check if user is requesting admin panel access"""
        if role != 'admin':
            return False
        
        message_lower = message.lower()
        for pattern in self.admin_access_patterns:
            if re.search(pattern, message_lower):
                return True
        return False

    def _generate_admin_response(self, session_id: str) -> str:
        """Generate admin panel response with analytics"""
        
        # Calculate analytics
        total_sessions = len(self.user_sessions)
        total_messages = sum(session['message_count'] for session in self.user_sessions.values())
        
        role_distribution = defaultdict(int)
        for session in self.user_sessions.values():
            role_distribution[session['role']] += 1
        
        # Get recent activity
        recent_activity = []
        for session_id, session in self.user_sessions.items():
            if 'last_activity' in session:
                time_diff = datetime.now() - session['last_activity']
                if time_diff.total_seconds() < 3600:  # Last hour
                    recent_activity.append({
                        'session_id': session_id,
                        'role': session['role'],
                        'message_count': session['message_count'],
                        'last_activity': session['last_activity'].isoformat()
                    })
        
        admin_response = f"""
⚙️ **Admin Analytics Dashboard**

📊 **System Overview:**
- Total active sessions: {total_sessions}
- Total messages processed: {total_messages}
- System status: Healthy ✅

👥 **Role Distribution:**
{chr(10).join([f"- {role.title()}: {count}" for role, count in role_distribution.items()])}

🕒 **Recent Activity (Last Hour):**
{chr(10).join([f"- {activity['role'].title()} session: {activity['message_count']} messages" for activity in recent_activity[:5]])}

🎯 **Milestone Summary:**
{chr(10).join([f"- {milestone}: {count}" for milestone, count in self.milestone_tracker[session_id].items() if count > 0])}

💡 **System Insights:**
- Most active role: {max(role_distribution.items(), key=lambda x: x[1])[0].title() if role_distribution else 'None'}
- Average messages per session: {total_messages / total_sessions if total_sessions > 0 else 0:.1f}
- Peak activity time: {self._get_peak_activity_time()}
        """.strip()
        
        return admin_response

    def _get_peak_activity_time(self) -> str:
        """Get peak activity time based on session data"""
        # This is a simplified implementation
        return "Afternoon (2-5 PM)"

    def _update_user_preferences(self, session_id: str, message: str, response: str, role: str):
        """Update user preferences based on interaction"""
        session = self.user_sessions[session_id]
        
        # Analyze message for preferences
        message_lower = message.lower()
        
        # Property type preferences
        property_types = ['apartment', 'villa', 'townhouse', 'penthouse', 'studio']
        for prop_type in property_types:
            if prop_type in message_lower:
                session['preferences']['property_type'] = prop_type
        
        # Location preferences
        dubai_areas = ['dubai marina', 'downtown dubai', 'palm jumeirah', 'jbr', 'business bay']
        for area in dubai_areas:
            if area in message_lower:
                session['preferences']['preferred_area'] = area
        
        # Budget preferences
        budget_pattern = r'(\d+(?:,\d+)*)\s*(?:aed|dhs|dirhams?)'
        budget_match = re.search(budget_pattern, message_lower)
        if budget_match:
            budget = budget_match.group(1).replace(',', '')
            session['preferences']['budget'] = int(budget)

    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get conversation summary and insights"""
        if session_id not in self.user_sessions:
            return {"error": "Session not found"}
        
        session = self.user_sessions[session_id]
        
        return {
            'session_id': session_id,
            'role': session['role'],
            'message_count': session['message_count'],
            'preferences': session['preferences'],
            'milestones': dict(session['milestones']),
            'created_at': session['created_at'].isoformat(),
            'last_activity': session.get('last_activity', session['created_at']).isoformat()
        }

    def get_user_insights(self, session_id: str) -> Dict[str, Any]:
        """Get user insights and preferences"""
        if session_id not in self.user_sessions:
            return {"error": "Session not found"}
        
        session = self.user_sessions[session_id]
        
        return {
            'session_id': session_id,
            'role': session['role'],
            'preferences': session['preferences'],
            'activity_patterns': {
                'message_count': session['message_count'],
                'session_duration': (datetime.now() - session['created_at']).total_seconds() / 3600,
                'avg_messages_per_hour': session['message_count'] / max(1, (datetime.now() - session['created_at']).total_seconds() / 3600)
            },
            'milestones_achieved': dict(session['milestones'])
        }