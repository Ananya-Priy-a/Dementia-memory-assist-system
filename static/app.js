const video = document.getElementById("video");
const overlay = document.getElementById("overlay");
const ctx = overlay.getContext("2d");

const card = document.getElementById("memory-card");
const cardName = document.getElementById("card-name");
const cardRelationship = document.getElementById("card-relationship");
const cardSummary = document.getElementById("card-summary");
const statusPill = document.getElementById("status-pill");
const recordingIndicator = document.getElementById("recording-indicator");
const stopVideoBtn = document.getElementById("stop-video-btn");
const raybanModeBtn = document.getElementById("rayban-mode-btn");
const micBtn = document.getElementById("mic-btn");

// Registration modal elements
const registrationModal = document.getElementById("registration-modal");
const personNameInput = document.getElementById("person-name");
const personRelationInput = document.getElementById("person-relation");
const registerConfirmBtn = document.getElementById("register-confirm-btn");
const registerCancelBtn = document.getElementById("register-cancel-btn");

let detectTimer = null;
let currentPersonId = null;
let lastBbox = null;

let audioRecorder = null;
let audioChunks = [];
let audioStream = null;
let recordingPersonId = null;
let recordingTimeout = null;

let isCameraRunning = false;
let isRayBanMode = false;
let isMicMuted = false;

// State for unknown person registration
let unknownPersonCanvas = null;
let unknownPersonScore = null;
let lastUnknownPersonTime = 0;

const DETECT_INTERVAL_MS = 1600;
const RECORD_WINDOW_MS = 32000; // ~30s demo window
const UNKNOWN_PERSON_THRESHOLD = 0.4; // Show registration if similarity < 40%
const UNKNOWN_PERSON_COOLDOWN_MS = 5000; // Prevent repeated prompts

function setStatus(text) {
  statusPill.textContent = text;
}

function toggleCamera() {
  if (isCameraRunning) {
    stopCamera();
  } else {
    startCamera();
  }
}

function stopCamera() {
  // Stop all video tracks
  const stream = video.srcObject;
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }
  
  // Stop detection loop
  if (detectTimer) {
    clearInterval(detectTimer);
    detectTimer = null;
  }
  
  // Stop recording if active
  if (audioRecorder && audioRecorder.state !== "inactive") {
    audioRecorder.stop();
  }
  
  if (audioStream) {
    audioStream.getTracks().forEach(track => track.stop());
  }
  
  // Hide memory card
  hideCard();
  
  isCameraRunning = false;
  setStatus("Camera stopped");
  video.srcObject = null;
  stopVideoBtn.textContent = "Start Video";
  stopVideoBtn.classList.remove("active");
}

function toggleRayBanMode() {
  isRayBanMode = !isRayBanMode;
  
  if (isRayBanMode) {
    setStatus("Ray-Ban Mode activated");
    raybanModeBtn.textContent = "Exit Ray-Ban Mode";
    raybanModeBtn.classList.add("active");
  } else {
    setStatus("Ray-Ban Mode deactivated");
    raybanModeBtn.textContent = "Enter Ray-Ban Mode";
    raybanModeBtn.classList.remove("active");
  }
}

function toggleMicrophone() {
  isMicMuted = !isMicMuted;
  
  if (isMicMuted) {
    setStatus("Microphone muted");
    micBtn.textContent = "🎤 Off";
    micBtn.classList.add("muted");
    micBtn.classList.remove("active");
    
    // Stop recording if active
    if (audioRecorder && audioRecorder.state !== "inactive") {
      audioRecorder.stop();
    }
  } else {
    setStatus("Microphone on");
    micBtn.textContent = "🎤 On";
    micBtn.classList.remove("muted");
    micBtn.classList.add("active");
    
    // Restart recording if a face is currently recognized
    if (currentPersonId) {
      maybeStartRecording(currentPersonId);
    }
  }
}

stopVideoBtn.addEventListener("click", toggleCamera);
raybanModeBtn.addEventListener("click", toggleRayBanMode);
micBtn.addEventListener("click", toggleMicrophone);

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    video.srcObject = stream;
    await video.play();
    isCameraRunning = true;
    resizeOverlay();
    window.addEventListener("resize", resizeOverlay);
    setStatus("Camera on");
    stopVideoBtn.textContent = "Stop Video";
    stopVideoBtn.classList.add("active");
    startDetectLoop();
  } catch (err) {
    console.error(err);
    isCameraRunning = false;
    setStatus("Camera permission needed");
    stopVideoBtn.textContent = "Start Video";
    stopVideoBtn.classList.remove("active");
  }
}

function resizeOverlay() {
  overlay.width = video.videoWidth || 1280;
  overlay.height = video.videoHeight || 720;
}

function drawBoxes(allBboxes) {
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  if (!allBboxes || allBboxes.length === 0) return;
  
  allBboxes.forEach((bbox, index) => {
    // Different colors for each detected face
    const colors = [
      "rgba(122, 181, 255, 0.8)",  // Blue
      "rgba(255, 193, 7, 0.8)",    // Gold
      "rgba(76, 175, 80, 0.8)",    // Green
      "rgba(244, 67, 54, 0.8)",    // Red
    ];
    
    ctx.strokeStyle = colors[index % colors.length];
    ctx.lineWidth = 3;
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(bbox.x, bbox.y, bbox.w, bbox.h, 12);
    } else {
      ctx.rect(bbox.x, bbox.y, bbox.w, bbox.h);
    }
    ctx.stroke();
  });
}

function drawBox(bbox) {
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  if (!bbox) return;
  ctx.strokeStyle = "rgba(122, 181, 255, 0.8)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  if (ctx.roundRect) {
    ctx.roundRect(bbox.x, bbox.y, bbox.w, bbox.h, 12);
  } else {
    ctx.rect(bbox.x, bbox.y, bbox.w, bbox.h);
  }
  ctx.stroke();
}

function positionCard(bbox) {
  if (!bbox) {
    card.style.left = "16px";
    card.style.top = "16px";
    return;
  }

  const videoRect = video.getBoundingClientRect();
  const scaleX = videoRect.width / overlay.width;
  const scaleY = videoRect.height / overlay.height;

  const rawX = (bbox.x + bbox.w + 16) * scaleX;
  const rawY = bbox.y * scaleY;

  const maxX = Math.max(videoRect.width - card.offsetWidth - 12, 12);
  const maxY = Math.max(videoRect.height - card.offsetHeight - 12, 12);

  const cardX = Math.min(Math.max(rawX, 12), maxX);
  const cardY = Math.min(Math.max(rawY, 12), maxY);

  card.style.left = `${cardX}px`;
  card.style.top = `${Math.max(cardY, 12)}px`;
}

// Registration Modal Functions
function showRegistrationModal(canvas, score) {
  unknownPersonCanvas = canvas;
  unknownPersonScore = score;
  personNameInput.value = "";
  personRelationInput.value = "";
  personNameInput.focus();
  registrationModal.classList.remove("hidden");
}

function hideRegistrationModal() {
  registrationModal.classList.add("hidden");
  unknownPersonCanvas = null;
  unknownPersonScore = null;
}

async function submitRegistration() {
  const name = personNameInput.value.trim();
  const relationship = personRelationInput.value.trim();

  if (!name) {
    alert("Please enter a name");
    return;
  }

  if (!unknownPersonCanvas) {
    alert("Error: No face image available");
    return;
  }

  registerConfirmBtn.disabled = true;
  registerConfirmBtn.textContent = "Saving...";

  try {
    const imageData = unknownPersonCanvas.toDataURL("image/jpeg", 0.75);

    const res = await fetch("/api/register_unknown_person", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image: imageData,
        name: name,
        relationship: relationship,
      }),
    });

    const result = await res.json();

    if (result.status === "success") {
      setStatus(`✓ Successfully registered ${name}!`);
      hideRegistrationModal();
      lastUnknownPersonTime = Date.now(); // Reset cooldown
      alert(`${name} has been added to your memory records!`);
    } else {
      alert("Error: " + (result.message || "Failed to register person"));
    }
  } catch (err) {
    console.error("Registration error:", err);
    alert("Error saving person: " + err.message);
  } finally {
    registerConfirmBtn.disabled = false;
    registerConfirmBtn.textContent = "Save & Add to Records";
  }
}

async function captureFrame() {
  if (video.readyState < 2) return;

  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 1280;
  canvas.height = video.videoHeight || 720;
  const context = canvas.getContext("2d");
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  const dataUrl = canvas.toDataURL("image/jpeg", 0.65);

  try {
    // Use multi-face detection endpoint
    const res = await fetch("/api/identify_all_faces", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataUrl }),
    });
    const payload = await res.json();
    handleMultiFaceDetection(payload, canvas);
  } catch (err) {
    console.error("identify error", err);
    setStatus("Connection error");
  }
}

function startDetectLoop() {
  if (detectTimer) return;
  detectTimer = setInterval(captureFrame, DETECT_INTERVAL_MS);
}

function handleMultiFaceDetection(payload, canvasFrame) {
  if (!payload) {
    hideCard();
    setStatus("No response from server");
    return;
  }

  if (payload.status === "error") {
    hideCard();
    setStatus("Error: " + (payload.message || "Unknown error"));
    console.error("API error:", payload);
    return;
  }

  if (payload.status === "no_face") {
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    hideCard();
    setStatus("No face detected");
    return;
  }

  const people = payload.people || [];
  
  // Draw boxes around all detected faces
  const bboxes = people.map(p => p.bbox).filter(b => b);
  drawBoxes(bboxes);

  // Get recognized people
  const recognizedPeople = people.filter(p => p.status === "ok" && p.person);
  
  // Check for unknown people with low similarity
  const unknownPeople = people.filter(p => p.status === "unknown");
  if (unknownPeople.length > 0 && registrationModal.classList.contains("hidden")) {
    const unknownPerson = unknownPeople[0]; // Take first unknown
    const score = unknownPerson.score || 0;
    
    // Show registration prompt if similarity is low and cooldown has passed
    if (score < UNKNOWN_PERSON_THRESHOLD && Date.now() - lastUnknownPersonTime > UNKNOWN_PERSON_COOLDOWN_MS) {
      if (canvasFrame) {
        setStatus(`New face detected (${(score * 100).toFixed(1)}%) - Open to register?`);
        showRegistrationModal(canvasFrame, score);
      }
    }
  }
  
  if (recognizedPeople.length === 0) {
    if (unknownPeople.length === 0) {
      hideCard();
      setStatus("No faces detected");
    }
    return;
  }

  // Display first recognized person's card
  const firstPerson = recognizedPeople[0];
  currentPersonId = firstPerson.person.id;
  
  // Track all recognized people for multi-speaker recording
  window.recognizedPeople = recognizedPeople.map(p => p.person.id);
  
  if (recognizedPeople.length > 1) {
    // For multi-speaker, show group conversation indicator
    showGroupConversationCard(recognizedPeople);
    setStatus(`Group conversation: ${recognizedPeople.map(p => p.person.name).join(", ")}`);
    maybeStartMultiSpeakerRecording(window.recognizedPeople);
  } else {
    showCard(firstPerson.person, firstPerson.bbox);
    maybeStartRecording(currentPersonId);
  }
}

function showGroupConversationCard(recognizedPeople) {
  const names = recognizedPeople.map(p => p.person.name).join(" & ");
  cardName.textContent = names;
  cardRelationship.textContent = "Group Conversation";
  cardSummary.textContent = "Recording group conversation...";

  // Position card at center-right
  card.style.left = "auto";
  card.style.right = "16px";
  card.style.top = "120px";
  card.classList.remove("hidden");
}

function showCard(person, bbox) {
  cardName.textContent = person.name || "Known Person";
  cardRelationship.textContent = person.relationship || "Visitor";
  cardSummary.textContent =
    person.last_summary ||
    "We will capture a short memory after this conversation.";

  positionCard(bbox);
  card.classList.remove("hidden");
  setStatus("Recognized: " + person.name);
}

function hideCard() {
  currentPersonId = null;
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  card.classList.add("hidden");
  setStatus("Searching…");
}

async function maybeStartRecording(personId) {
  // Don't start recording if mic is muted
  if (isMicMuted) {
    console.log(`[Recording] Mic is muted, skipping recording for ${personId}`);
    return;
  }
  
  if (audioRecorder || recordingPersonId === personId) {
    console.log(`[Recording] Already recording or same person (${personId})`);
    return;
  }

  console.log(`[Recording] Starting recording for ${personId}...`);
  try {
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("[Recording] Got audio stream");
    
    // Try to use webm, fallback to default
    let mimeType = "audio/webm";
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = ""; // Use browser default
      console.log("[Recording] WebM not supported, using default");
    }
    
    audioRecorder = new MediaRecorder(audioStream, { mimeType: mimeType });
    audioChunks = [];
    recordingPersonId = personId;

    audioRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunks.push(e.data);
        console.log(`[Recording] Chunk received: ${e.data.size} bytes (total: ${audioChunks.length} chunks)`);
      }
    };
    
    audioRecorder.onstop = async () => {
      console.log(`[Recording] Stopped. Total chunks: ${audioChunks.length}`);
      recordingIndicator.classList.add("hidden");
      const blob = new Blob(audioChunks, { type: mimeType || "audio/webm" });
      console.log(`[Recording] Blob size: ${blob.size} bytes`);
      audioStream.getTracks().forEach((t) => t.stop());
      await sendAudio(personId, blob);
      audioRecorder = null;
      audioChunks = [];
      audioStream = null;
      recordingPersonId = null;
    };

    audioRecorder.onerror = (e) => {
      console.error("[Recording] Error:", e);
      setStatus("Recording error");
    };

    audioRecorder.start();
    console.log(`[Recording] Recording started (will stop in ${RECORD_WINDOW_MS}ms)`);
    setStatus("Recording conversation…");
    recordingIndicator.classList.remove("hidden");
    recordingTimeout = setTimeout(() => {
      console.log("[Recording] Timeout reached, stopping...");
      if (audioRecorder && audioRecorder.state !== "inactive") {
        audioRecorder.stop();
      }
    }, RECORD_WINDOW_MS);
  } catch (err) {
    console.error("[Recording] Failed to start:", err);
    setStatus("Microphone permission needed");
    recordingIndicator.classList.add("hidden");
  }
}

async function maybeStartMultiSpeakerRecording(personIds) {
  // Don't start recording if mic is muted
  if (isMicMuted) {
    console.log(`[Recording] Mic is muted, skipping multi-speaker recording`);
    return;
  }
  
  if (audioRecorder) {
    console.log(`[Recording] Already recording, skipping new multi-speaker session`);
    return;
  }

  console.log(`[Recording] Starting multi-speaker recording for: ${personIds.join(", ")}...`);
  try {
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("[Recording] Got audio stream for multi-speaker");
    
    let mimeType = "audio/webm";
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = "";
      console.log("[Recording] WebM not supported, using default");
    }
    
    audioRecorder = new MediaRecorder(audioStream, { mimeType: mimeType });
    audioChunks = [];
    recordingPersonId = personIds.join(","); // Mark as multi-speaker
    window.currentPersonIds = personIds;

    audioRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunks.push(e.data);
        console.log(`[Recording] Chunk received: ${e.data.size} bytes`);
      }
    };
    
    audioRecorder.onstop = async () => {
      console.log(`[Recording] Stopped multi-speaker recording. Total chunks: ${audioChunks.length}`);
      recordingIndicator.classList.add("hidden");
      const blob = new Blob(audioChunks, { type: mimeType || "audio/webm" });
      console.log(`[Recording] Blob size: ${blob.size} bytes`);
      audioStream.getTracks().forEach((t) => t.stop());
      await sendMultiSpeakerAudio(personIds, blob);
      audioRecorder = null;
      audioChunks = [];
      audioStream = null;
      recordingPersonId = null;
    };

    audioRecorder.onerror = (e) => {
      console.error("[Recording] Error:", e);
      setStatus("Recording error");
    };

    audioRecorder.start();
    console.log(`[Recording] Multi-speaker recording started (will stop in ${RECORD_WINDOW_MS}ms)`);
    setStatus("Recording multi-speaker conversation…");
    recordingIndicator.classList.remove("hidden");
    recordingTimeout = setTimeout(() => {
      console.log("[Recording] Timeout reached, stopping multi-speaker...");
      if (audioRecorder && audioRecorder.state !== "inactive") {
        audioRecorder.stop();
      }
    }, RECORD_WINDOW_MS);
  } catch (err) {
    console.error("[Recording] Failed to start multi-speaker:", err);
    setStatus("Microphone permission needed");
    recordingIndicator.classList.add("hidden");
  }
}

async function sendAudio(personId, blob) {
  console.log(`[Audio] Sending audio for ${personId}, size: ${blob.size} bytes`);
  setStatus("Summarizing…");
  const form = new FormData();
  form.append("audio", blob, "conversation.webm");

  try {
    const res = await fetch(`/api/upload_audio/${personId}`, {
      method: "POST",
      body: form,
    });
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error(`[Audio] Server error: ${res.status} - ${errorText}`);
      setStatus("Summary failed: " + res.status);
      return;
    }
    
    const payload = await res.json();
    console.log("[Audio] Response:", payload);
    
    if (payload.status === "ok") {
      const summary = payload.summary || payload.person?.last_summary || "Memory updated.";
      cardSummary.textContent = summary;
      setStatus("Updated memory for " + (payload.person?.name || personId));
      console.log("[Audio] Summary updated:", summary);
    } else {
      console.error("[Audio] Error in response:", payload);
      setStatus("Summary failed: " + (payload.message || "Unknown error"));
    }
  } catch (err) {
    console.error("[Audio] Network error:", err);
    setStatus("Summary failed: Network error");
  } finally {
    if (recordingTimeout) {
      clearTimeout(recordingTimeout);
      recordingTimeout = null;
    }
  }
}

async function sendMultiSpeakerAudio(personIds, blob) {
  console.log(`[Audio] Sending multi-speaker audio for: ${personIds.join(", ")}, size: ${blob.size} bytes`);
  setStatus("Processing multi-speaker conversation…");

  // Convert blob to base64
  const reader = new FileReader();
  reader.onload = async () => {
    const base64audio = reader.result.split(",")[1];
    
    try {
      const response = await fetch("/api/upload_audio_multi", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          audio: reader.result,
          person_ids: personIds
        })
      });
      
      if (!response.ok) {
        console.error(`[Audio] Error: ${response.status}`);
        setStatus("Multi-speaker processing failed");
        return;
      }
      
      const payload = await response.json();
      console.log("[Audio] Multi-speaker response:", payload);
      
      if (payload.status === "ok") {
        // Update memory for all people involved
        const peopleNames = Object.values(payload.people)
          .map(p => p.name)
          .join(" & ");
        
        // Show group conversation summary in card
        cardName.textContent = peopleNames;
        cardRelationship.textContent = "Group Conversation";
        cardSummary.textContent = payload.people[Object.keys(payload.people)[0]].last_summary || "Memory updated";
        
        setStatus(`✓ Conversation saved for: ${peopleNames}`);
        console.log("[Audio] Multi-speaker memories updated");
      } else {
        console.error("[Audio] Error in response:", payload);
        setStatus("Multi-speaker processing failed: " + (payload.message || "Unknown error"));
      }
    } catch (err) {
      console.error("[Audio] Network error:", err);
      setStatus("Multi-speaker processing failed: Network error");
    } finally {
      if (recordingTimeout) {
        clearTimeout(recordingTimeout);
        recordingTimeout = null;
      }
    }
  };
  reader.readAsDataURL(blob);
}

// Registration Modal Event Listeners
registerConfirmBtn.addEventListener("click", submitRegistration);
registerCancelBtn.addEventListener("click", hideRegistrationModal);

// Allow pressing Enter to submit registration form
personNameInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    submitRegistration();
  }
});

personRelationInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    submitRegistration();
  }
});

// Close modal when clicking overlay
registrationModal.addEventListener("click", (e) => {
  if (e.target === registrationModal.querySelector(".modal-overlay")) {
    hideRegistrationModal();
  }
});

