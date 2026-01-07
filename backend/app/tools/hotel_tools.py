"""Hotel Booking Tools for MCP Server"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.models import Booking, User


class HotelTools:
    """Tools for hotel room search and booking"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        # legacy files, kept for room definitions
        self.rooms_file = os.path.join(data_dir, "hotel_rooms.json")
        
        # Initialize data files if they don't exist
        self._initialize_data()

    def get_db(self) -> Session:
        return SessionLocal()
    
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
        """
        try:
            # Convert types if needed (LLM sometimes passes strings)
            if isinstance(guests, str):
                guests = int(guests)
            if isinstance(max_price, str):
                max_price = float(max_price)
            
            # Load rooms
            with open(self.rooms_file, 'r') as f:
                rooms = json.load(f)
            
            # Fetch bookings from DB to check availability
            db = self.get_db()
            bookings = []
            try:
                # Get all active bookings
                # Note: In a real app we'd filter by date in SQL, but since dates are inside JSON or we need to parse them, 
                # and for simplicity matching previous logic, we fetch all non-cancelled.
                # Ideally we should extract start/end dates to columns for efficient querying.
                db_bookings = db.query(Booking).filter(Booking.status != 'cancelled').all()
                for b in db_bookings:
                    details = b.booking_details
                    # Inject status so logic below works
                    details['status'] = b.status
                    bookings.append(details)
            finally:
                db.close()
            
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
                        if booking.get('room_id') == room['room_id'] and booking.get('status') == 'confirmed':
                            # Check date overlap
                            try:
                                booking_start = datetime.strptime(booking['check_in'], '%Y-%m-%d')
                                booking_end = datetime.strptime(booking['check_out'], '%Y-%m-%d')
                                request_start = datetime.strptime(check_in, '%Y-%m-%d')
                                request_end = datetime.strptime(check_out, '%Y-%m-%d')
                                
                                if not (request_end <= booking_start or request_start >= booking_end):
                                    is_available = False
                                    break
                            except (ValueError, KeyError):
                                continue
                
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
        """
        if not phone:
             return {
                "success": False,
                "error": "Phone number is required for booking"
            }

        try:
            # Convert types if needed (LLM sometimes passes strings)
            if isinstance(guests, str):
                guests = int(guests)
                
            # Handle string special_requests from LLM
            if isinstance(special_requests, str):
                if special_requests.lower() in ['null', 'none', '', '[]']:
                    special_requests = []
                else:
                    # If it looks like a list string "['a','b']", try to parse or just wrap
                    try:
                        special_requests = json.loads(special_requests)
                    except:
                        special_requests = [special_requests]
            
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
            
            booking_id = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create booking details JSON
            booking_details = {
                "booking_id": booking_id,
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
                "special_requests": special_requests or [],
                "bed_type": bed_type,
                "booking_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            db = self.get_db()
            try:
                # Find or create user
                user = db.query(User).filter(User.phone_number == phone).first()
                if not user:
                    user = User(phone_number=phone)
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                
                # Create booking
                new_booking = Booking(
                    user_id=user.id,
                    booking_details=booking_details,
                    status="confirmed"
                )
                db.add(new_booking)
                db.commit()
                db.refresh(new_booking)
                
                # Update booking_details with the actual DB ID if needed, or just return as is
                # We used a generated string ID for display purposes
                
                return {
                    "success": True,
                    "message": "Booking confirmed successfully!",
                    "booking": booking_details
                }
            except Exception as db_err:
                db.rollback()
                raise db_err
            finally:
                db.close()
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_booking(self, booking_id: str) -> Dict[str, Any]:
        """
        Get booking details by booking ID
        """
        db = self.get_db()
        try:
            # We need to search inside the JSON or assume we can find it.
            # Since booking_id is in the JSON blob, we have to query.
            # Postgres supports JSON queries, but for simplicity/portability without complex SQL alchemy mapping:
            # We might want to just search all bookings or if we had put booking_id in a column.
            # Efficiency fix: In real app, put booking_id in a separate column.
            # For this agent task, let's just query all and filter in python or use generic JSON operator if possible.
            # OR we can assume booking_id matches the one generated. 
            
            # Let's try to query using text matching or simple iteration if list is small. 
            # Ideally: db.query(Booking).filter(Booking.booking_details['booking_id'].astext == booking_id).first()
            
            all_bookings = db.query(Booking).all()
            found_booking = None
            for b in all_bookings:
                if b.booking_details.get('booking_id') == booking_id:
                    found_booking = b
                    break
            
            if found_booking:
                details = found_booking.booking_details
                details['status'] = found_booking.status # Ensure status is consistent
                return {
                    "success": True,
                    "booking": details
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
        finally:
            db.close()
    
    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        """
        Cancel a booking
        """
        db = self.get_db()
        try:
            found_booking = None
            bookings = db.query(Booking).all()
            for b in bookings:
                if b.booking_details.get('booking_id') == booking_id:
                    found_booking = b
                    break
            
            if not found_booking:
                return {
                    "success": False,
                    "error": f"Booking {booking_id} not found"
                }
            
            if found_booking.status == 'cancelled':
                return {
                    "success": False,
                    "error": "Booking is already cancelled"
                }
            
            found_booking.status = 'cancelled'
            found_booking.booking_details['status'] = 'cancelled' # update json as well for consistency key
            found_booking.booking_details['cancellation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # For some SQLAlcheny versions detecting JSON mutation needs flagging
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(found_booking, "booking_details")
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Booking {booking_id} cancelled successfully",
                "booking": found_booking.booking_details
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            db.close()
    
    def list_all_bookings(self, status: Optional[str] = None) -> Dict[str, Any]:
        """
        List all bookings
        """
        db = self.get_db()
        try:
            query = db.query(Booking)
            if status:
                query = query.filter(Booking.status == status)
            
            bookings_orm = query.all()
            bookings_list = []
            for b in bookings_orm:
                details = b.booking_details
                details['status'] = b.status
                bookings_list.append(details)
            
            return {
                "success": True,
                "total_bookings": len(bookings_list),
                "bookings": bookings_list
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "bookings": []
            }
        finally:
            db.close()
