import React, { useState } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// SignUp Component
const SignUp = ({ onSignupSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    goals: ['', '', ''],
    reminder_times: ['09:00', '14:00', '20:00']
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleGoalChange = (index, value) => {
    const newGoals = [...formData.goals];
    newGoals[index] = value;
    setFormData(prev => ({ ...prev, goals: newGoals }));
  };

  const handleTimeChange = (index, value) => {
    const newTimes = [...formData.reminder_times];
    newTimes[index] = value;
    setFormData(prev => ({ ...prev, reminder_times: newTimes }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Filter out empty goals
      const cleanGoals = formData.goals.filter(goal => goal.trim() !== '');
      
      if (cleanGoals.length === 0) {
        throw new Error('Please enter at least one goal');
      }

      const submitData = {
        ...formData,
        goals: cleanGoals,
        phone: formData.phone.startsWith('+') ? formData.phone : `+${formData.phone}`
      };

      const response = await axios.post(`${API}/users/signup`, submitData);
      console.log('Signup successful:', response.data);
      onSignupSuccess(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Signup failed');
      console.error('Signup error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">🔒</div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome to LockedIn</h1>
          <p className="text-gray-600">Your AI-powered goal reminder companion</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Info */}
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Enter your name"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="your@email.com"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              WhatsApp Phone Number
            </label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="+1234567890 (include country code)"
              required
            />
            <p className="text-sm text-gray-500 mt-1">
              📱 Remember to join our WhatsApp sandbox by sending "join adjective-engine" to +14155238886
            </p>
          </div>

          {/* Goals Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              🎯 Your 3 Goals
            </label>
            <div className="space-y-3">
              {[0, 1, 2].map((index) => (
                <input
                  key={index}
                  type="text"
                  value={formData.goals[index]}
                  onChange={(e) => handleGoalChange(index, e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder={`Goal ${index + 1} (e.g., Exercise for 30 minutes)`}
                />
              ))}
            </div>
          </div>

          {/* Reminder Times */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              ⏰ Reminder Times (GMT+1)
            </label>
            <div className="grid grid-cols-3 gap-4">
              {[0, 1, 2].map((index) => (
                <div key={index}>
                  <label className="block text-xs text-gray-500 mb-1">
                    Reminder {index + 1}
                  </label>
                  <input
                    type="time"
                    value={formData.reminder_times[index]}
                    onChange={(e) => handleTimeChange(index, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Setting up your goals...
              </span>
            ) : (
              'Get LockedIn 🔒'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

// Success Component
const Success = ({ user, onManageReminders }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-400 via-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-2xl text-center">
        <div className="text-6xl mb-6">🎉</div>
        <h1 className="text-3xl font-bold text-gray-800 mb-4">Welcome to LockedIn, {user.name}!</h1>
        <p className="text-gray-600 mb-8">You're all set! Here's what happens next:</p>
        
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-blue-50 p-6 rounded-xl">
            <div className="text-3xl mb-3">📧</div>
            <h3 className="font-semibold text-gray-800 mb-2">Check Your Email</h3>
            <p className="text-sm text-gray-600">We've sent you a welcome email with all your goal details</p>
          </div>
          <div className="bg-green-50 p-6 rounded-xl">
            <div className="text-3xl mb-3">📱</div>
            <h3 className="font-semibold text-gray-800 mb-2">Join WhatsApp</h3>
            <p className="text-sm text-gray-600">Send "join adjective-engine" to +14155238886 to receive reminders</p>
          </div>
          <div className="bg-purple-50 p-6 rounded-xl">
            <div className="text-3xl mb-3">⏰</div>
            <h3 className="font-semibold text-gray-800 mb-2">Daily Reminders</h3>
            <p className="text-sm text-gray-600">You'll get reminders at your scheduled times</p>
          </div>
        </div>

        <div className="bg-gray-50 p-6 rounded-xl mb-6">
          <h3 className="font-semibold text-gray-800 mb-4">Your Goals & Reminder Times:</h3>
          <div className="space-y-2">
            {user.goals.map((goal, index) => (
              <div key={index} className="flex justify-between items-center bg-white p-3 rounded-lg">
                <span className="text-gray-700">{goal}</span>
                <span className="text-purple-600 font-medium">{user.reminder_times[index] || 'No time set'}</span>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={onManageReminders}
          className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold py-3 px-8 rounded-lg hover:from-purple-700 hover:to-indigo-700 transition duration-200"
        >
          Manage Reminder Times
        </button>
      </div>
    </div>
  );
};

// Manage Reminders Component
const ManageReminders = ({ user, onBack }) => {
  const [reminderTimes, setReminderTimes] = useState(user.reminder_times);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleTimeChange = (index, value) => {
    const newTimes = [...reminderTimes];
    newTimes[index] = value;
    setReminderTimes(newTimes);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await axios.put(`${API}/users/reminder-times`, {
        phone: user.phone,
        reminder_times: reminderTimes
      });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update reminder times');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-xl">
        <div className="text-center mb-6">
          <div className="text-4xl mb-4">⏰</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Manage Reminder Times</h1>
          <p className="text-gray-600">Update when you want to receive your daily reminders</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {user.goals.map((goal, index) => (
            <div key={index} className="bg-gray-50 p-4 rounded-lg">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Goal {index + 1}: {goal}
              </label>
              <input
                type="time"
                value={reminderTimes[index] || ''}
                onChange={(e) => handleTimeChange(index, e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          ))}

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-green-600 text-sm">✅ Reminder times updated successfully!</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <div className="flex space-x-4">
            <button
              type="button"
              onClick={onBack}
              className="flex-1 bg-gray-500 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-600 transition duration-200"
            >
              Back
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 transition duration-200"
            >
              {loading ? 'Updating...' : 'Update Times'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('signup'); // 'signup', 'success', 'manage'
  const [user, setUser] = useState(null);

  const handleSignupSuccess = (userData) => {
    setUser(userData);
    setCurrentView('success');
  };

  const handleManageReminders = () => {
    setCurrentView('manage');
  };

  const handleBack = () => {
    setCurrentView('success');
  };

  return (
    <div className="App">
      {currentView === 'signup' && (
        <SignUp onSignupSuccess={handleSignupSuccess} />
      )}
      {currentView === 'success' && user && (
        <Success user={user} onManageReminders={handleManageReminders} />
      )}
      {currentView === 'manage' && user && (
        <ManageReminders user={user} onBack={handleBack} />
      )}
    </div>
  );
}

export default App;
