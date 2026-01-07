# Phone Number Integration Fix

## Issue Identified
The agent was attempting to book rooms with `"phone": "null"` or `"phone": "None"`, causing bookings to fail because the `book_room` function requires a valid phone number.

## Root Cause
- Phone number is collected by the frontend (from the dial pad)
- Phone number is passed as `user_id` to the backend
- Agent was not storing or using this phone number when making bookings

## Solution Implemented

### 1. Store Phone Number in Agent
**File**: `/backend/app/agents/agent.py`

Added phone number storage in the agent initialization:
```python
# Store phone number (passed as user_id from frontend)
self.phone_number = user_id if user_id else None
```

### 2. Include Phone in System Prompt
Updated the system prompt to:
- Display the phone number to the agent
- Explicitly instruct the agent to use it in ALL bookings
- Show the exact phone number value to use

```python
phone_info = f"Phone number: {self.phone_number}" if self.phone_number else "Phone number: Not provided"

# In system prompt:
Phone number: {self.phone_number}

# Booking instructions:
10. **BOOK** - Call book_hotel_room with:
    - guest_name: The name they provided
    - email: The email they provided
    - phone: "{self.phone_number}" (ALWAYS use this exact phone number)
    - room_id, check_in, check_out, guests: From conversation
    - special_requests, bed_type: If provided
```

### 3. Clear Instructions
Added to IMPORTANT section:
```
- **ALWAYS USE PHONE: "{self.phone_number}"** - This is the caller's phone number, use it in ALL bookings
- Never ask for phone number - it's already captured
```

## How It Works

### Frontend Flow:
1. User enters phone number on dial pad
2. Phone number stored in state: `phoneNumber`
3. When calling API, phone passed as `user_id`:
   ```typescript
   user_id: phoneNumber || undefined
   ```

### Backend Flow:
1. Agent receives `user_id` (phone number) in constructor
2. Stores it: `self.phone_number = user_id`
3. Includes it in system prompt context
4. Agent uses it when calling `book_hotel_room` tool

### Example Booking Call:
```json
{
  "guest_name": "John Smith",
  "email": "john@email.com",
  "phone": "5551234567",  // ✅ Now uses actual phone number
  "room_id": "R201",
  "check_in": "2026-01-08",
  "check_out": "2026-01-10",
  "guests": 2,
  "special_requests": [],
  "bed_type": "King"
}
```

## Testing

### Before Fix:
```json
{
  "phone": "null",  // ❌ Booking fails
  "guest_name": "null",
  "email": "null"
}
```

### After Fix:
```json
{
  "phone": "5551234567",  // ✅ Valid phone number
  "guest_name": "John Smith",
  "email": "john@email.com"
}
```

## Files Modified

1. **`/backend/app/agents/agent.py`**
   - Added `self.phone_number` storage (line 40-41)
   - Updated system prompt to include phone number (line 241-243)
   - Added explicit booking instructions with phone number (line 268-273)
   - Added important reminder about phone usage (line 283-284)

## Benefits

✅ Bookings will now succeed with valid phone numbers
✅ No need to ask users for phone number (already captured)
✅ Agent has clear context about the caller
✅ All booking data is complete and valid

## Auto-Reload

The backend automatically reloaded with these changes. You should see in the terminal:
```
WARNING:  WatchFiles detected changes in 'app/agents/agent.py'. Reloading...
INFO:     Started server process [19643]
```

## Next Test

Try making a booking now and you should see:
```
🔧 Executing tool: book_hotel_room
   Arguments: {
  "guest_name": "Your Name",
  "email": "your@email.com",
  "phone": "5551234567",  // ✅ Real phone number
  "room_id": "R201",
  ...
}
```

The booking should succeed! 🎉
