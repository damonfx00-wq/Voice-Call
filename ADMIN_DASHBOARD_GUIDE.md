# Admin Dashboard - 3D Room Visualization

## Overview
The admin dashboard provides a visual 3D-style interface to manage hotel rooms and bookings, similar to cinema seat selection systems.

## Features

### 🔐 **Authentication**
- Simple login system
- Demo credentials: `admin` / `admin123`
- Session-based access control

### 📊 **Dashboard Stats**
- **Available Rooms**: Real-time count of bookable rooms
- **Booked Rooms**: Currently occupied rooms
- **Total Rooms**: Complete inventory (200 rooms)
- **Active Bookings**: Number of confirmed reservations

### 🏢 **Floor Selection**
- Visual floor selector (Floors 1-10)
- Each floor has 20 rooms
- Easy navigation between floors

### 🎨 **3D Room Grid Visualization**
The room grid displays all rooms on the selected floor with:

#### Visual Status Indicators:
- **Green (Available)**: Room is ready to book
  - Shows room number, type, price, and capacity
- **Red (Booked)**: Room is currently occupied
  - Shows guest name and booking dates
- **Gray (Unavailable)**: Room is out of service

#### Interactive Features:
- **Hover Effect**: 3D lift animation on hover
- **Color Coding**: Instant status recognition
- **Detailed Info**: Guest details for booked rooms
- **Responsive Grid**: Adapts to screen size

### 📋 **Bookings Table**
- Recent bookings list
- Booking ID, room number, guest name
- Check-in/check-out dates
- Status badges (confirmed/cancelled)

## Access

### URL
```
http://localhost:5173/admin
```

### Login Credentials
```
Username: admin
Password: admin123
```

## Room Grid Layout

```
┌─────────────────────────────────────────┐
│  Floor 1 - Room Layout                  │
├─────────────────────────────────────────┤
│                                         │
│  [R101] [R102] [R103] [R104] [R105]    │
│  [R106] [R107] [R108] [R109] [R110]    │
│  [R111] [R112] [R113] [R114] [R115]    │
│  [R116] [R117] [R118] [R119] [R120]    │
│                                         │
└─────────────────────────────────────────┘
```

## Room Card Information

### Available Room
```
┌──────────────┐
│    R101      │  ← Room Number
│   Standard   │  ← Room Type
│  $107/night  │  ← Price
│    👥 1      │  ← Capacity
└──────────────┘
```

### Booked Room
```
┌──────────────┐
│    R201      │  ← Room Number
│   Deluxe     │  ← Room Type
│  John Smith  │  ← Guest Name
│  Jan 8-10    │  ← Booking Dates
│    👥 2      │  ← Capacity
└──────────────┘
```

## Color Scheme

| Status | Color | Gradient |
|--------|-------|----------|
| Available | Green | `#d4edda` → `#a8d5ba` |
| Booked | Red | `#f8d7da` → `#f5c6cb` |
| Unavailable | Gray | `#e2e3e5` → `#d6d8db` |

## API Endpoints Used

### Get All Bookings
```http
GET http://localhost:8000/api/bookings
```

Response:
```json
{
  "success": true,
  "total_bookings": 5,
  "bookings": [
    {
      "booking_id": "BK20260107143000",
      "room_id": "R201",
      "guest_name": "John Smith",
      "check_in": "2026-01-08",
      "check_out": "2026-01-10",
      "status": "confirmed"
    }
  ]
}
```

### Room Data
Loaded from: `/data/hotel_rooms.json`

## Features in Detail

### 1. Real-Time Updates
- Click "🔄 Refresh" to reload data
- Automatically syncs with backend
- Shows current booking status

### 2. Floor Navigation
- 10 floors with 20 rooms each
- Quick floor switching
- Active floor highlighted

### 3. Visual Feedback
- 3D hover effects
- Smooth animations
- Gradient backgrounds
- Shadow effects

### 4. Responsive Design
- Mobile-friendly grid
- Adaptive layout
- Touch-optimized

## Technical Stack

### Frontend
- **React** with TypeScript
- **CSS3** for 3D effects
- **Fetch API** for data loading

### Backend
- **FastAPI** endpoints
- **SQLAlchemy** for bookings
- **JSON** for room data

## File Structure

```
frontend/
├── src/
│   ├── pages/
│   │   └── AdminDashboard.tsx    # Main dashboard component
│   ├── styles/
│   │   └── AdminDashboard.css    # 3D styling
│   └── App.tsx                   # Routing setup

backend/
├── main.py                       # API endpoints
├── app/
│   └── tools/
│       └── hotel_tools.py        # Booking logic
└── data/
    └── hotel_rooms.json          # Room inventory
```

## Usage Guide

### For Administrators

1. **Login**
   - Navigate to `/admin`
   - Enter credentials
   - Click "Login"

2. **View Room Status**
   - Select a floor
   - View color-coded room grid
   - Hover for details

3. **Check Bookings**
   - Scroll to bookings table
   - View recent reservations
   - Check guest information

4. **Refresh Data**
   - Click refresh button
   - Updates all information
   - Syncs with database

## Customization

### Change Colors
Edit `AdminDashboard.css`:
```css
.room-card.available {
  background: linear-gradient(135deg, #yourcolor1, #yourcolor2);
}
```

### Adjust Grid Layout
Modify grid columns:
```css
.room-grid {
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
}
```

### Update Login Credentials
Edit `AdminDashboard.tsx`:
```typescript
if (username === 'yourusername' && password === 'yourpassword') {
  setIsAuthenticated(true);
}
```

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Drag-and-drop room assignment
- [ ] Multi-floor view
- [ ] Booking creation from dashboard
- [ ] Guest management
- [ ] Revenue analytics
- [ ] Export reports
- [ ] Email notifications

## Troubleshooting

### Rooms Not Loading
- Check backend is running on port 8000
- Verify `/data/hotel_rooms.json` exists
- Check browser console for errors

### Bookings Not Showing
- Ensure database is initialized
- Check API endpoint: `http://localhost:8000/api/bookings`
- Verify CORS settings

### Login Not Working
- Check credentials: `admin` / `admin123`
- Clear browser cache
- Check console for errors

## Support

For issues or questions:
1. Check browser console
2. Verify backend logs
3. Review API responses
4. Check network tab

---

**Built with ❤️ for ABC Hotel**
