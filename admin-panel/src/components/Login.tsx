import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [dateOfBirth, setDateOfBirth] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [isSignUp, setIsSignUp] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // Phone number validation
        const phoneRegex = /^\d{10}$/;
        if (isSignUp && phoneNumber && !phoneRegex.test(phoneNumber.replace(/\s/g, ''))) {
            setError('Please enter a valid 10-digit phone number (e.g., 1234567890)');
            setLoading(false);
            return;
        }

        // Password confirmation validation
        if (isSignUp && password !== confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        try {
            const endpoint = isSignUp ? '/api/admin/register' : '/api/admin/login';
            const requestBody = isSignUp
                ? {
                    email,
                    password,
                    first_name: firstName,
                    last_name: lastName,
                    date_of_birth: dateOfBirth,
                    phone_number: phoneNumber
                }
                : { email, password };

            const response = await fetch(`http://localhost:8001${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();
            console.log('Login response status:', response.status, 'ok:', response.ok);
            console.log('Login response data:', data);

            if (response.status === 200 && data.success === true) {
                console.log('Login successful, user data:', data.user);
                localStorage.setItem('isLoggedIn', 'true');
                localStorage.setItem('adminEmail', email);
                if (data.user) {
                    localStorage.setItem('userId', data.user.id.toString());
                    localStorage.setItem('userRole', data.user.role);
                    console.log('Stored userId:', data.user.id);
                } else {
                    console.error('No user data in response');
                }
                navigate('/dashboard');
            } else {
                console.log('Login failed with status:', response.status, 'data:', data);
                setError(data.message || 'Authentication failed');
            }
        } catch (error) {
            setError('Network error. Please check if the API server is running on port 8001.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="d-flex align-items-center justify-content-center py-4" style={{
            minHeight: "100vh",
            backgroundImage: "url('/public/OIP.jpeg')",
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat"
        }}>
            <div className="container">
                <div className="row justify-content-center">
                    <div className="col-sm-8 col-md-6 col-lg-8">
                        <div className="card" style={{
                            backdropFilter: "blur(20px)",
                            backgroundColor: "rgba(255, 255, 255, 0.5)",
                            border: "1px solid var(--glass-border)",
                            borderRadius: "15px",
                            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)"
                        }}>
                            <div className="card-body">
                                <h2 className="card-title text-center mb-3" style={{
                                    backgroundColor: "var(--light-primary)",
                                    color: "white",
                                    padding: "12px 20px",
                                    margin: "-16px -16px 20px -16px",
                                    borderRadius: "12px 12px 0 0",
                                    fontWeight: "600",
                                    boxShadow: "0 2px 4px rgba(0,123,255,0.3)",
                                }}>{isSignUp ? 'Admin Sign Up' : 'Admin Login'}</h2>

                                {error && (
                                    <div className="alert alert-danger" role="alert">
                                        {error}
                                    </div>
                                )}

                                <form onSubmit={handleSubmit}>
                                    {!isSignUp && (
                                        <div className="mb-3">
                                            <label htmlFor="email" className="form-label fw-semibold">Email Address</label>
                                            <input type="email"
                                                className="form-control"
                                                id="email" value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                placeholder="Enter your email"
                                                required
                                                disabled={loading}
                                                style={{
                                                    border: "1px solid var(--glass-border)",
                                                    borderRadius: "8px",
                                                    padding: "0.75rem"
                                                }} />
                                        </div>
                                    )}

                                    {isSignUp && (
                                        <>
                                            <div className="mb-3">
                                                <h5 className="text-muted mb-3 fw-bold" style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                                    Account Information
                                                </h5>
                                                <div className="row">
                                                    <div className="col-md-4 mb-1">
                                                        <label htmlFor="firstName" className="form-label fw-semibold">First Name</label>
                                                        <input type="text"
                                                            className="form-control"
                                                            id="firstName" value={firstName}
                                                            onChange={(e) => setFirstName(e.target.value)}
                                                            placeholder="Enter first name"
                                                            required
                                                            disabled={loading}
                                                            style={{
                                                                border: "1px solid var(--glass-border)",
                                                                borderRadius: "8px",
                                                                padding: "0.75rem"
                                                            }} />
                                                    </div>
                                                    <div className="col-md-4 mb-1">
                                                        <label htmlFor="lastName" className="form-label fw-semibold">Last Name</label>
                                                        <input type="text"
                                                            className="form-control"
                                                            id="lastName" value={lastName}
                                                            onChange={(e) => setLastName(e.target.value)}
                                                            placeholder="Enter last name"
                                                            required
                                                            disabled={loading}
                                                            style={{
                                                                border: "1px solid var(--glass-border)",
                                                                borderRadius: "8px",
                                                                padding: "0.75rem"
                                                            }} />
                                                    </div>
                                                    <div className="col-md-4 mb-1">
                                                        <label htmlFor="dateOfBirth" className="form-label fw-semibold">Date of Birth</label>
                                                        <input type="date"
                                                            className="form-control"
                                                            id="dateOfBirth" value={dateOfBirth}
                                                            onChange={(e) => setDateOfBirth(e.target.value)}
                                                            required
                                                            disabled={loading}
                                                            style={{
                                                                border: "1px solid var(--glass-border)",
                                                                borderRadius: "8px",
                                                                padding: "0.75rem"
                                                            }} />
                                                    </div>
                                                </div>
                                                <div className="row mt-2">
                                                    <div className="col-md-6 mb-1">
                                                        <label htmlFor="phoneNumber" className="form-label fw-semibold">Phone Number</label>
                                                        <input type="tel"
                                                            className="form-control"
                                                            id="phoneNumber" value={phoneNumber}
                                                            onChange={(e) => setPhoneNumber(e.target.value)}
                                                            placeholder="1234567890"
                                                            maxLength={10}
                                                            required
                                                            disabled={loading}
                                                            style={{
                                                                border: "1px solid var(--glass-border)",
                                                                borderRadius: "8px",
                                                                padding: "0.75rem"
                                                            }} />
                                                    </div>
                                                    <div className="col-md-6 mb-1">
                                                        <label htmlFor="email" className="form-label fw-semibold">Email Address</label>
                                                        <input type="email"
                                                            className="form-control"
                                                            id="email" value={email}
                                                            onChange={(e) => setEmail(e.target.value)}
                                                            placeholder="Enter your email"
                                                            required
                                                            disabled={loading}
                                                            style={{
                                                                border: "1px solid var(--glass-border)",
                                                                borderRadius: "8px",
                                                                padding: "0.75rem"
                                                            }} />
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="mb-1">
                                                <div className="row">
                                                    <div className="col-md-6 mb-2">
                                                        <label htmlFor="password" className="form-label fw-semibold">Password</label>
                                                        <input type="password"
                                                            className="form-control"
                                                            id="password" value={password}
                                                            onChange={(e) => setPassword(e.target.value)}
                                                            placeholder="Create a strong password"
                                                            required
                                                            disabled={loading}
                                                            style={{
                                                                border: "1px solid var(--glass-border)",
                                                                borderRadius: "8px",
                                                                padding: "0.75rem"
                                                            }} />
                                                    </div>
                                                    <div className="col-md-6 mb-1">
                                                        <label htmlFor="confirmPassword" className="form-label fw-semibold">Confirm Password</label>
                                                        <input type="password"
                                                            className="form-control"
                                                            id="confirmPassword" value={confirmPassword}
                                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                                            placeholder="Confirm your password"
                                                            required
                                                            disabled={loading}
                                                            style={{
                                                                border: "1px solid var(--glass-border)",
                                                                borderRadius: "8px",
                                                                padding: "0.75rem"
                                                            }} />
                                                    </div>
                                                </div>
                                            </div>
                                        </>
                                    )}

                                    {!isSignUp && (
                                        <div className="mb-2">
                                            <label htmlFor="password" className="form-label fw-semibold">Password</label>
                                            <input type="password"
                                                className="form-control"
                                                id="password" value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                placeholder="Enter your password"
                                                required
                                                disabled={loading}
                                                style={{
                                                    border: "1px solid var(--glass-border)",
                                                    borderRadius: "8px",
                                                    padding: "0.75rem"
                                                }} />
                                        </div>
                                    )}
                                    <div className="d-grid gap-2">
                                        <button type="submit" className="btn btn-primary" disabled={loading}>
                                            {loading ? 'Please wait...' : (isSignUp ? 'Sign Up' : 'Sign In')}
                                        </button>
                                        <button
                                            type="button"
                                            className="btn btn-outline-secondary"
                                            onClick={() => {
                                                setIsSignUp(!isSignUp);
                                                setFirstName('');
                                                setLastName('');
                                                setDateOfBirth('');
                                                setPhoneNumber('');
                                                setPassword('');
                                                setConfirmPassword('');
                                                setError('');
                                            }}
                                            disabled={loading}
                                        >
                                            {isSignUp ? 'Already have an account? Sign In' : 'Need an account? Sign Up'}
                                        </button>
                                    </div>
                                </form>
                                <div className="text-center mt-2">
                                    <Link to="/forgot-password">Forgot Password?</Link>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div >
        </div >
    );
};

export default Login;