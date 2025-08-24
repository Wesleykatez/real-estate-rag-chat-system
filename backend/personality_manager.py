"""
Personality Manager
==================

Manages role-based AI personalities for different user types:
- Client: Friendly, patient, educational, focuses on property benefits and lifestyle
- Agent: Professional, data-driven, market-savvy, emphasizes ROI and market trends
- Employee: Technical, process-oriented, regulatory-focused, internal knowledge
- Admin: Analytical, strategic, system-focused, performance metrics
"""

from typing import Dict, Any, List
from enum import Enum
import json

class UserRole(Enum):
    CLIENT = "client"
    AGENT = "agent"
    EMPLOYEE = "employee"
    ADMIN = "admin"

class PersonalityManager:
    """Manages role-based AI personalities"""
    
    def __init__(self):
        self.personalities = self._load_personalities()
        self.response_lengths = {
            UserRole.CLIENT: "concise",      # 2-3 sentences
            UserRole.AGENT: "detailed",      # 3-4 sentences
            UserRole.EMPLOYEE: "technical",  # 2-3 sentences
            UserRole.ADMIN: "analytical"     # 3-4 sentences
        }
    
    def _load_personalities(self) -> Dict[UserRole, Dict[str, Any]]:
        """Load personality configurations for each role"""
        return {
            UserRole.CLIENT: {
                "tone": "friendly and patient",
                "style": "educational and supportive",
                "focus": ["property benefits", "lifestyle", "value for money", "location advantages"],
                "language": "simple and clear",
                "urgency": "moderate",
                "suggestions": ["property viewings", "neighborhood tours", "financing options"],
                "emojis": ["🏠", "💰", "📍", "✨", "🎯"],
                "greeting": "Hi there! 👋 I'm here to help you find your perfect property in Dubai.",
                "closing": "Would you like me to show you some properties or help with anything else? 😊"
            },
            UserRole.AGENT: {
                "tone": "professional and confident",
                "style": "data-driven and market-savvy",
                "focus": ["ROI", "market trends", "investment potential", "sales strategies"],
                "language": "professional with market terminology",
                "urgency": "high",
                "suggestions": ["market analysis", "investment opportunities", "client leads", "sales techniques"],
                "emojis": ["📊", "💼", "🎯", "📈", "🏢"],
                "greeting": "Welcome! 📊 Ready to boost your real estate success with market insights.",
                "closing": "Need market data or sales strategies? Let's optimize your performance! 💼"
            },
            UserRole.EMPLOYEE: {
                "tone": "technical and process-oriented",
                "style": "regulatory-focused and systematic",
                "focus": ["compliance", "processes", "regulations", "internal procedures"],
                "language": "technical and precise",
                "urgency": "low",
                "suggestions": ["documentation", "compliance checks", "process improvements"],
                "emojis": ["📋", "⚖️", "🔧", "📝", "✅"],
                "greeting": "Hello! 📋 I'm here to assist with internal processes and compliance.",
                "closing": "Need help with documentation or procedures? I'm here to support! 📝"
            },
            UserRole.ADMIN: {
                "tone": "analytical and strategic",
                "style": "system-focused and performance-oriented",
                "focus": ["performance metrics", "system optimization", "strategic insights", "team management"],
                "language": "analytical with data insights",
                "urgency": "moderate",
                "suggestions": ["performance reports", "system improvements", "strategic planning"],
                "emojis": ["📊", "🎯", "⚙️", "📈", "🔍"],
                "greeting": "Welcome! 📊 Ready to optimize your real estate operations with data-driven insights.",
                "closing": "Need performance analytics or strategic guidance? Let's drive results! 📈"
            }
        }
    
    def get_personality(self, role: str) -> Dict[str, Any]:
        """Get personality configuration for a role"""
        try:
            user_role = UserRole(role.lower())
            return self.personalities[user_role]
        except ValueError:
            # Default to client personality
            return self.personalities[UserRole.CLIENT]
    
    def create_role_specific_prompt(self, 
                                  role: str, 
                                  base_prompt: str, 
                                  query_analysis: Dict[str, Any]) -> str:
        """Create a role-specific prompt with personality"""
        
        personality = self.get_personality(role)
        
        # Add role-specific context
        role_context = f"""
You are a Dubai real estate AI assistant with a {personality['tone']} personality.

**Your Style**: {personality['style']}
**Focus Areas**: {', '.join(personality['focus'])}
**Communication**: {personality['language']}
**Response Length**: Keep responses {self.response_lengths[UserRole(role.lower())]} and actionable.

**Key Guidelines**:
- Use {personality['tone']} language
- Focus on {', '.join(personality['focus'][:2])}
- Provide {personality['style']} insights
- Include relevant emojis: {', '.join(personality['emojis'][:3])}
- Suggest next steps: {', '.join(personality['suggestions'][:2])}
- Keep responses concise and actionable
- Use Dubai-specific terminology and context
        """
        
        # Add query-specific guidance
        intent = query_analysis.get('intent', 'general')
        sentiment = query_analysis.get('sentiment', 'neutral')
        
        intent_guidance = self._get_intent_guidance(role, intent, sentiment)
        
        return f"{role_context}\n\n{intent_guidance}\n\n{base_prompt}"
    
    def _get_intent_guidance(self, role: str, intent: str, sentiment: str) -> str:
        """Get role-specific guidance based on intent and sentiment"""
        
        guidance = {
            UserRole.CLIENT: {
                "property_search": "Focus on lifestyle benefits, location advantages, and value for money. Use friendly, encouraging language.",
                "market_inquiry": "Explain market trends in simple terms. Emphasize opportunities and positive aspects.",
                "investment_advice": "Highlight long-term benefits and lifestyle advantages. Use reassuring, educational tone.",
                "confused": "Be extra patient and break down complex information into simple steps. Use encouraging language.",
                "excited": "Match their enthusiasm! Highlight opportunities and next steps. Use positive, energetic language."
            },
            UserRole.AGENT: {
                "property_search": "Focus on ROI potential, market positioning, and sales opportunities. Use professional, confident language.",
                "market_inquiry": "Provide detailed market analysis with specific data points. Emphasize investment opportunities.",
                "investment_advice": "Highlight market trends, ROI projections, and competitive advantages. Use data-driven insights.",
                "confused": "Provide clear, structured information with actionable steps. Use professional, reassuring tone.",
                "excited": "Channel their energy into actionable strategies. Focus on opportunities and next steps."
            },
            UserRole.EMPLOYEE: {
                "property_search": "Focus on compliance requirements, documentation needs, and internal procedures.",
                "market_inquiry": "Provide regulatory context and compliance considerations. Use technical, precise language.",
                "investment_advice": "Highlight legal requirements, documentation needs, and procedural steps.",
                "confused": "Provide step-by-step procedural guidance. Use clear, technical explanations.",
                "excited": "Channel enthusiasm into proper procedures and compliance. Focus on systematic approaches."
            },
            UserRole.ADMIN: {
                "property_search": "Focus on performance metrics, market analysis, and strategic insights.",
                "market_inquiry": "Provide comprehensive market analysis with performance implications.",
                "investment_advice": "Highlight strategic opportunities and performance optimization.",
                "confused": "Provide clear, analytical breakdown with strategic context.",
                "excited": "Channel energy into strategic planning and performance optimization."
            }
        }
        
        try:
            user_role = UserRole(role.lower())
            return guidance[user_role].get(intent, guidance[user_role]["property_search"])
        except ValueError:
            return guidance[UserRole.CLIENT]["property_search"]
    
    def enhance_response_for_role(self, 
                                response: str, 
                                role: str, 
                                query_analysis: Dict[str, Any]) -> str:
        """Enhance response with role-specific personality elements"""
        
        personality = self.get_personality(role)
        
        # Add role-specific elements
        enhanced_response = response
        
        # Add relevant emoji based on content
        if "property" in response.lower() or "home" in response.lower():
            enhanced_response = f"🏠 {enhanced_response}"
        elif "investment" in response.lower() or "roi" in response.lower():
            enhanced_response = f"💰 {enhanced_response}"
        elif "location" in response.lower() or "area" in response.lower():
            enhanced_response = f"📍 {enhanced_response}"
        
        # Add role-specific suggestions
        if personality['suggestions']:
            suggestion = personality['suggestions'][0]
            enhanced_response += f"\n\n💡 **Next Step**: {suggestion}"
        
        # Add role-specific closing
        if role.lower() == "client":
            enhanced_response += f"\n\n{personality['closing']}"
        
        return enhanced_response
    
    def get_smart_suggestions(self, role: str, context: Dict[str, Any]) -> List[str]:
        """Get role-specific smart suggestions based on context"""
        
        personality = self.get_personality(role)
        suggestions = []
        
        if role.lower() == "client":
            if context.get('budget_range'):
                suggestions.append("💰 Show me properties in my budget range")
                suggestions.append("📊 Compare properties side by side")
            if context.get('preferred_locations'):
                suggestions.append("📍 Explore neighborhoods in my preferred areas")
                suggestions.append("🏠 Schedule property viewings")
            suggestions.append("📱 Get market updates and alerts")
            
        elif role.lower() == "agent":
            suggestions.append("📊 View market performance reports")
            suggestions.append("🎯 Find high-potential leads")
            suggestions.append("📈 Analyze investment opportunities")
            suggestions.append("💼 Access sales resources and training")
            
        elif role.lower() == "employee":
            suggestions.append("📋 Review compliance requirements")
            suggestions.append("⚖️ Check regulatory updates")
            suggestions.append("🔧 Access internal procedures")
            suggestions.append("📝 Generate required documentation")
            
        elif role.lower() == "admin":
            suggestions.append("📊 View performance analytics")
            suggestions.append("🎯 Analyze team performance")
            suggestions.append("⚙️ Review system optimization")
            suggestions.append("📈 Generate strategic reports")
        
        return suggestions[:4]  # Limit to 4 suggestions