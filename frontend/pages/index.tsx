"use client";
import { useState, useMemo } from "react";
import axios from "axios";
import styles from "../styles/globals.module.css";

export default function Home() {
  const [urls, setUrls] = useState<string[]>([""]);
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [personality, setPersonality] = useState("formal");
  const [tooltip, setTooltip] = useState(""); // Tooltip state

  // Handle URL changes
  const handleUrlChange = (index: number, value: string) => {
    setUrls((prevUrls) => {
      const newUrls = [...prevUrls];
      newUrls[index] = value;
      return newUrls;
    });
  };

  // Add new URL input field
  const addUrlInput = () => setUrls([...urls, ""]);

  // Scrape URLs
  const scrapeUrls = async () => {
    setScraping(true);
    try {
      await axios.post("http://NEXT_PUBLIC_API_URL:8000/scrape", { urls, namespace: "scraped_content" });
      setResponse("✅ Scraping successful! ABEX Chat Bot is ready.");
    } catch (error) {
      setResponse("❌ Error scraping URLs");
    }
    setScraping(false);
  };

  // Ask AI Question
  const askQuestion = async () => {
    setLoading(true);
    try {
      const res = await axios.post("http://NEXT_PUBLIC_API_URL:8000/ask", { query, personality });
      setResponse(res.data.answer);
    } catch (error) {
      setResponse("❌ Error fetching AI response");
    }
    setLoading(false);
  };

  // ✅ Optimized AI Response Handling
  const formattedResponse = useMemo(() => {
    return response || "Your AI response will appear here...";
  }, [response]);

  // ✅ Optimize URL Input Rendering
  const urlInputs = useMemo(() => {
    return urls.map((url, index) => (
      <input
        key={index}
        type="url"
        placeholder={`Enter URL ${index + 1}`}
        value={url}
        onChange={(e) => handleUrlChange(index, e.target.value)}
        className="url-input"
      />
    ));
  }, [urls]);

  // ✅ Optimize Button Text to Avoid Re-Render
  const scrapeButtonText = useMemo(() => (scraping ? "⏳ Scraping..." : "🚀 Start Scraping"), [scraping]);
  const askButtonText = useMemo(() => (loading ? "⏳ Thinking..." : "🔎 Get Answer"), [loading]);

  return (
    <div className="chat-container">
      <h1 className="chat-header">💬 ABEX CHAT BOT</h1>

      <div className="chat-interface">
        {/* Scraping Section */}
        <div className="scraping-section">
          <h2 className="section-title">🌍 Scrape Web Data</h2>
          {urlInputs}
          <button onClick={addUrlInput} className="add-url-btn">➕ Add URL</button>
          <button onClick={scrapeUrls} className={`scrape-btn ${scraping ? "blinking" : ""}`}>
            {scrapeButtonText}
          </button>
        </div>

        {/* AI Chat Section */}
        <div className="chat-box">
          <h2 className="section-title">🤖 Chat with AI</h2>

          {/* Compact Personality Selection with Tooltip */}
          <div className="personality-container">
            <span className="personality-label">🎭 AI Mode:</span>
            <div className="personality-options">
              <button
                className={`personality-btn ${personality === "formal" ? "selected" : ""}`}
                onClick={() => setPersonality("formal")}
                onMouseEnter={() => setTooltip("🎓 Formal: Professional and structured responses")}
                onMouseLeave={() => setTooltip("")}
              >
                🎓
              </button>
              <button
                className={`personality-btn ${personality === "casual" ? "selected" : ""}`}
                onClick={() => setPersonality("casual")}
                onMouseEnter={() => setTooltip("😎 Casual: Friendly and relaxed conversation")}
                onMouseLeave={() => setTooltip("")}
              >
                😎
              </button>
              <button
                className={`personality-btn ${personality === "humorous" ? "selected" : ""}`}
                onClick={() => setPersonality("humorous")}
                onMouseEnter={() => setTooltip("🤡 Fun: Playful and humorous responses")}
                onMouseLeave={() => setTooltip("")}
              >
                🤡
              </button>
            </div>
            {/* Tooltip Display */}
            {tooltip && <div className="tooltip">{tooltip}</div>}
          </div>

          <input
            type="text"
            placeholder="Ask something..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="chat-input"
          />
          <button onClick={askQuestion} className="ask-btn">
            {askButtonText}
          </button>
          <div className="response-box">
            <p>{formattedResponse}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
