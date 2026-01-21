import base64
import io
import json
import os
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from PIL import Image

from face_module import FaceMemoryRecognizer
from audio_pipeline import ConversationAudioProcessor
from memory_store import MemoryStore


app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

MEMORY_PATH = os.path.join(DATA_DIR, "memories.json")
KNOWN_FACES_DIR = os.path.join(DATA_DIR, "known_faces")
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

memory_store = MemoryStore(MEMORY_PATH)
face_recognizer = FaceMemoryRecognizer(KNOWN_FACES_DIR, memory_store)
audio_processor = ConversationAudioProcessor(memory_store)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/identify_face", methods=["POST"])
def identify_face():
    """
    Accepts a JSON payload:
    {
      "image": "data:image/jpeg;base64,..."
    }
    Returns:
    {
      "status": "ok" | "no_face" | "unknown",
      "person": {
         "id": "jake",
         "name": "Jake",
         "relationship": "Son",
         "last_summary": "...",
         "visit_count": 4,
         "last_visit": "2026-01-12"
      }
    }
    """
    payload = request.get_json(silent=True)
    if not payload or "image" not in payload:
        return jsonify({"status": "error", "message": "Missing image"}), 400

    image_data = payload["image"]
    try:
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        decoded = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(decoded)).convert("RGB")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid image: {e}"}), 400

    match = face_recognizer.identify_pil_image(img)

    if match is None:
        print("[API] No face detected in image")
        return jsonify({"status": "no_face"})

    if match["label"] is None:
        print(f"[API] Face detected but not recognized (score: {match.get('score', 0):.3f})")
        return jsonify({"status": "unknown", "bbox": match.get("bbox"), "score": match.get("score", 0)})
    
    print(f"[API] Recognized: {match['label']} (score: {match.get('score', 0):.3f})")

    person_id = match["label"]
    person_memory = memory_store.get_person(person_id)

    return jsonify(
        {
            "status": "ok",
            "bbox": match.get("bbox"),
            "person": {
                "id": person_id,
                "name": person_memory["name"],
                "relationship": person_memory.get("relationship", ""),
                "last_summary": person_memory.get("last_summary", ""),
                "visit_count": person_memory.get("visit_count", 0),
                "last_visit": person_memory.get("last_visit"),
            },
        }
    )


@app.route("/api/identify_all_faces", methods=["POST"])
def identify_all_faces():
    """
    Detects and identifies all faces in an image.
    Returns list of all detected people with their bboxes.
    """
    payload = request.get_json(silent=True)
    if not payload or "image" not in payload:
        return jsonify({"status": "error", "message": "Missing image"}), 400

    image_data = payload["image"]
    try:
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        decoded = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(decoded)).convert("RGB")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid image: {e}"}), 400

    matches = face_recognizer.identify_all_faces_in_image(img)

    if not matches:
        print("[API] No faces detected in image")
        return jsonify({"status": "no_face", "people": []})

    people = []
    for match in matches:
        if match["label"] is None:
            # Unknown face
            people.append({
                "status": "unknown",
                "bbox": match.get("bbox"),
                "score": match.get("score", 0)
            })
        else:
            person_id = match["label"]
            person_memory = memory_store.get_person(person_id)
            people.append({
                "status": "ok",
                "bbox": match.get("bbox"),
                "person": {
                    "id": person_id,
                    "name": person_memory["name"],
                    "relationship": person_memory.get("relationship", ""),
                    "last_summary": person_memory.get("last_summary", ""),
                    "visit_count": person_memory.get("visit_count", 0),
                    "last_visit": person_memory.get("last_visit"),
                },
                "score": match.get("score", 0)
            })

    print(f"[API] Detected {len(people)} face(s)")
    return jsonify({"status": "ok", "people": people})


@app.route("/api/upload_audio/<person_id>", methods=["POST"])
def upload_audio(person_id):
    """
    Accepts multipart/form-data with a single file field 'audio'.
    Uses Whisper + simple summarization to update the person's memory.
    Returns updated memory snapshot.
    """
    if "audio" not in request.files:
        return jsonify({"status": "error", "message": "Missing audio file"}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    # Persist audio temporarily
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    conv_dir = os.path.join(DATA_DIR, "conversations")
    os.makedirs(conv_dir, exist_ok=True)
    temp_path = os.path.join(conv_dir, f"{person_id}_{ts}.webm")
    audio_file.save(temp_path)
    
    file_size = os.path.getsize(temp_path)
    print(f"[API] Received audio file: {temp_path} ({file_size} bytes)")

    try:
        transcript, summary = audio_processor.process_conversation(person_id, temp_path)
        print(f"[API] Processing complete. Transcript length: {len(transcript)}, Summary length: {len(summary)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return (
            jsonify({"status": "error", "message": f"Audio processing failed: {e}"}),
            500,
        )
    finally:
        # Clean up temp audio file; no background recording
        if os.path.exists(temp_path):
            os.remove(temp_path)

    updated = memory_store.update_after_visit(person_id, summary)

    return jsonify(
        {
            "status": "ok",
            "transcript": transcript,
            "summary": summary,
            "person": updated,
        }
    )


@app.route("/api/upload_audio_multi", methods=["POST"])
def upload_audio_multi():
    """
    Handles multi-speaker conversation audio.
    Expects JSON with:
    {
      "audio": base64_audio,
      "person_ids": ["person1", "person2"]
    }
    Processes conversation and updates all people's memories.
    """
    payload = request.get_json(silent=True)
    if not payload or "audio" not in payload or "person_ids" not in payload:
        return jsonify({"status": "error", "message": "Missing audio or person_ids"}), 400

    person_ids = payload.get("person_ids", [])
    if not person_ids or not isinstance(person_ids, list):
        return jsonify({"status": "error", "message": "Invalid person_ids"}), 400

    # Decode audio
    audio_data = payload["audio"]
    try:
        if "," in audio_data:
            audio_data = audio_data.split(",", 1)[1]
        decoded = base64.b64decode(audio_data)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        conv_dir = os.path.join(DATA_DIR, "conversations")
        os.makedirs(conv_dir, exist_ok=True)
        audio_path = os.path.join(conv_dir, f"multi_{ts}.webm")
        with open(audio_path, "wb") as f:
            f.write(decoded)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid audio: {e}"}), 400

    try:
        results = audio_processor.process_multi_speaker_conversation(person_ids, audio_path)
        
        # Update memory for each person
        updated_people = {}
        for person_id, (transcript, summary) in results.items():
            memory_store.update_after_visit(person_id, transcript, summary)
            updated_people[person_id] = memory_store.get_person(person_id)
        
        return jsonify({
            "status": "ok",
            "people": updated_people,
            "transcript": list(results.values())[0][0] if results else ""
        })
    except Exception as e:
        print(f"[API] Error processing multi-speaker audio: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass


@app.route("/api/memories", methods=["GET"])
def list_memories():
    """Small helper endpoint for debugging/demo."""
    return jsonify({"status": "ok", "people": memory_store.list_people()})

@app.route("/api/debug/faces", methods=["GET"])
def debug_faces():
    """Debug endpoint to check loaded face embeddings."""
    loaded_ids = list(face_recognizer.embeddings.keys())
    return jsonify({
        "status": "ok",
        "loaded_faces": loaded_ids,
        "count": len(loaded_ids),
        "threshold": face_recognizer.threshold
    })


@app.route("/api/register_unknown_person", methods=["POST"])
def register_unknown_person():
    """
    Register a new unknown person detected in camera.
    Expects:
    {
      "image": "data:image/jpeg;base64,...",
      "name": "John",
      "relationship": "Friend"
    }
    Returns:
    {
      "status": "success" | "error",
      "person_id": "john_123...",
      "message": "..."
    }
    """
    payload = request.get_json(silent=True)
    if not payload or "image" not in payload or "name" not in payload:
        return jsonify({"status": "error", "message": "Missing image, name, or relationship"}), 400

    image_data = payload["image"]
    name = payload.get("name", "").strip()
    relationship = payload.get("relationship", "").strip()

    if not name:
        return jsonify({"status": "error", "message": "Name cannot be empty"}), 400

    try:
        # Decode image
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        decoded = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(decoded)).convert("RGB")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid image: {e}"}), 400

    # Create unique person_id
    import uuid
    person_id = f"{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"

    # Save new person
    success = face_recognizer.save_new_person(person_id, name, relationship, img)

    if not success:
        return jsonify({"status": "error", "message": "Failed to save person"}), 500

    return jsonify({
        "status": "success",
        "person_id": person_id,
        "message": f"Successfully registered {name}!"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
