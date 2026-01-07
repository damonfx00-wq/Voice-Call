"""Script to create 20 sample bookings for testing the admin dashboard"""
import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.hotel_tools import HotelTools

# Sample guest names
GUEST_NAMES = [
    "John Smith", "Sarah Johnson", "Mike Chen", "Emily Davis",
    "David Wilson", "Lisa Anderson", "James Taylor", "Maria Garcia",
    "Robert Brown", "Jennifer Martinez", "William Jones", "Jessica Miller",
    "Michael Davis", "Ashley Rodriguez", "Christopher Lee", "Amanda White",
    "Daniel Harris", "Melissa Clark", "Matthew Lewis", "Stephanie Walker"
]

# Sample emails
def generate_email(name):
    """Generate email from name"""
    first, last = name.lower().split()
    return f"{first}.{last}@email.com"

# Sample phone numbers
def generate_phone():
    """Generate random phone number"""
    return f"555{random.randint(1000000, 9999999)}"

def create_sample_bookings():
    """Create 20 sample bookings"""
    hotel_tools = HotelTools(data_dir="./data")
    
    # Get today's date
    today = datetime.now()
    
    print("🏨 Creating 20 sample bookings...\n")
    
    successful_bookings = 0
    failed_bookings = 0
    
    for i in range(20):
        guest_name = GUEST_NAMES[i]
        email = generate_email(guest_name)
        phone = generate_phone()
        
        # Random check-in date (today to 7 days from now)
        check_in_offset = random.randint(0, 7)
        check_in_date = today + timedelta(days=check_in_offset)
        
        # Random stay duration (1-5 nights)
        nights = random.randint(1, 5)
        check_out_date = check_in_date + timedelta(days=nights)
        
        # Format dates
        check_in = check_in_date.strftime('%Y-%m-%d')
        check_out = check_out_date.strftime('%Y-%m-%d')
        
        # Random number of guests (1-4)
        guests = random.randint(1, 4)
        
        # Search for available rooms
        search_result = hotel_tools.search_rooms(
            check_in=check_in,
            check_out=check_out,
            guests=guests
        )
        
        if search_result['success'] and search_result['rooms']:
            # Pick a random available room
            room = random.choice(search_result['rooms'])
            room_id = room['room_id']
            
            # Random bed type
            bed_types = ['King', 'Queen', 'Twin', 'Double']
            bed_type = random.choice(bed_types)
            
            # Random special requests
            special_requests_options = [
                [],
                ['Late check-in'],
                ['Early check-out'],
                ['Extra towels'],
                ['Late check-in', 'Extra pillows'],
                ['Ocean view preferred']
            ]
            special_requests = random.choice(special_requests_options)
            
            # Book the room
            booking_result = hotel_tools.book_room(
                room_id=room_id,
                guest_name=guest_name,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                email=email,
                phone=phone,
                special_requests=special_requests,
                bed_type=bed_type
            )
            
            if booking_result['success']:
                successful_bookings += 1
                booking = booking_result['booking']
                print(f"✅ Booking {successful_bookings}/20: {guest_name}")
                print(f"   Room: {room_id} ({room['room_type']})")
                print(f"   Dates: {check_in} to {check_out} ({nights} nights)")
                print(f"   Guests: {guests}")
                print(f"   Booking ID: {booking['booking_id']}")
                print()
            else:
                failed_bookings += 1
                print(f"❌ Failed to book for {guest_name}: {booking_result.get('error', 'Unknown error')}")
                print()
        else:
            failed_bookings += 1
            print(f"❌ No available rooms for {guest_name} ({guests} guests, {check_in} to {check_out})")
            print()
    
    print("\n" + "="*60)
    print(f"📊 Booking Summary:")
    print(f"   ✅ Successful: {successful_bookings}")
    print(f"   ❌ Failed: {failed_bookings}")
    print(f"   📋 Total: {successful_bookings + failed_bookings}")
    print("="*60)
    print("\n🎉 Done! You can now view these bookings in the admin dashboard at:")
    print("   http://localhost:5173/admin")
    print("   Login: admin / admin123")

if __name__ == "__main__":
    create_sample_bookings()
