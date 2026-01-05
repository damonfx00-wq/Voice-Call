"""Test script for Hotel Booking System"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.agent import IntelligentAgent
from app.tools.hotel_tools import HotelTools
from dotenv import load_dotenv

load_dotenv()


def test_hotel_tools():
    """Test hotel booking tools"""
    print("\n" + "="*60)
    print("Testing Hotel Booking Tools")
    print("="*60)
    
    hotel_tools = HotelTools(data_dir="./data")
    
    # Test search rooms
    print("\n1. Searching for rooms (2 guests, check-in: 2026-01-10, check-out: 2026-01-12):")
    result = hotel_tools.search_rooms(
        check_in="2026-01-10",
        check_out="2026-01-12",
        guests=2
    )
    if result["success"]:
        print(f"   Found {result['total_rooms']} available rooms")
        for room in result['rooms']:
            print(f"   - {room['room_type']} ({room['room_id']}): ${room['price_per_night']}/night")
            print(f"     Capacity: {room['capacity']} guests")
            print(f"     Amenities: {', '.join(room['amenities'])}")
    
    # Test book room
    print("\n2. Booking a room:")
    result = hotel_tools.book_room(
        room_id="R102",
        guest_name="John Doe",
        check_in="2026-01-10",
        check_out="2026-01-12",
        guests=2,
        email="john@example.com",
        phone="+1234567890"
    )
    if result["success"]:
        print(f"   ✅ {result['message']}")
        print(f"   Booking ID: {result['booking']['booking_id']}")
        print(f"   Room: {result['booking']['room_type']}")
        print(f"   Nights: {result['booking']['nights']}")
        print(f"   Total Price: ${result['booking']['total_price']}")
        booking_id = result['booking']['booking_id']
        
        # Test get booking
        print("\n3. Retrieving booking details:")
        result = hotel_tools.get_booking(booking_id)
        if result["success"]:
            print(f"   Guest: {result['booking']['guest_name']}")
            print(f"   Email: {result['booking']['email']}")
            print(f"   Room: {result['booking']['room_type']}")
            print(f"   Check-in: {result['booking']['check_in']}")
            print(f"   Check-out: {result['booking']['check_out']}")
            print(f"   Status: {result['booking']['status']}")
        
        # Test list bookings
        print("\n4. Listing all confirmed bookings:")
        result = hotel_tools.list_all_bookings(status="confirmed")
        if result["success"]:
            print(f"   Total confirmed bookings: {result['total_bookings']}")


def test_agent():
    """Test intelligent agent with hotel booking"""
    print("\n" + "="*60)
    print("Testing Hotel Booking Agent")
    print("="*60)
    
    # Check if API key is set
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("\n⚠️  NVIDIA_API_KEY not set in .env file")
        print("   Skipping agent tests")
        return
    
    agent = IntelligentAgent()
    
    # Test 1: Search for rooms
    print("\n1. Agent Test - Room Search:")
    print("   User: 'I need a hotel room for 2 people from January 15 to January 17, 2026'")
    response = agent.chat("I need a hotel room for 2 people from January 15 to January 17, 2026")
    print(f"   Agent: {response}")
    
    # Test 2: Book a specific room
    print("\n2. Agent Test - Make Booking:")
    print("   User: 'Book room R201 for Sarah Johnson from Jan 20 to Jan 22, email sarah@email.com'")
    agent.reset_conversation()
    response = agent.chat("Book room R201 for Sarah Johnson, 2 guests, from 2026-01-20 to 2026-01-22, email sarah@email.com, phone +1234567890")
    print(f"   Agent: {response}")
    
    # Test 3: List bookings
    print("\n3. Agent Test - View Bookings:")
    print("   User: 'Show me all confirmed bookings'")
    agent.reset_conversation()
    response = agent.chat("Show me all confirmed bookings")
    print(f"   Agent: {response}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Hotel Booking System - Test Suite")
    print("="*60)
    
    try:
        # Test hotel tools
        test_hotel_tools()
        
        # Test agent (requires API key)
        test_agent()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
