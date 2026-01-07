"""Intelligent Agent that uses MCP tools via NVIDIA API"""
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from app.memory import ConversationMemory
from datetime import datetime

load_dotenv()


class IntelligentAgent:
    """Agent that decides which MCP tool to use based on user requests"""
    
    def __init__(self, api_key: str = None, session_id: Optional[str] = None, 
                 user_id: Optional[str] = None):
        """
        Initialize agent with NVIDIA API and conversation memory
        
        Args:
            api_key: NVIDIA API key (or set NVIDIA_API_KEY env var)
            session_id: Optional session ID to resume conversation
            user_id: Optional user identifier
        """
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        
        # Initialize OpenAI client with NVIDIA base URL
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )
        
        # Use Meta Llama 3.1 8B Instruct - fast and reliable for conversational AI
        self.model = "meta/llama-3.1-8b-instruct"
        
        # Initialize conversation memory
        self.memory = ConversationMemory()
        
        # Store phone number (passed as user_id from frontend)
        self.phone_number = user_id if user_id else None
        
        # STATE TRACKING - Track what info we've collected
        self.collected_info = {
            'has_name': False,
            'has_email': False,
            'has_dates': False,
            'has_preferences': False,
            'has_searched': False,
            'presented_options': False,
            'user_selected_room': False,
            'guest_name': None,
            'email': None,
            'check_in': None,
            'check_out': None,
            'room_type': None,
            'guests': None,
            'selected_room_id': None
        }
        
        # Create or load session
        if session_id:
            self.session_id = session_id
            # Verify session exists
            if not self.memory.get_session(session_id):
                # Session doesn't exist, create new one
                self.session_id = self.memory.create_session(user_id)
        else:
            # Create new session
            self.session_id = self.memory.create_session(user_id)
        
        # Load conversation history from memory
        self.conversation_history = self.memory.get_formatted_history(self.session_id)
        
        # Tool definitions for function calling - Hotel Booking Only
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_hotel_rooms",
                    "description": "Search for available hotel rooms based on criteria like dates, number of guests, room type, and price",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "check_in": {
                                "type": "string",
                                "description": "Check-in date in YYYY-MM-DD format"
                            },
                            "check_out": {
                                "type": "string",
                                "description": "Check-out date in YYYY-MM-DD format"
                            },
                            "guests": {
                                "type": "integer",
                                "description": "Number of guests"
                            },
                            "room_type": {
                                "type": "string",
                                "description": "Type of room (e.g., Standard, Deluxe, Suite)"
                            },
                            "max_price": {
                                "type": "number",
                                "description": "Maximum price per night"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "book_hotel_room",
                    "description": "Book a hotel room for a guest",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "room_id": {
                                "type": "string",
                                "description": "ID of the room to book (e.g., R101, R201)"
                            },
                            "guest_name": {
                                "type": "string",
                                "description": "Name of the guest"
                            },
                            "check_in": {
                                "type": "string",
                                "description": "Check-in date in YYYY-MM-DD format"
                            },
                            "check_out": {
                                "type": "string",
                                "description": "Check-out date in YYYY-MM-DD format"
                            },
                            "guests": {
                                "type": "integer",
                                "description": "Number of guests"
                            },
                            "email": {
                                "type": "string",
                                "description": "Guest email address"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Guest phone number"
                            },
                            "special_requests": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "List of special requests (e.g., Extra bed, Late check-in)"
                            },
                            "bed_type": {
                                "type": "string",
                                "description": "Bed preference (e.g., Single, Double, Twin)"
                            }
                        },
                        "required": ["room_id", "guest_name", "check_in", "check_out", "guests"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_hotel_booking",
                    "description": "Get details of a hotel booking by booking ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_id": {
                                "type": "string",
                                "description": "Booking ID (e.g., BK20260105115810)"
                            }
                        },
                        "required": ["booking_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_hotel_booking",
                    "description": "Cancel a hotel booking",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_id": {
                                "type": "string",
                                "description": "Booking ID to cancel"
                            }
                        },
                        "required": ["booking_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_hotel_bookings",
                    "description": "List all hotel bookings, optionally filtered by status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["confirmed", "cancelled"],
                                "description": "Filter by booking status"
                            }
                        }
                    }
                }
            }
        ]
    
        # Load state from session memory
        session_data = self.memory.get_session(self.session_id)
        saved_state = session_data.get('metadata', {}).get('collected_info', {}) if session_data else {}
        
        # Merge saved state with defaults
        self.collected_info.update(saved_state)

    def update_state_from_history(self, user_message: str):
        """Update state based on conversation history"""
        if not self.conversation_history:
            return
            
        last_ai_msg = ""
        for msg in reversed(self.conversation_history):
            if msg['role'] == 'assistant':
                last_ai_msg = msg['content'].lower()
                break
        
        # Heuristic: If AI asked for X, and User responded, assume X is collected
        if "name" in last_ai_msg and "?" in last_ai_msg:
            self.collected_info['has_name'] = True
        if "email" in last_ai_msg and "?" in last_ai_msg:
            self.collected_info['has_email'] = True
        if ("check" in last_ai_msg or "date" in last_ai_msg or "when" in last_ai_msg) and "?" in last_ai_msg:
            self.collected_info['has_dates'] = True
        if ("type" in last_ai_msg or "preference" in last_ai_msg or "guest" in last_ai_msg) and "?" in last_ai_msg:
            self.collected_info['has_preferences'] = True
            
        # Also check update state based on current user message content (Proactive info)
        user_msg_lower = user_message.lower()
        
        # 1. Proactive Email
        if "@" in user_msg_lower: 
            self.collected_info['has_email'] = True
            
        # 2. Proactive Dates detection (basic keywords)
        if any(w in user_msg_lower for w in ['count', 'check', 'book for', 'nights', 'tomorrow', 'next week', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
            self.collected_info['has_dates'] = True

        # 3. Proactive Name (heuristic: "my name is X" or "I am X")
        if "name is" in user_msg_lower or "i am" in user_msg_lower:
            self.collected_info['has_name'] = True

        # Save updated state
        self.memory.update_metadata(self.session_id, {'collected_info': self.collected_info})

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with validation and state checking
        """
        print(f"\n🔧 Executing tool: {tool_name}")
        print(f"   Arguments: {arguments}")
        
        from app.tools.hotel_tools import HotelTools
        hotel_tools = HotelTools(data_dir=os.getenv("HOTEL_DATA_DIR", "./data"))
        
        result = None
        
        # VALIDATION LAYER - Block invalid tool calls based on STATE
        
        if tool_name == "search_hotel_rooms":
            # BLOCK search if we haven't even asked for dates/preferences
            if not self.collected_info['has_dates'] and not self.collected_info['has_preferences']:
                 result = {"success": False, "error": "SYSTEM BLOCK: You must ASK the user for check-in/out dates before searching. Do not hallucinate dates."}
            else:
                # Validate parameters
                if not arguments.get('check_in') or not arguments.get('check_out'):
                    result = {"success": False, "error": "I need check-in and check-out dates from you to search for rooms. When would you like to stay?"}
                elif not arguments.get('guests'):
                    result = {"success": False, "error": "I need to know how many guests will be staying. How many people?"}
                else:
                    self.collected_info['has_searched'] = True
                    self.memory.update_metadata(self.session_id, {'collected_info': self.collected_info})
                    result = hotel_tools.search_rooms(**arguments)

        elif tool_name == "book_hotel_room":
            # BLOCK booking if we haven't collected basics
            if not self.collected_info['has_name']:
                result = {"success": False, "error": "SYSTEM BLOCK: You must ASK for the guest's name before booking."}
            elif not self.collected_info['has_email']:
                result = {"success": False, "error": "SYSTEM BLOCK: You must ASK for the email before booking."}
            else:
                # STRICT VALIDATION - Block placeholder/invalid data
                guest_name = arguments.get('guest_name', '')
                email = arguments.get('email', '')
                room_id = arguments.get('room_id', '')
                check_in = arguments.get('check_in', '')
                check_out = arguments.get('check_out', '')
                
                # Check for placeholder/invalid names
                invalid_names = ['unknown', 'your name', 'guest', 'user', 'john', 'sarah', 'test', '']
                if not guest_name or guest_name.lower() in invalid_names:
                    result = {"success": False, "error": "I don't have your name yet. May I have your name, please?"}
                
                # Check for placeholder/invalid emails
                elif not email or email.lower() in ['unknown', 'your email', 'test@test.com', 'john@test.com', ''] or '@' not in email:
                    result = {"success": False, "error": "I need your email address. What's your email?"}
                
                # Check for valid room ID
                elif not room_id or room_id.lower() in ['unknown', ''] or not room_id.startswith('R'):
                    result = {"success": False, "error": "I need you to select a room from the options I presented. Which room would you like?"}
                
                # Check for valid dates
                elif not check_in or check_in.lower() in ['unknown', ''] or len(check_in) != 10:
                    result = {"success": False, "error": "I need your check-in date. When would you like to check in?"}
                elif not check_out or check_out.lower() in ['unknown', ''] or len(check_out) != 10:
                    result = {"success": False, "error": "I need your check-out date. When would you like to check out?"}
                
                # All validation passed - proceed with booking
                else:
                    result = hotel_tools.book_room(**arguments)
            
        elif tool_name == "get_hotel_booking":
            result = hotel_tools.get_booking(**arguments)
        elif tool_name == "cancel_hotel_booking":
            result = hotel_tools.cancel_booking(**arguments)
        elif tool_name == "list_hotel_bookings":
            result = hotel_tools.list_all_bookings(**arguments)
        else:
            result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
        # Log result
        if result:
            if tool_name == "search_hotel_rooms" and result.get('success'):
                 summary = {k: v for k, v in result.items() if k != 'rooms'}
                 summary['rooms_found'] = len(result.get('rooms', []))
                 print(f"   ► Tool Result: {summary}")
            else:
                 print(f"   ► Tool Result: {result}")
        else:
            print("   ► Tool Result: None (Error!)")
            
        return result
    
    def chat(self, user_message: str, stream: bool = False) -> str:
        """
        Process user message and decide which tools to use
        
        Args:
            user_message: User's message
            stream: Whether to stream the response
            
        Returns:
            Agent's response
        """
        # Load conversation history
        session_data = self.memory.get_session(self.session_id)
        if session_data:
            self.conversation_history = session_data.get('conversation_history', [])
        else:
            self.conversation_history = []
            
        # Update state based on previous turn + new message
        self.update_state_from_history(user_message)
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Save user message to memory
        self.memory.add_message(self.session_id, "user", user_message)
        
        # Get current date for relative date calculation
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # System prompt – optimized for fast voice responses
        phone_info = f"Phone number: {self.phone_number}" if self.phone_number else "Phone number: Not provided"
        
        system_message = {
            "role": "system",
            "content": f"""You are a friendly AI assistant for ABC Hotel helping with room bookings. Current date: {current_date}
{phone_info}

🚫 CRITICAL RULES - NEVER VIOLATE:
1. ONLY use information the user ACTUALLY provides in THIS conversation
2. NEVER use example names like "John", "Sarah", or "R112" 
3. NEVER book without collecting: name, email, dates from the USER
4. NEVER search without dates from the USER
5. NEVER choose a room - USER must select
6. If you don't have information, ASK for it - don't assume or use examples

✅ MANDATORY FLOW (ASK EACH QUESTION):
Step 1: "Welcome to ABC Hotel! How can I help you today?"
Step 2: IF booking → "May I have your name, please?"
Step 3: WAIT for name → "And your email address?"
Step 4: WAIT for email → "When would you like to check in and check out?"
Step 5: WAIT for dates → "What type of room? Standard, Deluxe, or Suite?"
Step 6: WAIT for preference → SEARCH with search_hotel_rooms
Step 7: PRESENT results → "I found: Option 1: [details], Option 2: [details]. Which one?"
Step 8: WAIT for selection → "Shall I book [room ID]?"
Step 9: WAIT for confirmation → BOOK with book_hotel_room
Step 10: Confirm booking

🛑 BEFORE CALLING ANY TOOL:
- search_hotel_rooms: Must have dates from user (not examples)
- book_hotel_room: Must have name, email, dates, room_id from user (not examples)

VALIDATION CHECKLIST:
Before booking, verify you collected from the USER:
✓ Name: Not empty, not "John", not example
✓ Email: Has @, not "john@test.com", not example  
✓ Dates: From user, not "tomorrow" without parsing
✓ Room ID: User selected from search results
✓ Phone: {self.phone_number} (system provided)

If ANY field is missing or is an example value:
- DO NOT call the tool
- ASK the user for the real information

KEY RULES:
- Keep responses SHORT (1-2 sentences max) - this is a voice call
- Be warm, conversational and natural
- Parse dates flexibly ("tomorrow", "next Friday", etc.) and convert to YYYY-MM-DD format for tools
- Ask ONE question at a time
- ALWAYS use the guest's name throughout the conversation (once they provide it)
- NEVER use placeholder or example data

SMART FILTERING:
- We have 200 rooms, so ALWAYS ask about preferences BEFORE searching
- Ask: "What's your budget range?" or "Standard, Deluxe, or Suite?" or "How many guests?"
- Use their answers to filter with search_hotel_rooms (use room_type, max_price, guests parameters)
- Present ONLY the top 2-3 matches, not all results
- Keep it simple: room type, price, ONE key feature

HANDLING DIFFERENT REQUESTS:
- **IF USER ASKS GENERAL QUESTION** (hours, amenities, location, etc.):
  - Answer their question briefly and helpfully
  - Then ask: "Is there anything else I can help you with?"
  - Don't collect name/email unless they want to book
  
- **IF USER WANTS TO BOOK**:
  - MUST collect: name → email → dates → preferences → search → present options
  - NEVER skip any step
  - NEVER book without ALL required information

CRITICAL - BEFORE BOOKING VALIDATION:
🛑 STOP! Before calling book_hotel_room, you MUST verify:
1. guest_name is NOT "your name", "user", "guest", or any placeholder
2. email contains "@" symbol and looks like a real email
3. phone is from system variable: "{self.phone_number}"
4. check_in and check_out are in YYYY-MM-DD format
5. check_in date is before check_out date
6. guests is a number (1, 2, 3, etc.)
7. room_id is from the search results (e.g., "R101", "R205")

If ANY field is missing, placeholder, or invalid:
- DO NOT call book_hotel_room
- ASK the user for the missing/invalid information
- Be polite: "I need your [name/email/dates] to complete the booking"

IMPORTANT:
- **START WITH: "How can I help you today?"** - Let user state their intent first
- **COLLECT NAME & EMAIL ONLY FOR BOOKINGS** - Don't ask if they're just inquiring
- **USE THEIR NAME** - Once collected, say their name in every response
- **FILTER INTELLIGENTLY** - Ask preferences to narrow down from 200 rooms
- **PRESENT 2-3 OPTIONS MAX** - Don't overwhelm with all room details
- **CONFIRM BEFORE BOOKING** - Get explicit "yes" before calling book_hotel_room
- **ALWAYS USE PHONE: "{self.phone_number}"** - This is the caller's phone number, use it in ALL bookings
- Never ask for phone number - it's already captured

ERROR HANDLING:
- If search returns too many results: Ask more specific preferences
- If search returns no results: Suggest alternative dates or room types
- If booking fails: "Let me try that again for you, [Name]"
- Never expose technical errors

Be warm, use their name often, and make it feel like a personal concierge service."""
        }
        
        messages = [system_message] + self.conversation_history
        
        try:
            # Make API call with function calling
            # Adjust model parameters for concise, smart replies
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=150,  # Shorter for faster voice responses
                stream=stream
            )
            
            if stream:
                return self._handle_streaming_response(response)
            else:
                return self._handle_response(response)
                
        except Exception as e:
            # Log the error for debugging
            print(f"Error calling NVIDIA API: {str(e)}")
            
            # Provide user-friendly error message
            user_friendly_msg = "I'm having a bit of trouble right now. Let me try that again for you."
            self.conversation_history.append({
                "role": "assistant",
                "content": user_friendly_msg
            })
            # Save user-friendly message to memory
            self.memory.add_message(self.session_id, "assistant", user_friendly_msg)
            return user_friendly_msg
    
    def _handle_response(self, response) -> str:
        """Handle non-streaming response"""
        assistant_message = response.choices[0].message
        
        # Check if tool calls are needed
        if assistant_message.tool_calls:
            # Execute tool calls
            tool_results = []
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as e:
                    print(f"Error parsing tool arguments: {e}")
                    arguments = {}
                    # Optionally return an error to the model
                
                print(f"\n🔧 Executing tool: {tool_name}")
                print(f"   Arguments: {json.dumps(arguments, indent=2)}")
                
                result = self.execute_tool(tool_name, arguments)
                tool_results.append({
                    "tool": tool_name,
                    "result": result
                })
                
                # Add tool call and result to conversation
                self.conversation_history.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
            
            try:
                # Get final response with tool results
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{
                        "role": "system", 
                        "content": "Provide a brief, conversational response (1-2 sentences) based on the tool results. If the tool returned an error, handle it gracefully without exposing technical details. Offer to help in a different way or ask the user to try again."
                    }] + self.conversation_history,
                    temperature=0.7,
                    max_tokens=150  # Keep responses short for voice
                )
                
                final_content = final_response.choices[0].message.content
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_content
                })
                
                # Save assistant response to memory
                self.memory.add_message(self.session_id, "assistant", final_content)
                
                return final_content
            except Exception as e:
                # Log error for debugging
                print(f"Error generating final response: {str(e)}")
                
                # Provide graceful fallback based on tool results
                if tool_results and tool_results[0]['result'].get('success'):
                    fallback_msg = "I've completed that for you. Is there anything else I can help with?"
                else:
                    fallback_msg = "Let me check that for you again. Could you please repeat your request?"
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": fallback_msg
                })
                self.memory.add_message(self.session_id, "assistant", fallback_msg)
                return fallback_msg


        else:
            # No tool calls, just return the response
            content = assistant_message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": content
            })
            # Save assistant response to memory
            self.memory.add_message(self.session_id, "assistant", content)
            return content
    
    def _handle_streaming_response(self, response) -> str:
        """Handle streaming response"""
        full_response = ""
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end="", flush=True)
        
        print()  # New line after streaming
        
        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })
        
        # Save assistant response to memory
        self.memory.add_message(self.session_id, "assistant", full_response)
        
        return full_response
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        # Clear memory storage
        self.memory.clear_history(self.session_id)
    
    def get_session_id(self) -> str:
        """Get the current session ID"""
        return self.session_id
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get session information"""
        return self.memory.get_session(self.session_id)

