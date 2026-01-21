"""Quick test to verify face images are loading correctly."""
import cv2
import os
from face_module import FaceMemoryRecognizer
from memory_store import MemoryStore

DATA_DIR = "data"
KNOWN_FACES_DIR = os.path.join(DATA_DIR, "known_faces")
MEMORY_PATH = os.path.join(DATA_DIR, "memories.json")

print("Testing face recognition setup...")
print(f"Known faces directory: {KNOWN_FACES_DIR}")
print(f"Files in directory:")
for f in os.listdir(KNOWN_FACES_DIR):
    print(f"  - {f}")

memory_store = MemoryStore(MEMORY_PATH)
recognizer = FaceMemoryRecognizer(KNOWN_FACES_DIR, memory_store)

print(f"\nLoaded {len(recognizer.embeddings)} face embeddings:")
for person_id in recognizer.embeddings.keys():
    print(f"  - {person_id}")

if len(recognizer.embeddings) == 0:
    print("\n⚠️  No faces loaded! Check:")
    print("  1. Images are .jpg, .jpeg, or .png")
    print("  2. Images contain clear frontal faces")
    print("  3. Images are readable by OpenCV")
else:
    print("\nFace recognition ready!")
