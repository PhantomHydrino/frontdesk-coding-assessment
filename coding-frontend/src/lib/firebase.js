// lib/firebase.ts
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: <API-KEY>,
  authDomain: <API-DOMAIN>,
  projectId: <PROJECT-ID>,
  storageBucket: <BUCKET-ID>,
  messagingSenderId: <SENDER-ID>,
  appId: <APP-ID>,
  measurementId: <MEASUREMENT-ID>
};

//all the details will be avialble for your project on firebase

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);