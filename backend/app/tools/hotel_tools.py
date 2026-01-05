"""Hotel Booking Tools for MCP Server"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class HotelTools:
    """Tools for hotel room search and booking"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.bookings_file = os.path.join(data_dir, "hotel_bookings.json")
        self.rooms_file = os.path.join(data_dir, "hotel_rooms.json")
        
        # Initialize data files if they don't exist
        self._initialize_data()
    
    def _initialize_data(self):
        """Initialize hotel data files with sample data"""
        
        # Sample rooms data
        if not os.path.exists(self.rooms_file):
            sample_rooms = [
                {
                    "room_id": "R101",
                    "room_type": "Standard Single",
                    "capacity": 1,
                    "price_per_night": 100,
                    "amenities": ["WiFi", "TV", "Air Conditioning"],
                    "available": True
                },
                {
                    "room_id": "R102",
                    "room_type": "Standard Double",
                    "capacity": 2,
                    "price_per_night": 150,
                    "amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar"],
                    "available": True
                },
                {
                    "room_id": "R201",
                    "room_type": "Deluxe Suite",
                    "capacity": 2,
                    "price_per_night": 250,
                    "amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Ocean View", "Balcony"],
                    "available": True
                },
                {
                    "room_id": "R202",
                    "room_type": "Family Suite",
                    "capacity": 4,
                    "price_per_night": 350,
                    "amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Kitchen", "Living Room"],
                    "available": True
                },
                {
                    "room_id": "R301",
                    "room_type": "Presidential Suite",
                    "capacity": 4,
                    "price_per_night": 500,
                    "amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Ocean View", "Balcony", "Jacuzzi", "Butler Service"],
                    "available": True
                }
            ]
            
            with open(self.rooms_file, 'w') as f:
                json.dump(sample_rooms, f, indent=2)
        
        # Initialize bookings file
        if not os.path.exists(self.bookings_file):
            with open(self.bookings_file, 'w') as f:
                json.dump([], f, indent=2)
    
    def search_rooms(
        self,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        guests: int = 1,
        room_type: Optional[str] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Search for available hotel rooms
        
        Args:
            check_in: Check-in date (YYYY-MM-DD format)
            check_out: Check-out date (YYYY-MM-DD format)
            guests: Number of guests
            room_type: Type of room (e.g., "Standard", "Deluxe", "Suite")
            max_price: Maximum price per night
        
        Returns:
            Dictionary with search results
        """
        try:
            # Load rooms
            with open(self.rooms_file, 'r') as f:
                rooms = json.load(f)
            
            # Load bookings to check availability
            with open(self.bookings_file, 'r') as f:
                bookings = json.load(f)
            
            # Filter available rooms
            available_rooms = []
            
            for room in rooms:
                # Check capacity
                if room['capacity'] < guests:
                    continue
                
                # Check room type
                if room_type and room_type.lower() not in room['room_type'].lower():
                    continue
                
                # Check price
                if max_price and room['price_per_night'] > max_price:
                    continue
                
                # Check if room is booked for the requested dates
                is_available = True
                if check_in and check_out:
                    for booking in bookings:
                        if booking['room_id'] == room['room_id'] and booking['status'] == 'confirmed':
                            # Check date overlap
                            booking_start = datetime.strptime(booking['check_in'], '%Y-%m-%d')
                            booking_end = datetime.strptime(booking['check_out'], '%Y-%m-%d')
                            request_start = datetime.strptime(check_in, '%Y-%m-%d')
                            request_end = datetime.strptime(check_out, '%Y-%m-%d')
                            
                            if not (request_end <= booking_start or request_start >= booking_end):
                                is_available = False
                                break
                
                if is_available:
                    available_rooms.append(room)
            
            return {
                "success": True,
                "total_rooms": len(available_rooms),
                "rooms": available_rooms,
                "search_criteria": {
                    "check_in": check_in,
                    "check_out": check_out,
                    "guests": guests,
                    "room_type": room_type,
                    "max_price": max_price
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rooms": []
            }
    
    def book_room(
        self,
        room_id: str,
        guest_name: str,
        check_in: str,
        check_out: str,
        guests: int,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        special_requests: Optional[List[str]] = None,
        bed_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Book a hotel room
        
        Args:
            room_id: ID of the room to book
            guest_name: Name of the guest
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            email: Guest email
            phone: Guest phone number
            special_requests: List of special requests
            bed_type: Preference for bed type
        
        Returns:
            Dictionary with booking confirmation
        """
        try:
            # Load rooms
            with open(self.rooms_file, 'r') as f:
                rooms = json.load(f)
            
            # Find the room
            room = next((r for r in rooms if r['room_id'] == room_id), None)
            if not room:
                return {
                    "success": False,
                    "error": f"Room {room_id} not found"
                }
            
            # Check capacity
            if room['capacity'] < guests:
                return {
                    "success": False,
                    "error": f"Room capacity ({room['capacity']}) is less than number of guests ({guests})"
                }
            
            # Check availability
            availability = self.search_rooms(check_in=check_in, check_out=check_out)
            available_room_ids = [r['room_id'] for r in availability['rooms']]
            
            if room_id not in available_room_ids:
                return {
                    "success": False,
                    "error": f"Room {room_id} is not available for the selected dates"
                }
            
            # Calculate total price
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
            nights = (check_out_date - check_in_date).days
            total_price = room['price_per_night'] * nights
            
            # Create booking
            booking = {
                "booking_id": f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "room_id": room_id,
                "room_type": room['room_type'],
                "guest_name": guest_name,
                "email": email,
                "phone": phone,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "nights": nights,
                "price_per_night": room['price_per_night'],
                "total_price": total_price,
                "status": "confirmed",
                "special_requests": special_requests or [],
                "bed_type": bed_type,
                "booking_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Load existing bookings
            with open(self.bookings_file, 'r') as f:
                bookings = json.load(f)
            
            # Add new booking
            bookings.append(booking)
            
            # Save bookings
            with open(self.bookings_file, 'w') as f:
                json.dump(bookings, f, indent=2)
            
            return {
                "success": True,
                "message": "Booking confirmed successfully!",
                "booking": booking
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_booking(self, booking_id: str) -> Dict[str, Any]:
        """
        Get booking details by booking ID
        
        Args:
            booking_id: Booking ID
        
        Returns:
            Dictionary with booking details
        """
        try:
            with open(self.bookings_file, 'r') as f:
                bookings = json.load(f)
            
            booking = next((b for b in bookings if b['booking_id'] == booking_id), None)
            
            if booking:
                return {
                    "success": True,
                    "booking": booking
                }
            else:
                return {
                    "success": False,
                    "error": f"Booking {booking_id} not found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        """
        Cancel a booking
        
        Args:
            booking_id: Booking ID to cancel
        
        Returns:
            Dictionary with cancellation status
        """
        try:
            with open(self.bookings_file, 'r') as f:
                bookings = json.load(f)
            
            booking = next((b for b in bookings if b['booking_id'] == booking_id), None)
            
            if not booking:
                return {
                    "success": False,
                    "error": f"Booking {booking_id} not found"
                }
            
            if booking['status'] == 'cancelled':
                return {
                    "success": False,
                    "error": "Booking is already cancelled"
                }
            
            # Update booking status
            booking['status'] = 'cancelled'
            booking['cancellation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Save updated bookings
            with open(self.bookings_file, 'w') as f:
                json.dump(bookings, f, indent=2)
            
            return {
                "success": True,
                "message": f"Booking {booking_id} cancelled successfully",
                "booking": booking
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_all_bookings(self, status: Optional[str] = None) -> Dict[str, Any]:
        """
        List all bookings
        
        Args:
            status: Filter by status (confirmed, cancelled)
        
        Returns:
            Dictionary with list of bookings
        """
        try:
            with open(self.bookings_file, 'r') as f:
                bookings = json.load(f)
            
            if status:
                bookings = [b for b in bookings if b['status'] == status]
            
            return {
                "success": True,
                "total_bookings": len(bookings),
                "bookings": bookings
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "bookings": []
            }
