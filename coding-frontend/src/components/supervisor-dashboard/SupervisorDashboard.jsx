import { useEffect, useState } from "react";
import {db} from '../../lib/firebase'
import { collection, getDocs, doc, updateDoc } from "firebase/firestore";
import "./style/style.css";

export default function SupervisorDashboard() {
  const [requests, setRequests] = useState([]);
  const [responses, setResponses] = useState({});

  useEffect(() => {
    fetchRequests();
  }, []);

  async function fetchRequests() {
    const querySnapshot = await getDocs(collection(db, "help_requests"));
    const data = [];
    querySnapshot.forEach((doc) => {
      data.push({ id: doc.id, ...doc.data() });
    });
    setRequests(data);
  }

  async function submitResponse(id) {
    const response = responses[id];
    await updateDoc(doc(db, "help_requests", id), {
      supervisor_response: response,
      status: "resolved",
    });
    fetchRequests();
  }

  return (
    <div className="dashboard-container">
      {requests.map((req) => (
        <div key={req.id} className="card">
          <div className="card-content">
            <div>
              <strong>Question:</strong> {req.question}
            </div>
            <div>
              <strong>Status:</strong> {req.status}
            </div>

            {req.status === "pending" && (
              <>
                <textarea
                  placeholder="Enter your response..."
                  value={responses[req.id] || ""}
                  onChange={(e) =>
                    setResponses({ ...responses, [req.id]: e.target.value })
                  }
                />
                <button onClick={() => submitResponse(req.id)}>
                  Submit Response
                </button>
              </>
            )}

            {req.status === "resolved" && (
              <div>
                <strong>Response:</strong> {req.supervisor_response}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
