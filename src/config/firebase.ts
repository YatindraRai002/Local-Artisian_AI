import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyDrsyYPS6Rei_QwOhUh4imDHcr8zFkWBCY",
  authDomain: "artisian-ai-9377c.firebaseapp.com",
  projectId: "artisian-ai-9377c",
  storageBucket: "artisian-ai-9377c.firebasestorage.app",
  messagingSenderId: "626183905123",
  appId: "1:626183905123:web:4c800567262f5a785c3d56",
  measurementId: "G-BN7EZ4HF9N"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const analytics = getAnalytics(app);
export const googleProvider = new GoogleAuthProvider();

export default app;