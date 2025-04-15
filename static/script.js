const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const submitBtn = document.getElementById("submit-btn");
const recordBtn = document.getElementById("record-btn");
const stopBtn = document.getElementById("stop-btn");
const audioPlayer = document.getElementById("audio-player");

const homeDiv = document.getElementById("home");
const chatContainer = document.getElementById("chat-container");

let mediaRecorder;
let audioChunks = [];

// Append a new message bubble to the chat box
function addMessage(sender, text) {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("message");
  msgDiv.classList.add(sender === "user" ? "user-msg" : "bot-msg");
  msgDiv.textContent = text;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Hide home greeting and reveal chat interface
function showChat() {
  homeDiv.classList.add("hidden");
  chatContainer.classList.remove("hidden");
}

// Handle text submission
submitBtn.onclick = async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;
  addMessage("user", text);
  userInput.value = "";
  showChat();

  const res = await fetch("/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  });

  const data = await res.json();
  addMessage("bot", data.response);
  showEmotionAnimation(data.tone);  // Updated
  playAudio();
};

// Handle voice recording
recordBtn.onclick = async () => {
  audioChunks = [];
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
  mediaRecorder.start();
  recordBtn.disabled = true;
  stopBtn.disabled = false;
};

stopBtn.onclick = () => {
  mediaRecorder.stop();
  recordBtn.disabled = false;
  stopBtn.disabled = true;

  mediaRecorder.onstop = async () => {
    const blob = new Blob(audioChunks, { type: "audio/wav" });
    const formData = new FormData();
    formData.append("audio", blob, "input.wav");

    const res = await fetch("/audio", { method: "POST", body: formData });
    const data = await res.json();

    if (data.transcription) addMessage("user", data.transcription);
    addMessage("bot", data.response);
    showEmotionAnimation(data.tone);  // Updated
    showChat();
    playAudio();
  };
};

// Play TTS audio with cache-busting
function playAudio() {
  const audio = new Audio("/static/response.mp3?t=" + new Date().getTime());
  audio.play();
}

// Auto-grow the textarea
userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = userInput.scrollHeight + "px";
});

// Show emotion animation
function showEmotionAnimation(tone) {
  const player = document.getElementById('emotion-player');
  const emotionLottieMap = {
    happy: "https://lottie.host/c39b9f0c-5181-4932-b3c4-c6ab2d8160b1/i5FED40sdb.json",
    sad: "https://lottie.host/012409ef-100f-4f0c-bc9f-c1f9dc66c601/fv2HAzueT0.json",
    friendly: "https://lottie.host/290cb4cf-3c2c-4276-9d46-ec4fd57d9c2b/uvZugZxoKV.json",
    thinking: "https://lottie.host/fa9bf99b-d611-46a8-b73d-2eb48d54ae08/bQiaozQwuq.json",
    angry: "https://lottie.host/3e4b40df-0e7f-423d-896e-0f29dca82dfe/Bykvs1Jisb.json"
  };
  const selectedTone = tone || "thinking";
  const animationUrl = emotionLottieMap[selectedTone] || emotionLottieMap["thinking"];
  player.load(animationUrl);
}