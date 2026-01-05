import { useState, useEffect } from 'react';
import './Header.css';

interface HeaderProps {
    onThemeToggle: () => void;
    isDark: boolean;
}

export default function Header({ onThemeToggle, isDark }: HeaderProps) {
    const [isScrolled, setIsScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 10);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <header className={`header ${isScrolled ? 'scrolled' : ''}`}>
            <div className="header-container">
                <div className="header-left">
                    <div className="logo">
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                            <rect width="32" height="32" rx="8" fill="url(#gradient)" />
                            <path
                                d="M16 8L22 12V20L16 24L10 20V12L16 8Z"
                                fill="white"
                                fillOpacity="0.9"
                            />
                            <defs>
                                <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                                    <stop stopColor="#1a73e8" />
                                    <stop offset="1" stopColor="#34a853" />
                                </linearGradient>
                            </defs>
                        </svg>
                        <span className="logo-text">MCP Agent</span>
                    </div>
                </div>

                <nav className="header-nav">
                    <a href="#chat" className="nav-link active">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M2 5C2 3.89543 2.89543 3 4 3H16C17.1046 3 18 3.89543 18 5V12C18 13.1046 17.1046 14 16 14H11L7 17V14H4C2.89543 14 2 13.1046 2 12V5Z" />
                        </svg>
                        Chat
                    </a>
                    <a href="#csv" className="nav-link">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M3 4C3 3.44772 3.44772 3 4 3H16C16.5523 3 17 3.44772 17 4V16C17 16.5523 16.5523 17 16 17H4C3.44772 17 3 16.5523 3 16V4Z" />
                            <path d="M7 7H13M7 10H13M7 13H10" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                        CSV Files
                    </a>
                    <a href="#rag" className="nav-link">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M4 4C4 2.89543 4.89543 2 6 2H10L14 6V16C14 17.1046 13.1046 18 12 18H6C4.89543 18 4 17.1046 4 16V4Z" />
                        </svg>
                        Documents
                    </a>
                </nav>

                <div className="header-right">
                    <button
                        className="icon-button"
                        onClick={onThemeToggle}
                        aria-label="Toggle theme"
                    >
                        {isDark ? (
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M10 2C10.5523 2 11 2.44772 11 3V4C11 4.55228 10.5523 5 10 5C9.44772 5 9 4.55228 9 4V3C9 2.44772 9.44772 2 10 2Z" />
                                <path d="M10 15C10.5523 15 11 15.4477 11 16V17C11 17.5523 10.5523 18 10 18C9.44772 18 9 17.5523 9 17V16C9 15.4477 9.44772 15 10 15Z" />
                                <path d="M3 10C3 9.44772 3.44772 9 4 9H5C5.55228 9 6 9.44772 6 10C6 10.5523 5.55228 11 5 11H4C3.44772 11 3 10.5523 3 10Z" />
                                <path d="M14 10C14 9.44772 14.4477 9 15 9H16C16.5523 9 17 9.44772 17 10C17 10.5523 16.5523 11 16 11H15C14.4477 11 14 10.5523 14 10Z" />
                                <circle cx="10" cy="10" r="3" />
                            </svg>
                        ) : (
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                            </svg>
                        )}
                    </button>
                </div>
            </div>
        </header>
    );
}
