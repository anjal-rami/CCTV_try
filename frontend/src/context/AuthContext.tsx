import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // MUST initialize as null, NEVER mock admin objects
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const storedToken = localStorage.getItem("access_token");
    const storedUser = localStorage.getItem("auth_user");

    if (storedToken && storedUser) {
      try {
        const parsed: User = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(parsed);
      } catch (err) {
        console.error("Invalid session storage. Clearing credentials.", err);
        localStorage.removeItem("access_token");
        localStorage.removeItem("auth_user");
        setToken(null);
        setUser(null);
      }
    } else {
      setToken(null);
      setUser(null);
    }
    setIsLoading(false);
  }, []);

  const login = (authenticatedUser: User, accessToken: string) => {
    setUser(authenticatedUser);
    setToken(accessToken);
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("auth_user", JSON.stringify(authenticatedUser));
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("access_token");
    localStorage.removeItem("auth_user");
    localStorage.removeItem("active_tab");
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
