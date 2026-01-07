# Hotel Room Inventory - 200 Rooms

## Overview
Successfully populated the database with **200 dummy hotel rooms** distributed across 10 floors.

## Room Distribution

| Room Type | Count | Capacity | Price Range |
|-----------|-------|----------|-------------|
| Standard Single | 20 | 1 guest | $91 - $109/night |
| Standard Double | 20 | 2 guests | $135 - $154/night |
| Deluxe Single | 20 | 1 guest | $169 - $193/night |
| Deluxe Double | 20 | 2 guests | $204 - $229/night |
| Deluxe Suite | 20 | 2 guests | $234 - $255/night |
| Family Room | 20 | 4 guests | $280 - $325/night |
| Family Suite | 20 | 4 guests | $326 - $364/night |
| Executive Suite | 20 | 3 guests | $372 - $435/night |
| Presidential Suite | 20 | 4 guests | $468 - $536/night |
| Penthouse Suite | 20 | 6 guests | $687 - $821/night |

**Total: 200 rooms**

## Floor Layout
- **Floor 1-10**: Each floor has 20 rooms (R101-R120, R201-R220, ..., R1001-R1020)
- Room IDs follow the pattern: `R[Floor][Room Number]`
  - Example: R305 = Floor 3, Room 5

## Amenities
Each room includes a variety of amenities:

### Standard Amenities (all rooms)
- WiFi
- TV
- Air Conditioning

### Premium Amenities (varies by room type)
- Mini Bar
- Ocean View
- Balcony
- Jacuzzi
- Butler Service
- Kitchen/Kitchenette
- Living Room
- Work Desk
- Premium Bathroom
- Private Terrace
- Full Kitchen

### Additional Amenities (randomly assigned)
- Room Service
- Laundry Service
- Safe
- Iron & Ironing Board
- Hair Dryer
- Bathrobe
- Slippers
- Complimentary Breakfast
- Minibar Snacks
- Soundproofing
- City View
- Garden View
- Blackout Curtains

## Price Range
- **Minimum**: $91/night (Standard Single)
- **Maximum**: $821/night (Penthouse Suite)
- **Average**: ~$300/night

## Sample Rooms

### Room R101 - Standard Single
- **Floor**: 1
- **Capacity**: 1 guest
- **Price**: $107/night
- **Amenities**: Air Conditioning, Garden View, TV, WiFi

### Room R505 - Deluxe Suite
- **Floor**: 5
- **Capacity**: 2 guests
- **Price**: ~$245/night
- **Amenities**: WiFi, TV, Air Conditioning, Mini Bar, Ocean View, Balcony, etc.

### Room R1010 - Penthouse Suite
- **Floor**: 10
- **Capacity**: 6 guests
- **Price**: ~$750/night
- **Amenities**: WiFi, TV, Air Conditioning, Mini Bar, Ocean View, Balcony, Jacuzzi, Butler Service, Private Terrace, Full Kitchen, etc.

## Files
- **Data File**: `/home/vedp/my-project/Voice-Call/backend/data/hotel_rooms.json`
- **Generation Script**: `/home/vedp/my-project/Voice-Call/backend/populate_rooms.py`

## Usage
The hotel booking system will now have access to all 200 rooms when searching for availability. The agent will automatically:
1. Search through all available rooms based on dates
2. Filter by capacity, room type, and price
3. Present options to users
4. Handle bookings and track availability

## Re-generating Data
To regenerate the room data with different random variations:
```bash
cd /home/vedp/my-project/Voice-Call/backend
python3 populate_rooms.py
```

This will overwrite the existing `hotel_rooms.json` file with a new set of 200 rooms.
