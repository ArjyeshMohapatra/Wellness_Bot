import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const ForgotPassword: React.FC = () => {
    const [email, setEmail] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const handleEmailSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setMessage('');
        setNewPassword('');

        try {
            const response = await fetch('http://localhost:8001/api/admin/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                setNewPassword(data.new_password);
                setMessage('Password reset successful! Your new password is shown below.');
                setShowPassword(true);
            } else {
                setError(data.message || 'Password reset failed');
            }
        } catch (error) {
            setError('Network error. Please check if the API server is running on port 8001.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="d-flex align-items-center justify-content-center min-vh-100" style={{
            backgroundImage: "url('/public/OIP.jpeg')",
            backgroundSize: "cover", backgroundPosition: "center",
            backgroundRepeat: "no-repeat"
        }}>
            <div className="container">
                <div className="row justify-content-center">
                    <div className="col-md-6">
                        <div className="card" style={{
                            backdropFilter: "blur(20px)",
                            backgroundColor: "rgba(255, 255, 255, 0.5)",
                            border: "1px solid var(--glass-border)",
                            borderRadius: "15px",
                            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)"
                        }}>
                            <div className="card-body p-4">
                                <h2 className="card-title text-center mb-4">Reset Password</h2>

                                {!showPassword ? (
                                    <form onSubmit={handleEmailSubmit}>
                                        <div className="mb-3">
                                            <label htmlFor="email" className="form-label">Email Address</label>
                                            <input
                                                type="email"
                                                className="form-control"
                                                id="email"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                required
                                            />
                                        </div>

                                        {error && (
                                            <div className="alert alert-danger" role="alert">
                                                {error}
                                            </div>
                                        )}

                                        {message && (
                                            <div className="alert alert-success" role="alert">
                                                {message}
                                            </div>
                                        )}

                                        <button
                                            type="submit"
                                            className="btn btn-primary w-100"
                                            disabled={loading}
                                        >
                                            {loading ? 'Resetting...' : 'Reset Password'}
                                        </button>
                                    </form>
                                ) : (
                                    <div className="text-center">
                                        <div className="alert alert-success" role="alert">
                                            <h5>Password Reset Complete!</h5>
                                            <p>Your new password is:</p>
                                            <h3 className="text-primary">{newPassword}</h3>
                                            <small className="text-muted">Save this password - it's shown only once!</small>
                                        </div>

                                        <Link to="/login" className="btn btn-primary">
                                            Go to Login
                                        </Link>
                                    </div>
                                )}

                                <div className="text-center mt-3">
                                    <Link to="/login" className="text-decoration-none">
                                        Back to Login
                                    </Link>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;