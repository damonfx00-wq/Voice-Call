"""Script to populate hotel_rooms.json with 200 dummy rooms"""
import json
import random
import os

# Define room types with their characteristics
ROOM_TYPES = [
    {
        "type": "Standard Single",
        "capacity": 1,
        "base_price": 100,
        "base_amenities": ["WiFi", "TV", "Air Conditioning"]
    },
    {
        "type": "Standard Double",
        "capacity": 2,
        "base_price": 150,
        "base_amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar"]
    },
    {
        "type": "Deluxe Single",
        "capacity": 1,
        "base_price": 180,
        "base_amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Premium Bedding"]
    },
    {
        "type": "Deluxe Double",
        "capacity": 2,
        "base_price": 220,
        "base_amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Premium Bedding", "Coffee Maker"]
    },
    {
        "type": "Deluxe Suite",
        "capacity": 2,
        "base_price": 250,
        "base_amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Ocean View", "Balcony"]
    },
    {
        "type": "Family Room",
        "capacity": 4,
        "base_price": 300,
        "base_amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Sofa Bed", "Microwave"]
    },
    {
        "type": "Family Suite",
        "capacity": 4,
        "base_price": 350,
        "base_amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Kitchen", "Living Room"]
    },
    {
        "type": "Executive Suite",
        "capacity": 3,
        "base_price": 400,
        "base_amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Ocean View", "Balcony", "Work Desk", "Premium Bathroom"]
    },
    {
        "type": "Presidential Suite",
        "capacity": 4,
        "base_price": 500,
        "base_amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Ocean View", "Balcony", "Jacuzzi", "Butler Service"]
    },
    {
        "type": "Penthouse Suite",
        "capacity": 6,
        "base_price": 750,
        "base_amenities": ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Ocean View", "Balcony", "Jacuzzi", "Butler Service", "Private Terrace", "Full Kitchen"]
    }
]

# Additional amenities that can be randomly added
EXTRA_AMENITIES = [
    "Room Service",
    "Laundry Service",
    "Safe",
    "Iron & Ironing Board",
    "Hair Dryer",
    "Bathrobe",
    "Slippers",
    "Complimentary Breakfast",
    "Minibar Snacks",
    "Soundproofing",
    "City View",
    "Garden View",
    "Blackout Curtains"
]

def generate_rooms(total_rooms=200):
    """Generate dummy room data"""
    rooms = []
    
    # Distribute rooms across 10 floors (20 rooms per floor)
    for floor in range(1, 11):
        for room_num in range(1, 21):
            # Create room ID (e.g., R101, R102, ..., R1020)
            room_id = f"R{floor}{room_num:02d}"
            
            # Select room type (distribute evenly with some randomness)
            room_type_data = ROOM_TYPES[len(rooms) % len(ROOM_TYPES)]
            
            # Add some price variation (+/- 10%)
            price_variation = random.uniform(0.9, 1.1)
            price = round(room_type_data["base_price"] * price_variation)
            
            # Base amenities
            amenities = room_type_data["base_amenities"].copy()
            
            # Randomly add 1-3 extra amenities
            num_extra = random.randint(1, 3)
            extra = random.sample(EXTRA_AMENITIES, num_extra)
            amenities.extend(extra)
            
            # Remove duplicates and sort
            amenities = sorted(list(set(amenities)))
            
            # Create room object
            room = {
                "room_id": room_id,
                "room_type": room_type_data["type"],
                "capacity": room_type_data["capacity"],
                "price_per_night": price,
                "amenities": amenities,
                "available": True,
                "floor": floor
            }
            
            rooms.append(room)
    
    return rooms

def main():
    """Main function to generate and save room data"""
    # Ensure data directory exists
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate 200 rooms
    rooms = generate_rooms(200)
    
    # Save to JSON file
    output_file = os.path.join(data_dir, "hotel_rooms.json")
    with open(output_file, 'w') as f:
        json.dump(rooms, f, indent=2)
    
    print(f"✅ Successfully generated {len(rooms)} rooms!")
    print(f"📁 Saved to: {output_file}")
    
    # Print summary statistics
    room_type_counts = {}
    for room in rooms:
        room_type = room["room_type"]
        room_type_counts[room_type] = room_type_counts.get(room_type, 0) + 1
    
    print("\n📊 Room Distribution:")
    for room_type, count in sorted(room_type_counts.items()):
        print(f"   {room_type}: {count} rooms")
    
    # Print price range
    prices = [room["price_per_night"] for room in rooms]
    print(f"\n💰 Price Range: ${min(prices)} - ${max(prices)} per night")
    
    # Print sample rooms
    print("\n🏨 Sample Rooms:")
    for i in range(min(3, len(rooms))):
        room = rooms[i]
        print(f"\n   Room {room['room_id']}:")
        print(f"   - Type: {room['room_type']}")
        print(f"   - Capacity: {room['capacity']} guests")
        print(f"   - Price: ${room['price_per_night']}/night")
        print(f"   - Floor: {room['floor']}")
        print(f"   - Amenities: {', '.join(room['amenities'][:5])}...")

if __name__ == "__main__":
    main()
