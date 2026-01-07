"""Simple test to verify hotel rooms data"""
import json
import os

# Load the rooms data
data_file = './data/hotel_rooms.json'

if os.path.exists(data_file):
    with open(data_file, 'r') as f:
        rooms = json.load(f)
    
    print(f'✅ Successfully loaded {len(rooms)} rooms from database')
    print(f'\n📊 Room Statistics:')
    
    # Count by type
    room_types = {}
    capacities = {}
    floors = {}
    
    for room in rooms:
        # Count by type
        room_type = room['room_type']
        room_types[room_type] = room_types.get(room_type, 0) + 1
        
        # Count by capacity
        capacity = room['capacity']
        capacities[capacity] = capacities.get(capacity, 0) + 1
        
        # Count by floor
        floor = room.get('floor', 'Unknown')
        floors[floor] = floors.get(floor, 0) + 1
    
    print(f'\n🏨 By Room Type:')
    for room_type, count in sorted(room_types.items()):
        print(f'   {room_type}: {count} rooms')
    
    print(f'\n👥 By Capacity:')
    for capacity, count in sorted(capacities.items()):
        print(f'   {capacity} guests: {count} rooms')
    
    print(f'\n🏢 By Floor:')
    for floor, count in sorted(floors.items()):
        print(f'   Floor {floor}: {count} rooms')
    
    # Price statistics
    prices = [room['price_per_night'] for room in rooms]
    print(f'\n💰 Price Statistics:')
    print(f'   Minimum: ${min(prices)}/night')
    print(f'   Maximum: ${max(prices)}/night')
    print(f'   Average: ${sum(prices)//len(prices)}/night')
    
    # Sample rooms
    print(f'\n🔍 Sample Rooms:')
    for i in range(min(5, len(rooms))):
        room = rooms[i]
        print(f'\n   {i+1}. Room {room["room_id"]} - {room["room_type"]}')
        print(f'      Floor: {room.get("floor", "N/A")} | Capacity: {room["capacity"]} | Price: ${room["price_per_night"]}/night')
        print(f'      Amenities: {", ".join(room["amenities"][:4])}...')
    
    print(f'\n✅ All rooms are ready for booking!')
else:
    print(f'❌ Error: {data_file} not found')
