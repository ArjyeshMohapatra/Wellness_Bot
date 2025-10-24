import React from 'react';

const DeveloperView: React.FC = () => {
    // Mock admin data
    const admins = [
        { id: 1, email: 'admin1@example.com', plan: '1 Month', members: 50, license: 'ABC123' },
        { id: 2, email: 'admin2@example.com', plan: '2 Months', members: 100, license: 'DEF456' },
    ];

    return (
        <div className="container mt-5">
            <h2 className="mb-4">Developer View - Admin Data</h2>
            <table className="table table-striped">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Email</th>
                        <th>Plan</th>
                        <th>Max Members</th>
                        <th>License Key</th>
                    </tr>
                </thead>
                <tbody>
                    {admins.map(admin => (
                        <tr key={admin.id}>
                            <td>{admin.id}</td>
                            <td>{admin.email}</td>
                            <td>{admin.plan}</td>
                            <td>{admin.members}</td>
                            <td>{admin.license}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <a href="/dashboard" className="btn btn-secondary">Back to Dashboard</a>
        </div>
    );
};

export default DeveloperView;