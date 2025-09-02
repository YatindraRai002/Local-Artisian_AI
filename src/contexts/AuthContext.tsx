import React, { createContext, useContext, useEffect, useState } from 'react';
import { 
  User, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged
} from 'firebase/auth';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { auth, googleProvider, db } from '../config/firebase';

export type UserType = 'user' | 'artist';

export interface UserProfile {
  uid: string;
  email: string;
  userType: UserType;
  displayName?: string;
  phone?: string;
  craftType?: string;
  location?: {
    state: string;
    district: string;
    village: string;
  };
  createdAt: Date;
}

interface AuthContextType {
  currentUser: User | null;
  userProfile: UserProfile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, userType: UserType, additionalInfo?: Partial<UserProfile>) => Promise<void>;
  loginWithGoogle: (userType: UserType) => Promise<void>;
  logout: () => Promise<void>;
  updateUserProfile: (data: Partial<UserProfile>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  async function signup(email: string, password: string, userType: UserType, additionalInfo: Partial<UserProfile> = {}) {
    const result = await createUserWithEmailAndPassword(auth, email, password);
    
    // Create user profile in Firestore
    const profile: UserProfile = {
      uid: result.user.uid,
      email: result.user.email!,
      userType,
      displayName: result.user.displayName || additionalInfo.displayName || '',
      phone: additionalInfo.phone || '',
      craftType: additionalInfo.craftType || '',
      location: additionalInfo.location || { state: '', district: '', village: '' },
      createdAt: new Date()
    };

    await setDoc(doc(db, 'users', result.user.uid), profile);
    setUserProfile(profile);
  }

  async function login(email: string, password: string) {
    await signInWithEmailAndPassword(auth, email, password);
  }

  async function loginWithGoogle(userType: UserType) {
    const result = await signInWithPopup(auth, googleProvider);
    
    // Check if user profile exists
    const userDoc = await getDoc(doc(db, 'users', result.user.uid));
    
    if (!userDoc.exists()) {
      // Create profile for new Google user
      const profile: UserProfile = {
        uid: result.user.uid,
        email: result.user.email!,
        userType,
        displayName: result.user.displayName || '',
        phone: '',
        craftType: '',
        location: { state: '', district: '', village: '' },
        createdAt: new Date()
      };

      await setDoc(doc(db, 'users', result.user.uid), profile);
      setUserProfile(profile);
    }
  }

  async function logout() {
    await signOut(auth);
    setUserProfile(null);
  }

  async function updateUserProfile(data: Partial<UserProfile>) {
    if (!currentUser || !userProfile) return;

    const updatedProfile = { ...userProfile, ...data };
    await setDoc(doc(db, 'users', currentUser.uid), updatedProfile);
    setUserProfile(updatedProfile);
  }

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      
      if (user) {
        // Fetch user profile from Firestore
        const userDoc = await getDoc(doc(db, 'users', user.uid));
        if (userDoc.exists()) {
          setUserProfile(userDoc.data() as UserProfile);
        }
      } else {
        setUserProfile(null);
      }
      
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const value: AuthContextType = {
    currentUser,
    userProfile,
    loading,
    signup,
    login,
    loginWithGoogle,
    logout,
    updateUserProfile
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}