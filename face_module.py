import json
import os
from datetime import datetime
from typing import Dict, Optional

import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1
from PIL import Image


class FaceMemoryRecognizer:
    """
    Thin wrapper around DeepFace for demo-ready, local face recognition
    for a very small, pre-registered set of people.
    """

    def __init__(self, known_faces_dir: str, memory_store):
        self.known_faces_dir = known_faces_dir
        self.memory_store = memory_store
        self.threshold = 0.5  # cosine similarity threshold for "same person" (lowered for demo)
        self.embeddings: Dict[str, np.ndarray] = {}
        self.cascade = cv2.CascadeClassifier(
            os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        )
        self.device = torch.device("cpu")
        print(f"[FaceMemoryRecognizer] Loading FaceNet model...")
        self.model = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)
        print(f"[FaceMemoryRecognizer] Model loaded. Loading known faces from {known_faces_dir}...")
        self._load_known_faces()

    def _load_known_faces(self):
        """
        Expects structure:
        data/known_faces/
          jake.jpg
          jake.json   # {"id": "jake", "name": "Jake", "relationship": "Son", ...}
        """
        if not os.path.isdir(self.known_faces_dir):
            return

        for fname in os.listdir(self.known_faces_dir):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            stem, _ = os.path.splitext(fname)
            img_path = os.path.join(self.known_faces_dir, fname)
            meta_path = os.path.join(self.known_faces_dir, f"{stem}.json")

            person_id = stem
            meta = {"id": stem, "name": stem, "relationship": ""}
            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    person_id = meta.get("id", stem)
                except Exception:
                    pass

            # Ensure memory store has an entry
            self.memory_store.ensure_person(
                person_id,
                name=meta.get("name", stem),
                relationship=meta.get("relationship", ""),
            )

            try:
                img_bgr = cv2.imread(img_path)
                if img_bgr is None:
                    print(f"[FaceMemoryRecognizer] Failed to read image: {img_path}")
                    continue
                vec = self._embed_from_bgr(img_bgr)
                if vec is not None:
                    self.embeddings[person_id] = vec
                    print(f"[FaceMemoryRecognizer] Loaded {person_id} ({meta.get('name', person_id)})")
                else:
                    print(f"[FaceMemoryRecognizer] No face detected in {img_path}")
            except Exception as e:
                print(f"[FaceMemoryRecognizer] Failed to embed {img_path}: {e}")
                import traceback
                traceback.print_exc()

        print(f"[FaceMemoryRecognizer] Loaded embeddings for {len(self.embeddings)} people")

    def _detect_face(self, bgr: np.ndarray) -> Optional[Dict[str, int]]:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        faces = self.cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
        if len(faces) == 0:
            return None
        # pick largest face
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        x, y, w, h = faces[0]
        return {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}

    def _detect_all_faces(self, bgr: np.ndarray) -> list:
        """Detect all faces in the image, return list of bboxes with validation"""
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        faces = self.cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
        if len(faces) == 0:
            return []
        
        # Filter out false positives: validate face size and aspect ratio
        img_height, img_width = bgr.shape[:2]
        valid_faces = []
        
        for x, y, w, h in faces:
            # Face should not be too large (>80% of image) or too small (<5% of image)
            face_area_ratio = (w * h) / (img_width * img_height)
            if face_area_ratio < 0.05 or face_area_ratio > 0.8:
                continue
            
            # Face should have reasonable aspect ratio (roughly square, not extremely stretched)
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio < 0.7 or aspect_ratio > 1.3:
                continue
            
            valid_faces.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
        
        return valid_faces

    def _preprocess_face(self, face_bgr: np.ndarray) -> torch.Tensor:
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        face_resized = cv2.resize(face_rgb, (160, 160))
        arr = face_resized.astype("float32")
        arr = (arr - 127.5) / 128.0  # standard Facenet normalization
        tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
        return tensor.to(self.device)

    def _embed_from_bgr(self, bgr: np.ndarray) -> Optional[np.ndarray]:
        if bgr is None or bgr.size == 0:
            return None
        bbox = self._detect_face(bgr)
        if bbox:
            x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]
            face_roi = bgr[y : y + h, x : x + w]
        else:
            face_roi = bgr

        try:
            tensor = self._preprocess_face(face_roi)
            with torch.no_grad():
                emb = self.model(tensor).cpu().numpy()[0]
            return emb
        except Exception as e:
            print(f"[FaceMemoryRecognizer] Embedding failed: {e}")
            return None

    def _embed_pil(self, img: Image.Image) -> Optional[Dict]:
        # Convert PIL to OpenCV-style BGR
        rgb = np.array(img)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        bbox = self._detect_face(bgr)
        embedding = self._embed_from_bgr(bgr)
        if embedding is None:
            return None
        return {"embedding": embedding, "bbox": bbox}

    def identify_pil_image(self, img: Image.Image) -> Optional[Dict]:
        """
        Returns:
          None -> no face / no embedding
          {"label": None} -> face but not recognized
          {"label": "jake", "score": 0.83} -> recognized
        """
        if not self.embeddings:
            print(f"[FaceMemoryRecognizer] No embeddings loaded! Check known_faces directory.")
            return None

        embed_result = self._embed_pil(img)
        if embed_result is None:
            return None

        target_vec = embed_result["embedding"]
        bbox = embed_result["bbox"]

        best_label = None
        best_score = -1.0
        for person_id, vec in self.embeddings.items():
            # cosine similarity
            denom = (np.linalg.norm(vec) * np.linalg.norm(target_vec)) + 1e-8
            sim = float(np.dot(vec, target_vec) / denom)
            if sim > best_score:
                best_score = sim
                best_label = person_id

        print(f"[FaceMemoryRecognizer] Best match: {best_label} (score: {best_score:.3f}, threshold: {self.threshold})")
        
        if best_score < self.threshold:
            # Treat as unknown / stranger
            return {"label": None, "score": best_score, "bbox": bbox}

        return {"label": best_label, "score": best_score, "bbox": bbox}

    def identify_all_faces_in_image(self, img: Image.Image) -> list:
        """
        Detect and identify all faces in the image.
        Returns list of {"label": person_id or None, "score": similarity, "bbox": bbox}
        Only includes valid faces that pass quality checks.
        """
        if not self.embeddings:
            return []

        rgb = np.array(img)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        # Detect all faces with validation
        bboxes = self._detect_all_faces(bgr)
        if not bboxes:
            return []

        results = []
        for bbox in bboxes:
            x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]
            face_roi = bgr[y : y + h, x : x + w]

            # Validate face ROI
            if face_roi.size == 0 or face_roi.shape[0] < 20 or face_roi.shape[1] < 20:
                print(f"[FaceMemoryRecognizer] Invalid face ROI size: {face_roi.shape}")
                continue

            try:
                tensor = self._preprocess_face(face_roi)
                with torch.no_grad():
                    target_vec = self.model(tensor).cpu().numpy()[0]
                
                # Validate embedding: check if it's reasonable (not all zeros or NaN)
                if np.isnan(target_vec).any() or np.allclose(target_vec, 0):
                    print(f"[FaceMemoryRecognizer] Invalid embedding detected")
                    continue
                    
            except Exception as e:
                print(f"[FaceMemoryRecognizer] Failed to embed face: {e}")
                continue

            best_label = None
            best_score = -1.0
            for person_id, vec in self.embeddings.items():
                denom = (np.linalg.norm(vec) * np.linalg.norm(target_vec)) + 1e-8
                sim = float(np.dot(vec, target_vec) / denom)
                if sim > best_score:
                    best_score = sim
                    best_label = person_id

            if best_score >= self.threshold:
                results.append({"label": best_label, "score": best_score, "bbox": bbox})
            else:
                # Only add as unknown if we have a valid embedding
                results.append({"label": None, "score": best_score, "bbox": bbox})

        return results

    def save_new_person(self, person_id: str, name: str, relationship: str, image_pil: Image.Image) -> bool:
        """
        Save a new person to the known faces database.
        - Generates embedding from image
        - Saves image as PNG
        - Creates metadata JSON
        - Updates memory store
        Returns True on success, False otherwise
        """
        try:
            # Generate embedding
            embedding = self._embed_pil(image_pil)
            if embedding is None:
                print(f"[FaceMemoryRecognizer] Failed to generate embedding for {person_id}")
                return False

            # Save image as PNG
            img_path = os.path.join(self.known_faces_dir, f"{person_id}.png")
            image_pil.save(img_path)
            print(f"[FaceMemoryRecognizer] Saved face image: {img_path}")

            # Create metadata JSON
            meta = {
                "id": person_id,
                "name": name,
                "relationship": relationship,
                "created_date": datetime.utcnow().isoformat()
            }
            meta_path = os.path.join(self.known_faces_dir, f"{person_id}.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            print(f"[FaceMemoryRecognizer] Saved metadata: {meta_path}")

            # Update in-memory embeddings
            self.embeddings[person_id] = embedding["embedding"]

            # Update memory store
            self.memory_store.ensure_person(person_id, name, relationship)

            print(f"[FaceMemoryRecognizer] Successfully registered new person: {person_id} ({name})")
            return True

        except Exception as e:
            print(f"[FaceMemoryRecognizer] Failed to save new person: {e}")
            import traceback
            traceback.print_exc()
            return False

