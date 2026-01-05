import { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import './VoiceCallInterface.css';

type CallState = 'idle' | 'dialing' | 'calling' | 'connected' | 'ended';

interface TranscriptItem {
    sender: 'user' | 'ai';
    text: string;
    timestamp: string;
}

export default function VoiceCallInterface() {
    const [callState, setCallState] = useState<CallState>('idle');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [currentTranscript, setCurrentTranscript] = useState('');
    const [lastUserSpeech, setLastUserSpeech] = useState('');
    const [lastAIResponse, setLastAIResponse] = useState('');
    const [callDuration, setCallDuration] = useState(0);
    const [audioLevel, setAudioLevel] = useState(0);
    const [error, setError] = useState<string | null>(null);

    // Transcript state
    const [transcript, setTranscript] = useState<TranscriptItem[]>([]);

    const recognitionRef = useRef<any>(null);
    const synthesisRef = useRef<SpeechSynthesis | null>(null);
    const callTimerRef = useRef<number | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const micStreamRef = useRef<MediaStream | null>(null);

    // Timer Effect - Independent of other states
    useEffect(() => {
        if (callState === 'connected') {
            callTimerRef.current = window.setInterval(() => {
                setCallDuration((prev) => prev + 1);
            }, 1000);
        } else {
            if (callTimerRef.current) {
                clearInterval(callTimerRef.current);
                callTimerRef.current = null;
            }
        }

        return () => {
            if (callTimerRef.current) {
                clearInterval(callTimerRef.current);
            }
        };
    }, [callState]);

    useEffect(() => {
        // Initialize speech recognition
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = true;
            recognitionRef.current.interimResults = true;
            recognitionRef.current.lang = 'en-US';
            recognitionRef.current.maxAlternatives = 1;

            recognitionRef.current.onresult = (event: any) => {
                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }

                setCurrentTranscript(interimTranscript || finalTranscript);

                if (finalTranscript) {
                    handleVoiceInput(finalTranscript);
                }
            };

            recognitionRef.current.onstart = () => {
                console.log('Speech recognition started');
                setIsListening(true);
                setError(null);
            };

            recognitionRef.current.onend = () => {
                console.log('Speech recognition ended');
                setIsListening(false);

                // CRITICAL: Always restart if connected and not speaking
                if (callState === 'connected' && !isSpeaking) {
                    console.log('Auto-restarting listener...');
                    setTimeout(() => {
                        try {
                            recognitionRef.current?.start();
                        } catch (e) {
                            console.log('Restart failed:', e);
                        }
                    }, 300);
                }
            };

            recognitionRef.current.onerror = (event: any) => {
                console.error('Speech recognition error:', event.error);

                if (event.error === 'not-allowed') {
                    setError('Microphone access denied. Please allow microphone access.');
                } else if (event.error === 'no-speech') {
                    // Silence detected - just restart immediately
                    if (callState === 'connected' && !isSpeaking) {
                        try {
                            recognitionRef.current?.stop();
                            setTimeout(() => recognitionRef.current?.start(), 200);
                        } catch (e) { }
                    }
                } else {
                    if (callState === 'connected' && !isSpeaking) {
                        setTimeout(() => {
                            try {
                                recognitionRef.current?.start();
                            } catch (e) { }
                        }, 1000);
                    }
                }
            };
        } else {
            setError('Speech recognition not supported in this browser. Please use Chrome or Edge.');
        }

        // Initialize speech synthesis
        synthesisRef.current = window.speechSynthesis;

        return () => {
            stopAll();
        };
    }, [callState, isSpeaking]);

    const stopAll = () => {
        if (recognitionRef.current) recognitionRef.current.stop();
        if (synthesisRef.current) synthesisRef.current.cancel();
        // Don't clear timer here, handled by separate effect
        if (micStreamRef.current) micStreamRef.current.getTracks().forEach(track => track.stop());
        if (audioContextRef.current) audioContextRef.current.close();
    };

    const initializeAudioVisualization = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            micStreamRef.current = stream;
            audioContextRef.current = new AudioContext();
            analyserRef.current = audioContextRef.current.createAnalyser();
            const source = audioContextRef.current.createMediaStreamSource(stream);

            analyserRef.current.fftSize = 256;
            source.connect(analyserRef.current);

            updateAudioLevel();
        } catch (error) {
            console.error('Error accessing microphone:', error);
            setError('Could not access microphone. Please check permissions.');
        }
    };

    const updateAudioLevel = () => {
        if (!analyserRef.current) return;

        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);

        const animate = () => {
            if (callState !== 'connected') return;

            analyserRef.current!.getByteFrequencyData(dataArray);
            const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
            setAudioLevel(average / 255);

            requestAnimationFrame(animate);
        };

        animate();
    };

    const handleDialPad = (digit: string) => {
        if (phoneNumber.length < 10) {
            setPhoneNumber(phoneNumber + digit);
            playDTMFTone();
        }
    };

    const handleBackspace = () => {
        setPhoneNumber(phoneNumber.slice(0, -1));
    };

    const playDTMFTone = () => {
        try {
            const audioContext = new AudioContext();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 697;
            gainNode.gain.value = 0.1;

            oscillator.start();
            setTimeout(() => oscillator.stop(), 100);
        } catch (e) {
            console.error('Audio context error:', e);
        }
    };

    const handleCall = async () => {
        setError(null);
        setCallState('dialing');
        setTranscript([]); // Reset transcript

        setTimeout(() => {
            setCallState('calling');
        }, 1000);

        setTimeout(() => {
            setCallState('connected');
            startCall();
        }, 3000);
    };

    const startCall = async () => {
        // Timer is handled by useEffect now
        await initializeAudioVisualization();

        const greeting = 'Hello! This is your AI assistant. I\'m listening. How can I help you today?';
        setLastAIResponse(greeting);
        addToTranscript('ai', greeting);

        // Speak greeting then start listening
        speakText(greeting);
    };

    const startListening = () => {
        if (recognitionRef.current && callState === 'connected') {
            try {
                recognitionRef.current.start();
            } catch (error) {
                console.error('Error starting recognition:', error);
            }
        }
    };

    const stopListening = () => {
        if (recognitionRef.current) {
            try {
                recognitionRef.current.stop();
            } catch (e) {
                console.log('Stop recognition error:', e);
            }
        }
    };

    const addToTranscript = (sender: 'user' | 'ai', text: string) => {
        setTranscript(prev => [...prev, {
            sender,
            text,
            timestamp: new Date().toLocaleTimeString()
        }]);
    };

    const handleVoiceInput = async (text: string) => {
        if (!text.trim() || isSpeaking) return;

        const lowerText = text.toLowerCase().trim();

        // Add user speech to transcript
        addToTranscript('user', text);

        // Handle "repeat" command locally with broader detection
        // Checks for "repeat", "say that again", "say it again", "pardon"
        if ((lowerText.includes('repeat') ||
            lowerText.includes('say that again') ||
            lowerText.includes('say it again') ||
            lowerText.includes('pardon')) && lastAIResponse) {

            setLastUserSpeech(text);
            setCurrentTranscript('');
            stopListening();
            speakText(lastAIResponse);
            addToTranscript('ai', lastAIResponse); // Log repeat as well
            return;
        }

        setLastUserSpeech(text);
        setCurrentTranscript('');
        stopListening();

        try {
            const response = await apiService.chat({ message: text });
            setLastAIResponse(response.response);
            addToTranscript('ai', response.response);
            speakText(response.response);
        } catch (error) {
            const errorMessage = 'Sorry, I encountered an error. Please try again.';
            setLastAIResponse(errorMessage);
            addToTranscript('ai', errorMessage);
            speakText(errorMessage);
        }
    };

    const speakText = (text: string) => {
        if (!synthesisRef.current) return;

        // Stop listening while speaking to avoid AI hearing itself
        if (recognitionRef.current) {
            try {
                recognitionRef.current.stop();
            } catch (e) { }
        }
        setIsListening(false);
        setIsSpeaking(true);

        synthesisRef.current.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        utterance.lang = 'en-US';

        // Simple voice selection
        const voices = synthesisRef.current.getVoices();
        const voice = voices.find(v => v.lang.startsWith('en')) || voices[0];
        if (voice) utterance.voice = voice;

        utterance.onend = () => {
            console.log('TTS Finished');
            setIsSpeaking(false);

            // CRITICAL: Resume listening immediately after speaking
            if (callState === 'connected') {
                console.log('Resuming listening after TTS...');
                setTimeout(() => startListening(), 200);
            }
        };

        utterance.onerror = (e) => {
            console.error('TTS Error:', e);
            setIsSpeaking(false);
            // Resume listening even on error
            if (callState === 'connected') {
                setTimeout(() => startListening(), 200);
            }
        };

        synthesisRef.current.speak(utterance);
    };

    const downloadTranscript = () => {
        if (transcript.length === 0) return;

        const date = new Date().toLocaleString();
        let content = `Call Transcript - ${date}\n`;
        content += `Duration: ${formatDuration(callDuration)}\n`;
        content += `----------------------------------------\n\n`;

        transcript.forEach(item => {
            const speaker = item.sender === 'user' ? 'You' : 'AI Assistant';
            content += `[${item.timestamp}] ${speaker}: ${item.text}\n\n`;
        });

        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `call_transcript_${new Date().getTime()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const handleEndCall = () => {
        stopAll();
        downloadTranscript(); // Auto-download transcript
        setCallState('ended');

        setTimeout(() => {
            setCallState('idle');
            setPhoneNumber('');
            setCallDuration(0);
            setCurrentTranscript('');
            setLastUserSpeech('');
            setLastAIResponse('');
            setError(null);
            setTranscript([]);
        }, 3000);
    };

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const formatPhoneNumber = (number: string) => {
        if (number.length <= 3) return number;
        if (number.length <= 6) return `(${number.slice(0, 3)}) ${number.slice(3)}`;
        return `(${number.slice(0, 3)}) ${number.slice(3, 6)}-${number.slice(6)}`;
    };

    return (
        <div className="voice-call-interface">
            <div className="call-container">
                {error && (
                    <div className="error-banner">
                        {error}
                        <button onClick={() => setError(null)}>✕</button>
                    </div>
                )}

                {/* Idle/Dialing State */}
                {(callState === 'idle' || callState === 'dialing') && (
                    <div className="dial-screen animate-fadeIn">
                        <div className="phone-display">
                            <div className="display-label">AI Voice Assistant</div>
                            <div className="phone-number">
                                {phoneNumber ? formatPhoneNumber(phoneNumber) : 'Tap to Call'}
                            </div>
                        </div>

                        <div className="dial-pad">
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, '*', 0, '#'].map((digit) => (
                                <button
                                    key={digit}
                                    className="dial-button"
                                    onClick={() => handleDialPad(digit.toString())}
                                    disabled={callState === 'dialing'}
                                >
                                    <span className="digit">{digit}</span>
                                </button>
                            ))}
                        </div>

                        <div className="call-actions">
                            {phoneNumber && (
                                <button className="backspace-button" onClick={handleBackspace}>
                                    ⌫
                                </button>
                            )}
                            <button
                                className="call-button"
                                onClick={handleCall}
                                disabled={callState === 'dialing'}
                            >
                                {callState === 'dialing' ? (
                                    <div className="spinner-small"></div>
                                ) : (
                                    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56-.35-.12-.74-.03-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z" />
                                    </svg>
                                )}
                            </button>
                        </div>
                    </div>
                )}

                {/* Calling State */}
                {callState === 'calling' && (
                    <div className="calling-screen animate-fadeIn">
                        <div className="calling-avatar">
                            <div className="avatar-ring animate-pulse"></div>
                            <div className="avatar-icon">AI</div>
                        </div>
                        <h2 className="calling-title">AI Assistant</h2>
                        <p className="calling-status">Connecting...</p>
                        <button className="end-call-button" onClick={handleEndCall}>
                            <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z" />
                            </svg>
                        </button>
                    </div>
                )}

                {/* Connected State - Voice Only */}
                {callState === 'connected' && (
                    <div className="connected-screen voice-only animate-fadeIn">
                        <div className="voice-status">
                            <div className="status-indicator">
                                <div className={`mic-icon ${isListening ? 'active' : ''}`} onClick={startListening}>
                                    <svg width="64" height="64" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                                        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                                    </svg>
                                </div>
                                <p className="status-text">
                                    {isSpeaking ? '🔊 AI Speaking...' : isListening ? '🎤 Listening...' : '⏸️ Tap Mic to Speak'}
                                </p>
                            </div>

                            <div className="audio-visualizer">
                                {[...Array(7)].map((_, i) => (
                                    <div
                                        key={i}
                                        className="visualizer-bar"
                                        style={{
                                            height: `${(isListening ? audioLevel * 100 : 20) + Math.random() * 20}%`,
                                            animationDelay: `${i * 0.1}s`
                                        }}
                                    />
                                ))}
                            </div>

                            {/* Text transcripts hidden for pure voice experience */}
                        </div>

                        <div className="call-info-bar">
                            <div className="call-duration-display">
                                {formatDuration(callDuration)}
                            </div>
                            <div className="connection-quality">
                                <div className="quality-dot"></div>
                                HD Voice
                            </div>
                        </div>

                        <div className="call-controls-bottom">
                            <button className="end-call-button-large" onClick={handleEndCall}>
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z" />
                                </svg>
                                <span>End Call</span>
                            </button>
                        </div>
                    </div>
                )}

                {/* Call Ended State */}
                {callState === 'ended' && (
                    <div className="ended-screen animate-fadeIn">
                        <h2>Call Ended</h2>
                        <p className="call-summary">Duration: {formatDuration(callDuration)}</p>
                        <p className="transcript-note">Transcript downloaded</p>
                    </div>
                )}
            </div>
        </div>
    );
}
