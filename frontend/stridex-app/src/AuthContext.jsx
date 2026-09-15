import React, { createContext, useContext, useState, useCallback } from 'react';

const AuthContext = createContext(null);

const STORAGE_KEY_USER  = 'sx_user';
const STORAGE_KEY_TOKEN = 'sx_token';

export function AuthProvider({ children }) {
  const [user,  setUser]  = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY_USER)); }
    catch { return null; }
  });
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY_TOKEN));

  /** Call this after a successful login or registration */
  const signIn = useCallback((userData, tok) => {
    setUser(userData);
    setToken(tok);
    localStorage.setItem(STORAGE_KEY_USER,  JSON.stringify(userData));
    localStorage.setItem(STORAGE_KEY_TOKEN, tok);
  }, []);

  /** Alias so RegisterPage and LoginPage can both use the same name */
  const login = signIn;

  const signOut = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(STORAGE_KEY_USER);
    localStorage.removeItem(STORAGE_KEY_TOKEN);
  }, []);

  const isDoctor  = user?.role === 'doctor';
  const isPatient = user?.role === 'patient';

  return (
    <AuthContext.Provider value={{
      user, token, signIn, login, signOut,
      isAuthenticated: !!user,
      isDoctor, isPatient,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
