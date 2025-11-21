import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const reviewCode = async () => {
    if (!code.trim()) return alert("Write some code first!");

    setLoading(true);
    try {
      const response = await axios.post("http://127.0.0.1:8000/api/review", {
        filename: "example.py",
        language: "python",
        code: code,
      });
      setResult(response.data);
    } catch (error) {
      alert("Error connecting to backend 😢");
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <div className="app">
      <h1>⚡ Codexa AI Code Reviewer</h1>

      <textarea
        placeholder="Paste your code here..."
        value={code}
        onChange={(e) => setCode(e.target.value)}
      ></textarea>

      <button onClick={reviewCode} disabled={loading}>
        {loading ? "Analyzing..." : "🔍 Review Code"}
      </button>

      {result && (
        <div className="result">
          <h2>🧾 Summary</h2>
          <p>{result.summary}</p>

          <h2>🛠️ Issues ({result.issues.length})</h2>
          {result.issues.map((issue: any, index: number) => (
            <div key={index} className="issue">
              <p>
                <b>Line:</b> {issue.line}
              </p>
              <p>
                <b>Severity:</b> {issue.severity}
              </p>
              <p>
                <b>{issue.description}</b>
              </p>
              <p>
                <i>{issue.suggestion}</i>
              </p>
            </div>
          ))}

          <h2>🏆 Score: {result.score}</h2>
        </div>
      )}
    </div>
  );
}

export default App;
