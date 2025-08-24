"""
AI Enhancement Manager
=====================

Main manager that integrates all AI enhancement modules:
- Conversation Memory Management
- Query Understanding
- Response Enhancement
- Context Optimization
- Multi-modal Processing
"""

import json
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, text
from datetime import datetime

from ai_enhancements import ConversationMemory, MessageType
from query_understanding import QueryUnderstanding
from response_enhancer import ResponseEnhancer
from personality_manager import PersonalityManager

logger = logging.getLogger(__name__)

class AIEnhancementManager:
    """Main manager for all AI enhancements"""
    
    def __init__(self, db_url: str, model):
        self.engine = create_engine(db_url)
        self.model = model
        self.response_enhancer = ResponseEnhancer(model)
        self.personality_manager = PersonalityManager()
        
        # Cache for conversation memories
        self.memory_cache = {}
    
    def process_chat_request(self, 
                           message: str,
                           session_id: str,
                           role: str,
                           file_upload: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a complete chat request with all enhancements"""
        
        try:
            # Get or create conversation memory
            memory = self._get_conversation_memory(session_id)
            
            # Add user message to memory
            message_type = MessageType.DOCUMENT if file_upload else MessageType.TEXT
            memory.add_message('user', message, message_type, file_upload)
            
            # Process file upload if present
            file_analysis = None
            if file_upload:
                file_analysis = self._process_file_upload(file_upload)
            
            # Analyze query
            conversation_history = list(memory.messages)
            query_understanding = QueryUnderstanding.analyze(message, conversation_history)
            
            # Get user preferences
            user_preferences = memory.get_user_preferences()
            
            # Get conversation context
            recent_context = memory.get_recent_context(10)
            
            # Create enhanced prompt with personality
            enhanced_prompt = self._create_enhanced_prompt(
                message=message,
                query_understanding=query_understanding,
                user_preferences=user_preferences,
                conversation_history=recent_context,
                file_analysis=file_analysis,
                role=role
            )
            
            # Generate base response
            try:
                response = self.model.generate_content(enhanced_prompt)
                base_response = response.text
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                base_response = "I'm having trouble processing your request right now. Please try again in a moment."
            
            # Enhance response with personality
            enhanced_response = self.response_enhancer.enhance_response(
                base_response=base_response,
                query_understanding=query_understanding,
                user_preferences=user_preferences,
                conversation_history=recent_context
            )
            
            # Apply role-specific personality enhancements
            enhanced_response = self.personality_manager.enhance_response_for_role(
                response=enhanced_response,
                role=role,
                query_analysis=query_understanding.__dict__
            )
            
            # Add AI response to memory
            memory.add_message('assistant', enhanced_response, MessageType.TEXT)
            
            # Update memory cache
            self.memory_cache[session_id] = memory
            
            return {
                'response': enhanced_response,
                'query_analysis': {
                    'intent': query_understanding.intent,
                    'sentiment': query_understanding.sentiment.value,
                    'urgency_level': query_understanding.urgency_level,
                    'complexity_level': query_understanding.complexity_level,
                    'suggested_actions': query_understanding.suggested_actions,
                    'entities': query_understanding.entities
                },
                'user_preferences': user_preferences,
                'file_analysis': file_analysis,
                'conversation_id': memory.conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error in AI enhancement manager: {e}")
            return {
                'response': "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
                'query_analysis': {
                    'intent': 'general_inquiry',
                    'sentiment': 'neutral',
                    'urgency_level': 1,
                    'complexity_level': 1,
                    'suggested_actions': [],
                    'entities': {}
                },
                'user_preferences': {},
                'file_analysis': None,
                'conversation_id': None
            }
    
    def _get_conversation_memory(self, session_id: str) -> ConversationMemory:
        """Get or create conversation memory for a session"""
        if session_id in self.memory_cache:
            return self.memory_cache[session_id]
        
        # Try to load from database
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id FROM conversations 
                    WHERE session_id = :session_id AND is_active = TRUE
                """), {"session_id": session_id})
                row = result.fetchone()
                
                memory = ConversationMemory(session_id=session_id)
                if row:
                    memory.conversation_id = row[0]
                    
                    # Load recent messages
                    messages_result = conn.execute(text("""
                        SELECT role, content, message_type, metadata, created_at
                        FROM messages 
                        WHERE conversation_id = :conversation_id
                        ORDER BY created_at DESC 
                        LIMIT 20
                    """), {"conversation_id": row[0]})
                    
                    for msg_row in messages_result:
                        memory.add_message(
                            role=msg_row[0],
                            content=msg_row[1],
                            message_type=MessageType(msg_row[2]),
                            metadata=json.loads(msg_row[3]) if msg_row[3] else None
                        )
                
                self.memory_cache[session_id] = memory
                return memory
                
        except Exception as e:
            logger.error(f"Error loading conversation memory: {e}")
            memory = ConversationMemory(session_id=session_id)
            self.memory_cache[session_id] = memory
            return memory
    
    def _process_file_upload(self, file_upload: Dict) -> Optional[Dict]:
        """Process file upload for analysis"""
        try:
            file_type = file_upload.get('content_type', '')
            
            if file_type.startswith('image/'):
                # For now, return basic image analysis
                return {
                    "file_type": "image",
                    "analysis": "Image uploaded for property analysis",
                    "supported": True
                }
            
            elif file_type in ['application/pdf', 'text/plain', 'application/msword']:
                # For now, return basic document analysis
                return {
                    "file_type": "document",
                    "analysis": "Document uploaded for analysis",
                    "supported": True
                }
            
            else:
                return {
                    "error": f"Unsupported file type: {file_type}",
                    "supported_types": ["image/*", "application/pdf", "text/plain", "application/msword"]
                }
                
        except Exception as e:
            logger.error(f"Error processing file upload: {e}")
            return {"error": str(e)}
    
    def _create_enhanced_prompt(self,
                               message: str,
                               query_understanding: QueryUnderstanding,
                               user_preferences: Dict[str, Any],
                               conversation_history: List[Dict],
                               file_analysis: Optional[Dict] = None,
                               role: str = "client") -> str:
        """Create an enhanced prompt with all context and analysis"""
        
        prompt_parts = []
        
        # Use personality manager to create role-specific prompt
        base_prompt = f"""
You are an expert Dubai real estate AI assistant with deep knowledge of:
- Dubai property market trends and prices
- Real estate regulations and legal requirements
- Investment opportunities and ROI analysis
- Neighborhood information and amenities
- Golden Visa and residency requirements
- Property development and construction quality

You provide personalized, accurate, and helpful responses based on user preferences and conversation history.
Always use Dubai-specific terminology and provide practical, actionable advice.

Current Query: {message}
        """
        
        # Get role-specific prompt from personality manager
        enhanced_prompt = self.personality_manager.create_role_specific_prompt(
            role=role,
            base_prompt=base_prompt,
            query_analysis=query_understanding.__dict__
        )
        
        return enhanced_prompt
        
        # User preferences context
        if user_preferences:
            preferences_text = "User Preferences:\n"
            if user_preferences.get('budget_range'):
                preferences_text += f"- Budget: AED {user_preferences['budget_range'][0]:,.0f} - {user_preferences['budget_range'][1]:,.0f}\n"
            if user_preferences.get('preferred_locations'):
                preferences_text += f"- Preferred Locations: {', '.join(user_preferences['preferred_locations'])}\n"
            if user_preferences.get('property_types'):
                preferences_text += f"- Property Types: {', '.join(user_preferences['property_types'])}\n"
            if user_preferences.get('bedrooms'):
                preferences_text += f"- Bedrooms: {user_preferences['bedrooms']}\n"
            if user_preferences.get('bathrooms'):
                preferences_text += f"- Bathrooms: {user_preferences['bathrooms']}\n"
            
            prompt_parts.append(preferences_text)
        
        # Query analysis context
        prompt_parts.append(f"""
Query Analysis:
- Intent: {query_understanding.intent}
- Sentiment: {query_understanding.sentiment.value}
- Urgency Level: {query_understanding.urgency_level}/5
- Complexity Level: {query_understanding.complexity_level}/5
- Requires Follow-up: {query_understanding.requires_follow_up}
- Extracted Entities: {json.dumps(query_understanding.entities, indent=2)}
        """)
        
        # File analysis context
        if file_analysis:
            prompt_parts.append(f"""
File Analysis:
{json.dumps(file_analysis, indent=2)}
        """)
        
        # Conversation history context
        if conversation_history:
            history_text = "Recent Conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role_emoji = "👤" if msg['role'] == 'user' else "🤖"
                content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                history_text += f"{role_emoji} {msg['role'].title()}: {content_preview}\n"
            prompt_parts.append(history_text)
        
        # Current query
        prompt_parts.append(f"""
Current Query: {message}

Please provide a comprehensive, personalized response that:
1. Addresses the specific intent and sentiment
2. Uses the user's preferences when relevant
3. Incorporates file analysis if provided
4. Maintains conversation continuity
5. Suggests relevant next steps
6. Uses Dubai-specific terminology and context
7. Provides practical, actionable advice
8. Includes specific Dubai market insights when relevant
        """)
        
        return "\n\n".join(prompt_parts)
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation for a session"""
        try:
            memory = self._get_conversation_memory(session_id)
            
            # Extract key information from conversation
            user_messages = [msg for msg in memory.messages if msg['role'] == 'user']
            assistant_messages = [msg for msg in memory.messages if msg['role'] == 'assistant']
            
            # Get user preferences
            user_preferences = memory.get_user_preferences()
            
            # Analyze conversation topics
            topics = self._extract_conversation_topics(memory.messages)
            
            return {
                'session_id': session_id,
                'conversation_id': memory.conversation_id,
                'message_count': len(memory.messages),
                'user_messages': len(user_messages),
                'assistant_messages': len(assistant_messages),
                'user_preferences': user_preferences,
                'topics': topics,
                'last_updated': memory.last_updated.isoformat(),
                'duration': self._calculate_conversation_duration(memory.messages)
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {
                'session_id': session_id,
                'error': str(e)
            }
    
    def _extract_conversation_topics(self, messages: List[Dict]) -> List[str]:
        """Extract main topics from conversation"""
        topics = []
        all_content = " ".join([msg['content'].lower() for msg in messages])
        
        topic_keywords = {
            'property_search': ['property', 'apartment', 'villa', 'house', 'buy', 'rent', 'search'],
            'investment': ['investment', 'roi', 'return', 'profit', 'yield', 'golden visa'],
            'market_analysis': ['market', 'trend', 'price', 'analysis', 'forecast'],
            'legal_questions': ['legal', 'regulation', 'rera', 'law', 'documentation'],
            'area_information': ['area', 'neighborhood', 'location', 'amenities', 'schools'],
            'financing': ['mortgage', 'financing', 'payment', 'budget', 'loan']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_content for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _calculate_conversation_duration(self, messages: List[Dict]) -> str:
        """Calculate the duration of the conversation"""
        if len(messages) < 2:
            return "0 minutes"
        
        try:
            first_message = messages[0]
            last_message = messages[-1]
            
            first_time = datetime.fromisoformat(first_message['timestamp'])
            last_time = datetime.fromisoformat(last_message['timestamp'])
            
            duration = last_time - first_time
            minutes = int(duration.total_seconds() / 60)
            
            if minutes < 60:
                return f"{minutes} minutes"
            else:
                hours = minutes // 60
                remaining_minutes = minutes % 60
                return f"{hours} hours {remaining_minutes} minutes"
                
        except Exception:
            return "Unknown duration"
    
    def clear_conversation_memory(self, session_id: str) -> bool:
        """Clear conversation memory for a session"""
        try:
            if session_id in self.memory_cache:
                del self.memory_cache[session_id]
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation memory: {e}")
            return False
    
    def get_user_insights(self, session_id: str) -> Dict[str, Any]:
        """Get insights about the user based on conversation history"""
        try:
            memory = self._get_conversation_memory(session_id)
            user_preferences = memory.get_user_preferences()
            
            # Analyze user behavior
            user_messages = [msg for msg in memory.messages if msg['role'] == 'user']
            
            insights = {
                'preferences': user_preferences,
                'engagement_level': self._calculate_engagement_level(user_messages),
                'primary_interests': self._identify_primary_interests(user_messages),
                'urgency_pattern': self._analyze_urgency_pattern(user_messages),
                'complexity_preference': self._analyze_complexity_preference(user_messages)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting user insights: {e}")
            return {'error': str(e)}
    
    def _calculate_engagement_level(self, user_messages: List[Dict]) -> str:
        """Calculate user engagement level"""
        if not user_messages:
            return "new_user"
        
        avg_message_length = sum(len(msg['content']) for msg in user_messages) / len(user_messages)
        
        if avg_message_length > 100:
            return "highly_engaged"
        elif avg_message_length > 50:
            return "engaged"
        else:
            return "casual"
    
    def _identify_primary_interests(self, user_messages: List[Dict]) -> List[str]:
        """Identify user's primary interests"""
        interests = []
        all_content = " ".join([msg['content'].lower() for msg in user_messages])
        
        interest_patterns = {
            'investment': ['investment', 'roi', 'return', 'profit', 'golden visa'],
            'family_living': ['family', 'schools', 'children', 'kids', 'playground'],
            'luxury': ['luxury', 'premium', 'high-end', 'exclusive', 'penthouse'],
            'budget_conscious': ['budget', 'affordable', 'cheap', 'economical'],
            'location_focused': ['location', 'area', 'neighborhood', 'community']
        }
        
        for interest, keywords in interest_patterns.items():
            if any(keyword in all_content for keyword in keywords):
                interests.append(interest)
        
        return interests
    
    def _analyze_urgency_pattern(self, user_messages: List[Dict]) -> str:
        """Analyze user's urgency pattern"""
        urgent_keywords = ['urgent', 'asap', 'immediately', 'quick', 'fast', 'now', 'soon']
        
        urgent_count = 0
        for msg in user_messages:
            if any(keyword in msg['content'].lower() for keyword in urgent_keywords):
                urgent_count += 1
        
        if urgent_count > len(user_messages) * 0.5:
            return "high_urgency"
        elif urgent_count > 0:
            return "moderate_urgency"
        else:
            return "low_urgency"
    
    def _analyze_complexity_preference(self, user_messages: List[Dict]) -> str:
        """Analyze user's complexity preference"""
        complex_keywords = ['detailed', 'explain', 'how', 'what', 'why', 'process', 'requirements']
        simple_keywords = ['simple', 'basic', 'overview', 'summary']
        
        complex_count = sum(1 for msg in user_messages 
                          if any(keyword in msg['content'].lower() for keyword in complex_keywords))
        simple_count = sum(1 for msg in user_messages 
                          if any(keyword in msg['content'].lower() for keyword in simple_keywords))
        
        if complex_count > simple_count:
            return "detailed_explanations"
        elif simple_count > complex_count:
            return "simple_overviews"
        else:
            return "balanced"
