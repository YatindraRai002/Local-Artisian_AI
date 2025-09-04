import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { Login } from './components/Login';
import { ArtistDashboard } from './components/ArtistDashboard';
import { UserDashboard } from './components/UserDashboard';
import { Loader2 } from 'lucide-react';

// Loading component
const LoadingScreen: React.FC = () => (
  <div className="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 flex items-center justify-center">
    <div className="text-center">
      <Loader2 className="w-12 h-12 text-orange-600 animate-spin mx-auto mb-4" />
      <p className="text-gray-600">Loading Kala-Kaart...</p>
    </div>
  </div>
);

// Protected Route component
const ProtectedRoute: React.FC<{ 
  children: React.ReactNode; 
  requiredUserType?: 'user' | 'artist' 
}> = ({ children, requiredUserType }) => {
  const { currentUser, userProfile } = useAuth();
  
  if (!currentUser || !userProfile) {
    return <Navigate to="/login" replace />;
  }
  
  if (requiredUserType && userProfile.userType !== requiredUserType) {
    // Redirect to appropriate dashboard based on user type
    return <Navigate to={userProfile.userType === 'artist' ? '/artist' : '/dashboard'} replace />;
  }
  
  return <>{children}</>;
};

function App() {
  const { currentUser, userProfile, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={
          currentUser ? (
            <Navigate to={userProfile?.userType === 'artist' ? '/artist' : '/dashboard'} replace />
          ) : (
            <Login />
          )
        } 
      />
      
      <Route 
        path="/artist" 
        element={
          <ProtectedRoute requiredUserType="artist">
            <ArtistDashboard />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute requiredUserType="user">
            <UserDashboard />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path="/" 
        element={
          currentUser ? (
            <Navigate to={userProfile?.userType === 'artist' ? '/artist' : '/dashboard'} replace />
          ) : (
            <Navigate to="/login" replace />
          )
        } 
      />
      
      {/* Catch all route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;