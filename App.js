import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

import Login from './components/Login';
import Dashboard from './components/Dashboard';
import VehicleList from './components/VehicleList';
import CargoList from './components/CargoList';
import LoadPlanList from './components/LoadPlanList';
import LoadPlanCreate from './components/LoadPlanCreate';
import LoadPlanDetail from './components/LoadPlanDetail';
import Navbar from './components/Navbar';

// Protected Route Component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return (
    <>
      <Navbar />
      {children}
    </>
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/vehicles" 
            element={
              <ProtectedRoute>
                <VehicleList />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/cargo" 
            element={
              <ProtectedRoute>
                <CargoList />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/load-plans" 
            element={
              <ProtectedRoute>
                <LoadPlanList />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/load-plan/create" 
            element={
              <ProtectedRoute>
                <LoadPlanCreate />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/load-plan/:id" 
            element={
              <ProtectedRoute>
                <LoadPlanDetail />
              </ProtectedRoute>
            } 
          />
          
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        
        <ToastContainer
          position="top-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </div>
    </Router>
  );
}

export default App;
