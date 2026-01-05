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
        
        self.model = "openai/gpt-oss-120b"
        
        # Initialize conversation memory
        self.memory = ConversationMemory()
        
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
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a hotel booking tool
        """
        from app.tools.hotel_tools import HotelTools
        
        hotel_tools = HotelTools(data_dir=os.getenv("HOTEL_DATA_DIR", "./data"))
        
        if tool_name == "search_hotel_rooms":
            return hotel_tools.search_rooms(**arguments)
        elif tool_name == "book_hotel_room":
            return hotel_tools.book_room(**arguments)
        elif tool_name == "get_hotel_booking":
            return hotel_tools.get_booking(**arguments)
        elif tool_name == "cancel_hotel_booking":
            return hotel_tools.cancel_booking(**arguments)
        elif tool_name == "list_hotel_bookings":
            return hotel_tools.list_all_bookings(**arguments)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    def chat(self, user_message: str, stream: bool = False) -> str:
        """
        Process user message and decide which tools to use
        
        Args:
            user_message: User's message
            stream: Whether to stream the response
            
        Returns:
            Agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Save user message to memory
        self.memory.add_message(self.session_id, "user", user_message)
        
        # Get current date for relative date calculation
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # System prompt – detailed behavior per user request
        system_message = {
            "role": "system",
            "content": f"""You are an intelligent, polite, and professional AI call bot for HotelHub AI. Your goal is to help guests book a room by collecting all necessary details, checking availability, and confirming the booking.

CURRENT DATE: {current_date}

DATE PARSING INSTRUCTIONS:
- Users may provide dates in diverse formats (e.g., "next Friday", "tomorrow", "March 10th", "3 days from now", "12/05/2026").
- You MUST interpret these phrases relative to the CURRENT DATE ({current_date}).
- When calling tools (search_hotel_rooms, book_hotel_room), ALWAYS convert these dates to the specific "YYYY-MM-DD" format.
- Do NOT ask the user to reformat the date if you can understand it.

BEHAVIOR:
- Polite, Clear, Patient, Professional, Helpful.
- Keep answers concise and spoken-style.

CONVERSATION FLOW:
1. GREETING: "Hello, thank you for calling HotelHub AI. This is your automated booking assistant. How may I help you today?"
2. IDENTIFY INTENT: Confirm booking intent (e.g., "Sure, I can help you with a room reservation.").
3. COLLECT DATES:
   - Ask for Check-in Date.
   - Ask for Check-out Date.
   - Confirm calculated number of nights.
4. GUESTS:
   - Ask for number of Adults.
   - Ask for Children (and ages if yes).
5. ROOM PREFERENCE:
   - Offer options (Standard, Deluxe, Suite).
   - If unsure, explain differences.
6. BED PREFERENCE:
   - Ask: "Do you prefer a single bed, double bed, or twin beds?"
7. SEARCH & PRICE:
   - Use 'search_hotel_rooms' tool to check availability.
   - State the room price clearly (including breakfast if applicable).
   - Ask for price acceptance: "The [Room Type] costs $[Price] per night... Is this acceptable?"
8. SPECIAL REQUESTS:
   - Ask: "Do you have any special requests, such as Extra bed, Late check-in, Airport pickup, Non-smoking room?"
   - Note them down.
9. GUEST DETAILS:
   - Ask for Full Name.
   - Ask for Contact Number.
   - Ask for Email Address (and repeat to confirm).
10. PAYMENT:
    - State: "To confirm the booking, we require a credit card or advance payment." or "You can pay during check-in."
11. SUMMARY:
    - Summarize: Dates, Room, Guests, Total Price.
    - Ask: "Is everything correct?"
12. CONFIRMATION:
    - Use 'book_hotel_room' tool.
    - If successful: "Your booking has been successfully confirmed..."
    - If unavailable: "I'm sorry, the selected room is not available. Would you like to choose another option?"
13. CLOSING: "Thank you for choosing HotelHub AI. Have a wonderful day!"

ERROR HANDLING:
- Silence: "Are you still there? Please let me know if you need assistance."
- Anger: "I’m sorry for the inconvenience. I’m here to help you."
- Misunderstanding: "I apologize, could you please repeat that?"

TRANSFER OPTION:
- If requested or complex issue: "Would you like me to connect you to a hotel representative?"

Always maintain this flow and guide the user politely. Use the tools when appropriate (search_hotel_rooms for checking availability/price, book_hotel_room for final confirmation)."""
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
                temperature=0.6,
                max_tokens=1024,
                stream=stream
            )
            
            if stream:
                return self._handle_streaming_response(response)
            else:
                return self._handle_response(response)
                
        except Exception as e:
            error_msg = f"Error calling NVIDIA API: {str(e)}"
            self.conversation_history.append({
                "role": "assistant",
                "content": error_msg
            })
            # Save error to memory
            self.memory.add_message(self.session_id, "assistant", error_msg)
            return error_msg
    
    def _handle_response(self, response) -> str:
        """Handle non-streaming response"""
        assistant_message = response.choices[0].message
        
        # Check if tool calls are needed
        if assistant_message.tool_calls:
            # Execute tool calls
            tool_results = []
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
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
            
            # Get final response with tool results
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Summarize the results"}] + self.conversation_history,
                temperature=0.7,
                max_tokens=4096
            )
            
            final_content = final_response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": final_content
            })
            
            # Save assistant response to memory
            self.memory.add_message(self.session_id, "assistant", final_content)
            
            return final_content
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

