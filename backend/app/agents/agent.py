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
        
        # System prompt – optimized for fast voice responses
        system_message = {
            "role": "system",
            "content": f"""You are a friendly AI assistant for ABC Hotel helping with room bookings. Current date: {current_date}

KEY RULES:
- Keep responses SHORT (1-2 sentences max) - this is a voice call
- Be conversational and natural
- Parse dates flexibly ("tomorrow", "next Friday", etc.) and convert to YYYY-MM-DD format for tools
- Ask ONE question at a time
- Use tools to check availability and book rooms

BOOKING FLOW (collect info step-by-step):
1. Check-in/out dates → 2. Number of guests → 3. Room type preference → 4. Search availability → 5. Confirm price → 6. Guest details (name, email, phone) → 7. Special requests → 8. Book room

Be helpful, polite, and efficient. Guide users through booking naturally."""
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
                    messages=[{"role": "system", "content": "Provide a brief, conversational response (1-2 sentences) based on the tool results."}] + self.conversation_history,
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
                error_msg = f"Error generating final response: {str(e)}"
                print(error_msg)
                return "I completed the action, but I'm having trouble generating a response. " + str(tool_results[0]['result'] if tool_results else "")

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

