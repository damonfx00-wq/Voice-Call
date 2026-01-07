import React, { useState } from 'react';
import '../styles/AdminDashboard.css';

interface Room {
    room_id: string;
    room_type: string;
    capacity: number;
    price_per_night: number;
    floor: number;
    available: boolean;
}

interface Booking {
    booking_id: string;
    room_id: string;
    guest_name: string;
    check_in: string;
    check_out: string;
    status: string;
}

const AdminDashboard: React.FC = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [rooms, setRooms] = useState<Room[]>([]);
    const [bookings, setBookings] = useState<Booking[]>([]);
    const [selectedFloor, setSelectedFloor] = useState<number>(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Simple authentication (in production, use proper auth)
    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        if (username === 'admin' && password === 'admin123') {
            setIsAuthenticated(true);
            setError('');
            loadData();
        } else {
            setError('Invalid credentials. Use admin/admin123');
        }
    };

    const loadData = async () => {
        setLoading(true);
        try {
            // Load rooms from the JSON file
            const roomsResponse = await fetch('/data/hotel_rooms.json');
            const roomsData = await roomsResponse.json();
            setRooms(roomsData);

            // Load bookings from API
            const bookingsResponse = await fetch('http://localhost:8000/api/bookings');
            if (bookingsResponse.ok) {
                const bookingsData = await bookingsResponse.json();
                setBookings(bookingsData.bookings || []);
            }
        } catch (err) {
            console.error('Error loading data:', err);
        } finally {
            setLoading(false);
        }
    };

    const getRoomStatus = (roomId: string): 'available' | 'booked' | 'unavailable' => {
        // Show as booked if there is ANY confirmed booking for this room
        const booking = bookings.find(b =>
            b.room_id === roomId &&
            b.status === 'confirmed'
        );

        if (booking) return 'booked';

        const room = rooms.find(r => r.room_id === roomId);
        return room?.available ? 'available' : 'unavailable';
    };

    const getBookingInfo = (roomId: string): Booking | null => {
        return bookings.find(b =>
            b.room_id === roomId &&
            b.status === 'confirmed'
        ) || null;
    };

    const getRoomsByFloor = (floor: number) => {
        return rooms.filter(r => r.floor === floor);
    };

    const floors = Array.from(new Set(rooms.map(r => r.floor))).sort((a, b) => a - b);

    if (!isAuthenticated) {
        return (
            <div className="admin-login">
                <div className="login-container">
                    <div className="login-header">
                        <h1>🏨 ABC Hotel Admin</h1>
                        <p>Room Management Dashboard</p>
                    </div>

                    <form onSubmit={handleLogin} className="login-form">
                        <div className="form-group">
                            <label>Username</label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Enter username"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter password"
                                required
                            />
                        </div>

                        {error && <div className="error-message">{error}</div>}

                        <button type="submit" className="login-button">
                            Login
                        </button>

                        <div className="demo-credentials">
                            <small>Demo: admin / admin123</small>
                        </div>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-dashboard">
            <div className="dashboard-header">
                <div className="header-left">
                    <h1>🏨 ABC Hotel - Room Management</h1>
                    <p>Real-time room availability and booking status</p>
                </div>
                <div className="header-right">
                    <button onClick={() => loadData()} className="refresh-button">
                        🔄 Refresh
                    </button>
                    <button onClick={() => setIsAuthenticated(false)} className="logout-button">
                        Logout
                    </button>
                </div>
            </div>

            <div className="dashboard-stats">
                <div className="stat-card available">
                    <div className="stat-icon">✓</div>
                    <div className="stat-info">
                        <h3>{rooms.filter(r => getRoomStatus(r.room_id) === 'available').length}</h3>
                        <p>Available Rooms</p>
                    </div>
                </div>

                <div className="stat-card booked">
                    <div className="stat-icon">🔒</div>
                    <div className="stat-info">
                        <h3>{rooms.filter(r => getRoomStatus(r.room_id) === 'booked').length}</h3>
                        <p>Booked Rooms</p>
                    </div>
                </div>

                <div className="stat-card total">
                    <div className="stat-icon">🏢</div>
                    <div className="stat-info">
                        <h3>{rooms.length}</h3>
                        <p>Total Rooms</p>
                    </div>
                </div>

                <div className="stat-card revenue">
                    <div className="stat-icon">💰</div>
                    <div className="stat-info">
                        <h3>{bookings.filter(b => b.status === 'confirmed').length}</h3>
                        <p>Active Bookings</p>
                    </div>
                </div>
            </div>

            <div className="floor-selector">
                <h2>Select Floor</h2>
                <div className="floor-buttons">
                    {floors.map(floor => (
                        <button
                            key={floor}
                            className={`floor-button ${selectedFloor === floor ? 'active' : ''}`}
                            onClick={() => setSelectedFloor(floor)}
                        >
                            Floor {floor}
                        </button>
                    ))}
                </div>
            </div>

            <div className="room-grid-container">
                <div className="grid-header">
                    <h2>Floor {selectedFloor} - Room Layout</h2>
                    <div className="legend">
                        <div className="legend-item">
                            <span className="legend-color available"></span>
                            <span>Available</span>
                        </div>
                        <div className="legend-item">
                            <span className="legend-color booked"></span>
                            <span>Booked</span>
                        </div>
                        <div className="legend-item">
                            <span className="legend-color unavailable"></span>
                            <span>Unavailable</span>
                        </div>
                    </div>
                </div>

                {loading ? (
                    <div className="loading">Loading rooms...</div>
                ) : (
                    <div className="room-grid">
                        {getRoomsByFloor(selectedFloor).map(room => {
                            const status = getRoomStatus(room.room_id);
                            const booking = getBookingInfo(room.room_id);

                            return (
                                <div
                                    key={room.room_id}
                                    className={`room-card ${status}`}
                                    title={`${room.room_id} - ${room.room_type}`}
                                >
                                    <div className="room-number">{room.room_id}</div>
                                    <div className="room-type">{room.room_type.split(' ')[0]}</div>

                                    {booking && (
                                        <div className="booking-info">
                                            <div className="guest-name">{booking.guest_name}</div>
                                            <div className="booking-dates">
                                                {new Date(booking.check_in).toLocaleDateString()} -
                                                {new Date(booking.check_out).toLocaleDateString()}
                                            </div>
                                        </div>
                                    )}

                                    {status === 'available' && (
                                        <div className="room-price">${room.price_per_night}/night</div>
                                    )}

                                    <div className="room-capacity">👥 {room.capacity}</div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            <div className="bookings-section">
                <h2>Recent Bookings</h2>
                <div className="bookings-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Booking ID</th>
                                <th>Room</th>
                                <th>Guest Name</th>
                                <th>Check-in</th>
                                <th>Check-out</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {bookings.slice(0, 10).map(booking => (
                                <tr key={booking.booking_id}>
                                    <td>{booking.booking_id}</td>
                                    <td>{booking.room_id}</td>
                                    <td>{booking.guest_name}</td>
                                    <td>{new Date(booking.check_in).toLocaleDateString()}</td>
                                    <td>{new Date(booking.check_out).toLocaleDateString()}</td>
                                    <td>
                                        <span className={`status-badge ${booking.status}`}>
                                            {booking.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
