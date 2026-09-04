import { initializeApp } from "firebase/app";
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut,
  onAuthStateChanged 
} from "firebase/auth";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCGApzv-zRbif9LTYKhIGvr73uDaY3chuU",
  authDomain: "recreation-engine.firebaseapp.com",
  databaseURL: "https://recreation-engine-default-rtdb.firebaseio.com",
  projectId: "recreation-engine",
  storageBucket: "recreation-engine.firebasestorage.app",
  messagingSenderId: "748379597599",
  appId: "1:748379597599:web:3fc7bec636bec0dc75de2a",
  measurementId: "G-VTMMRWZPWE"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged 
};
