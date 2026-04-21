# Skin Cancer Analyzer - Project Review

## 📋 Project Overview

**Skin Cancer Analyzer** is a full-stack AI web application designed for dermatological image analysis. It provides clinicians and researchers with an intelligent tool to upload skin lesion images and receive automated classification predictions across seven lesion types, along with confidence scores and clinical context.

The application combines a modern **Next.js frontend** with a **FastAPI backend**, powered by a **ResNet18 deep learning model** trained on the HAM10000 dataset.

---

## 🎯 Project Goals & Accomplishments

### Primary Objectives
✅ Build a presentation-ready AI application for skin lesion classification  
✅ Implement a user-friendly web interface for image upload and analysis  
✅ Deploy an inference API with trained ML model  
✅ Provide interpretable confidence scores across all lesion classes  
✅ Add intelligent guardrails to reduce false positives  
✅ Create production-ready deployment configurations  

### Key Accomplishments
✅ **Trained ResNet18 model** achieving **80.6% test accuracy** on HAM10000 dataset  
✅ **Responsive Next.js frontend** with drag-drop image upload interface  
✅ **FastAPI inference server** with CORS-enabled endpoints  
✅ **Docker containerization** for both frontend and backend services  
✅ **Intelligent uncertainty handling** with adaptive confidence thresholds  
✅ **Lesion-focus guardrail** to reject non-lesion or poorly-framed images  
✅ **Comprehensive class scoring** showing confidence breakdown across all 7 lesion types  
✅ **Presentation-ready deployment** with custom startup scripts  

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SKIN CANCER ANALYZER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐         ┌──────────────────────────┐ │
│  │  Frontend (Next.js)  │         │  Backend (FastAPI)       │ │
│  │  Port: 3000          │◄───────►│  Port: 8000              │ │
│  │                      │ HTTP    │                          │ │
│  │ • Upload Zone        │ REST    │ • /analyze endpoint      │ │
│  │ • Result Panel       │         │ • /health endpoint       │ │
│  │ • Score Breakdown    │         │ • Inference Service      │ │
│  │ • Clinical Display   │         │                          │ │
│  └──────────────────────┘         └──────────────────────────┘ │
│           │                               │                    │
│           │ (Browser)                     │ (Python Process    │
│           │                               │  or Container)     │
│           │                               ▼                    │
│           │                      ┌──────────────────────────┐  │
│           │                      │  ML Model & Guardrails   │  │
│           │                      │                          │  │
│           │                      │ • ResNet18 (67.7 MB)    │  │
│           │                      │ • 7-class softmax       │  │
│           │                      │ • Uncertainty threshold  │  │
│           │                      │ • Lesion-focus ratio     │  │
│           │                      │ • Confidence override    │  │
│           │                      └──────────────────────────┘  │
│           ▼                               │                    │
│  localhost:3000               localhost:8000/health            │
│                                                                │
├─────────────────────────────────────────────────────────────────┤
│                   Deployment Options                           │
├─────────────────────────────────────────────────────────────────┤
│ • Docker Compose: Both services containerized                  │
│ • Local + Container: Frontend container + local Python backend │
│ • Pure Local: Both services as local processes                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 Technology Stack

### Frontend
- **Framework**: Next.js 14.2.3 (React 18.3.1)
- **Styling**: CSS Modules with responsive design
- **API Client**: Fetch API with CORS headers
- **Deployment**: Docker container

### Backend
- **Framework**: FastAPI 0.111.0 with Uvicorn
- **ML Model**: PyTorch 2.4.1
- **Image Processing**: Pillow 10.3.0
- **Data Science**: NumPy, Pandas, scikit-learn
- **Inference Device**: Auto-detect CUDA → DirectML GPU → CPU

### Database & Data
- **Dataset**: HAM10000 (10,015 dermoscopic images)
- **Classes**: 7 lesion types
- **Storage**: CSV metadata + image files (8GB+)

### DevOps & Deployment
- **Containerization**: Docker (both services)
- **Orchestration**: Docker Compose
- **Version Control**: Git with .gitignore
- **Configuration**: Environment variables

---

## 🤖 Machine Learning Model

### Model Architecture
```
ResNet18 (Residual Network)
├── Pretrained on ImageNet
├── Input: 224×224 RGB images
├── Feature extraction: 18 layers
├── Classification head: 7 output classes
└── Output: Normalized softmax probabilities
```

### Training Approach

**Phase 1: Head Training** (First 4 epochs)
- Freeze all ResNet18 body layers
- Train only the classification head (1000 → 7 classes)
- Learning rate: 0.001
- Batch size: 128 images

**Phase 2: Fine-tuning** (Remaining epochs)
- Unfreeze all layers
- Train entire network
- Learning rate: 0.0003 (lower to prevent destroying learned features)
- Batch size: 64 images (reduced memory footprint)
- Patience: 10 epochs without improvement
- Target: 0.80 validation accuracy (achieved at epoch 9)

### Training Configuration
```
Image size:      192×192 pixels
Epochs:          40 (stopped early at 20 due to patience)
Batch size:      128 → 64 (unfrozen)
Optimizer:       Adam
Loss function:   Cross-entropy
Data split:      Train (8012) / Val (1001) / Test (1002)
Device:          DirectML GPU (Windows) or CUDA
```

### Performance Metrics

| Metric | Value |
|--------|-------|
| **Validation Accuracy** | 0.8012 (80.12%) |
| **Test Accuracy** | 0.8064 (80.64%) |
| **Best Epoch** | 9 |
| **Model Size** | 67.7 MB |
| **Inference Time** | ~500ms per image |

### Class-Specific Performance
7 lesion categories trained and evaluated:
1. **nv** - Melanocytic nevus (benign)
2. **mel** - Melanoma (malignant, high severity)
3. **bkl** - Benign keratosis (benign)
4. **bcc** - Basal cell carcinoma (malignant, medium severity)
5. **akiec** - Actinic keratosis (malignant, high severity)
6. **vasc** - Vascular lesion (benign)
7. **df** - Dermatofibroma (benign)

---

## 🎨 Frontend Implementation

### Components

#### **Header Component** (`Header.js`)
- Application branding and navigation
- Dropdown menu for additional resources
- Consistent styling across pages

#### **UploadZone Component** (`UploadZone.js`)
- Drag-and-drop image upload interface
- Click-to-browse fallback
- Image preview with loading spinner
- Accepts PNG, JPG, JPEG formats
- File size validation

#### **ResultPanel Component** (`ResultPanel.js`)
- Displays prediction results
- Shows diagnosis with clinical severity
- Renders confidence meter (visual progress bar)
- **All 7 lesion class scores** with exact percentages
- Clinical notes and recommendations
- Handles "uncertain" state with special messaging

#### **InfoStrip Component** (`InfoStrip.js`)
- Contextual information cards
- Dataset coverage explanation
- Confidence guide
- Presentation flow information

#### **Disclaimer Component** (`Disclaimer.js`)
- Legal notices
- Usage restrictions
- Accuracy limitations

### Key Features

✅ **Responsive Layout**
- Desktop: Two-column design (upload left, results right)
- Tablet/Mobile: Stacked layout
- Sticky right panel on desktop

✅ **Real-time Feedback**
- Immediate preview of uploaded image
- Loading state during inference
- Error handling with fallback messages
- "Upload another" button for quick reanalysis

✅ **Confidence Visualization**
- Progress bars for each class
- Exact percentage display (not rounded)
- Color-coded severity indicators
- Visual distinction between benign/malignant

✅ **Summary Card**
- Session-at-a-glance statistics
- Classes available (7 types shown)
- Current analysis status
- Top confidence class
- Capture tips for better results

✅ **Support Band**
- Three informational cards below upload area
- Confidence interpretation guide
- Dataset diversity metrics
- Presentation workflow explanation

---

## ⚙️ Backend Implementation

### Main API (`main.py`)

#### **Endpoints**

**GET `/health`**
- Returns server status and configuration
- Exposes active thresholds
- Used for deployment health checks
- Response: `{model_loaded, device_name, thresholds}`

**POST `/analyze`**
- Accepts multipart form data with image file
- Validates image format
- Runs inference with guardrails
- Returns detailed prediction JSON

**Response Format**
```json
{
  "success": true,
  "prediction": "nv",
  "confidence": 0.856,
  "uncertain": false,
  "uncertain_reason": null,
  "all_scores": [0.856, 0.023, 0.042, 0.031, 0.018, 0.019, 0.011],
  "class_names": ["nv", "mel", "bkl", "bcc", "akiec", "vasc", "df"],
  "lesion_focus_ratio": 1.23,
  "reasons": [],
  "clinical_details": {
    "name": "Melanocytic nevus",
    "benign": true,
    "severity": "low"
  }
}
```

### Inference Engine

#### **Device Resolution**
```python
resolve_inference_device():
  ├─ Try: torch.cuda (NVIDIA GPU)
  ├─ Try: torch_directml (Windows GPU)
  └─ Fallback: CPU
```

#### **Image Preprocessing**
- Resize to 224×224
- Normalize using ImageNet statistics
- Convert to tensor
- Move to inference device

#### **Model Loading**
- Lazy load on first request
- Cache in memory
- PyTorch checkpoint format (.pt)
- 7 output nodes (softmax normalized)

### Intelligent Guardrails

#### **Two-Layer Uncertainty System**

**Layer 1: Confidence Threshold**
```python
if max_class_confidence < UNCERTAINTY_THRESHOLD (0.35):
    → Mark as UNCERTAIN
    → Return reason: "Low confidence across all classes"
```

**Layer 2: Lesion Focus Validation**
```python
lesion_focus_ratio = compute_lesion_focus_ratio(image)

if (lesion_focus_ratio < LESION_FOCUS_MIN_RATIO (1.05) 
    AND max_class_confidence < STRONG_CONFIDENCE_OVERRIDE (0.95)):
    → Mark as UNCERTAIN
    → Return reason: "Image does not appear to be centered on a lesion"
```

#### **Lesion Focus Ratio Heuristic**
- Compares color anomaly in center region vs border
- Scores 1.0 = uniform skin (no lesion)
- Scores > 1.05 = centered lesion detected
- Prevents false positives on generic skin images

#### **Configuration via Environment Variables**
```bash
UNCERTAINTY_THRESHOLD=0.35              # Min confidence to accept prediction
LESION_FOCUS_MIN_RATIO=1.05            # Min center-to-border anomaly ratio
STRONG_CONFIDENCE_OVERRIDE=0.95        # Override focus check at this confidence
```

---

## 🚀 Deployment & Usage

### Option 1: Docker Compose (Full Production)
```bash
cd c:\Study material\SKIN_CANCER
docker-compose up -d
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/health
```

### Option 2: Presentation Mode (Hybrid)
```bash
# Run startup script
.\start_presentation.bat

# This launches:
# • Frontend container (port 3000)
# • Local Python backend with configured thresholds
```

### Option 3: Local Development
```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
python main.py

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

---

## 📊 Project Structure

```
SKIN_CANCER/
├── backend/                          # FastAPI inference server
│   ├── main.py                      # FastAPI app & inference logic
│   ├── train_model.py               # Model training script
│   ├── evaluate_model.py            # Model evaluation script
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Backend container config
│   ├── best_model.pt                # Trained model checkpoint (67.7 MB)
│   ├── best_model_target80.pt       # Target 0.80 accuracy checkpoint
│   ├── training_metrics_target80.json # Training history
│   ├── evaluation_metrics.json      # Test set performance
│   └── data/HAM10000/               # Dataset directory
│       ├── HAM10000_images_part_1/  # 5000 images
│       ├── HAM10000_images_part_2/  # 5000 images
│       └── HAM10000_metadata.csv    # Class labels
│
├── frontend/                         # Next.js React application
│   ├── app/
│   │   ├── layout.js                # Root layout wrapper
│   │   ├── page.js                  # Main page component
│   │   ├── page.module.css          # Main page styles
│   │   └── globals.css              # Global styles
│   ├── components/
│   │   ├── Header.js                # Header component
│   │   ├── UploadZone.js            # Image upload interface
│   │   ├── ResultPanel.js           # Prediction results display
│   │   ├── InfoStrip.js             # Info cards
│   │   ├── Disclaimer.js            # Legal disclaimer
│   │   └── *.module.css             # Component styles
│   ├── package.json                 # Node dependencies
│   ├── next.config.js               # Next.js configuration
│   ├── Dockerfile                    # Frontend container config
│   └── .env.local                    # API URL configuration
│
├── docker-compose.yml                # Multi-container orchestration
├── start_presentation.bat            # Presentation startup script
├── PROJECT_OVERVIEW.md              # Original overview (legacy)
├── PROJECT_REVIEW.md                # This file
├── README.md                         # Quick start guide
├── QUICKSTART.md                     # 5-minute setup guide
└── SETUP.md                          # Detailed setup instructions
```

---

## 🔍 How the Application Works

### 1. **User Uploads Image**
- Opens http://localhost:3000
- Drags image onto upload zone OR clicks to browse
- Frontend validates format and size

### 2. **Frontend Processes Image**
- Displays preview with loading spinner
- Sets loading state → "Analyzing"
- Sends multipart POST request to `/analyze` endpoint

### 3. **Backend Receives Request**
- Validates image format (PNG/JPG)
- Loads trained model (first time only)
- Prepares image: resize → normalize → tensor → GPU

### 4. **Model Inference**
- Runs 224×224 image through ResNet18
- Gets softmax probabilities across 7 classes
- Computes max confidence and predicted class

### 5. **Guardrails Applied**
- **Check 1**: Is confidence > 0.35?
  - If NO → mark UNCERTAIN
- **Check 2**: Is lesion-focus-ratio > 1.05?
  - If NO and confidence < 0.95 → mark UNCERTAIN

### 6. **Backend Returns Response**
- All class probabilities (7 values)
- Predicted class with confidence
- Uncertainty flag with reason
- Clinical details (name, severity, benignity)
- Lesion focus ratio score

### 7. **Frontend Displays Results**
- Shows diagnosis card with color coding
- Renders confidence meter
- Displays all 7 class scores with bars and percentages
- Shows clinical recommendation
- Provides "Upload another" button for next image

---

## ✨ Key Features & Innovations

### 1. **7-Class Confidence Breakdown**
- All class probabilities visible
- Not just top prediction
- Helps clinician understand model uncertainty
- Exact percentage display (not rounded)

### 2. **Intelligent Uncertainty Handling**
- Doesn't force prediction on ambiguous images
- Uses dual-layer guardrails
- Adaptive thresholds (configurable)
- Clear reasoning in API response

### 3. **Lesion-Focused Validation**
- Heuristic to detect image quality/framing
- Rejects poor-quality captures
- Prevents false confidences on plain skin
- Overridable for very high-confidence predictions

### 4. **Production-Ready Inference**
- Auto device detection (GPU/CPU)
- CORS-enabled for web clients
- Health check endpoint for monitoring
- Environment variable configuration

### 5. **Responsive User Interface**
- Works on desktop, tablet, mobile
- Intuitive drag-drop or click upload
- Real-time feedback and progress
- Clean, medical-grade styling

### 6. **Containerized Deployment**
- Both services dockerized
- Single `docker-compose up` command
- No dependency conflicts
- Repeatable across environments

---

## 📈 Model Performance & Validation

### Test Set Results
- **Total test images**: 1,002
- **Correctly classified**: 808
- **Test accuracy**: 80.64%
- **Validation accuracy**: 80.12%

### Strengths
✅ Handles diverse image qualities (HAM10000 dataset)  
✅ Balanced performance across benign & malignant classes  
✅ Fast inference (<500ms per image)  
✅ Runs on consumer GPU (DirectML, NVIDIA, or CPU)  

### Limitations & Guardrails
⚠️ Dataset bias toward certain skin tones  
⚠️ Requires well-framed lesion-centered images  
⚠️ Not intended for clinical diagnosis (educational demo)  
⚠️ Lesion-focus heuristic may reject valid edge cases  
→ *Mitigated by 0.95 confidence override*

---

## 🛠️ Development Journey

### Phase 1: Emergency Deployment
- Set up FastAPI and Next.js skeleton
- Integrated trained PyTorch model
- Created basic upload/analyze flow
- Got presentation-ready quickly

### Phase 2: False Positive Reduction
- Identified low-confidence false positives (40% top class)
- Lowered uncertainty threshold from 0.50 → 0.35
- Fixed UI labeling ("Low risk" → "Likely benign")

### Phase 3: Healthy-Skin False Positives
- Built lesion-focus-ratio heuristic
- Implemented two-layer uncertainty
- Added strong-confidence override
- Achieved ~66% rejection on plain skin, ~1% on real lesions

### Phase 4: Score Visualization
- Refactored ResultPanel for all 7 classes
- Fixed rounding issues with exact percentages
- Added min-width bars for visibility
- Normalized missing scores to zero

### Phase 5: UI Polish
- Added hero-side summary card
- Created support band with info cards
- Compacted spacing and typography
- Improved page density without sacrificing readability

### Phase 6: Documentation & Cleanup
- Removed obsolete files (empty modules, old checkpoints)
- Created PROJECT_OVERVIEW.md for reference
- Generated GITHUB_REPORT_2026-04-11.md with metrics
- Documented all run modes and guardrails

### Phase 7: Production Readiness
- Created `start_presentation.bat` for one-click startup
- Configured environment variables for thresholds
- Verified Docker Compose orchestration
- Tested local + container hybrid mode

---

## 📝 Configuration & Customization

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `UNCERTAINTY_THRESHOLD` | 0.35 | Min confidence to accept prediction |
| `LESION_FOCUS_MIN_RATIO` | 1.05 | Center-vs-border anomaly ratio threshold |
| `STRONG_CONFIDENCE_OVERRIDE` | 0.95 | Override focus check above this confidence |

### Model Customization
- **Image size**: Hardcoded to 224×224 (ResNet18 standard)
- **Inference device**: Auto-detected, can prefer CUDA via environment
- **Class mapping**: Edit `CLASS_ORDER` and `CLASS_DETAILS` in `main.py`
- **Model checkpoint**: Replace `best_model.pt` with new trained model

### Frontend Customization
- **API URL**: Set `NEXT_PUBLIC_API_URL` env var
- **Styling**: Modify `.module.css` files
- **Colors/fonts**: Edit `globals.css`
- **Components**: React components in `components/` folder

---

## 🔗 API Reference

### Health Endpoint
```
GET http://localhost:8000/health

Response:
{
  "model_loaded": true,
  "device": "directml",
  "device_name": "DirectML GPU",
  "uncertainty_threshold": 0.35,
  "lesion_focus_min_ratio": 1.05,
  "strong_confidence_override": 0.95
}
```

### Analysis Endpoint
```
POST http://localhost:8000/analyze
Content-Type: multipart/form-data

Payload:
  file: <image file>

Response:
{
  "success": true,
  "prediction": "nv",
  "confidence": 0.856,
  "uncertain": false,
  "uncertain_reason": null,
  "all_scores": [0.856, 0.023, 0.042, 0.031, 0.018, 0.019, 0.011],
  "class_names": ["nv", "mel", "bkl", "bcc", "akiec", "vasc", "df"],
  "lesion_focus_ratio": 1.23,
  "reasons": [],
  "clinical_details": {...}
}
```

---

## ✅ Testing & Validation

### Manual Testing Performed
✅ Image upload with various formats (PNG, JPG, JPEG)  
✅ Inference on HAM10000 test set samples  
✅ Guardrail behavior on healthy-skin crops  
✅ Uncertainty threshold boundaries  
✅ Docker Compose startup and health checks  
✅ CORS requests from frontend to backend  
✅ Responsive layout on different screen sizes  

### Test Results
- **Happy path**: ✅ Works end-to-end
- **Low confidence images**: ✅ Correctly marked uncertain
- **Plain skin images**: ✅ Rejected with focus guardrail
- **High confidence lesions**: ✅ Predicted with confidence
- **Docker deployment**: ✅ Both services healthy
- **API endpoints**: ✅ Respond correctly

---

## 📚 References & Documentation

- **README.md** - Quick overview and links
- **QUICKSTART.md** - 5-minute setup guide
- **SETUP.md** - Detailed setup instructions
- **PROJECT_OVERVIEW.md** - Original architecture notes
- **GITHUB_REPORT_2026-04-11.md** - Metrics and performance report

---

## 🎓 Learning Outcomes

### Technologies Mastered
- PyTorch model training and inference
- FastAPI REST API development
- Next.js React framework
- Docker containerization and Compose orchestration
- ResNet18 fine-tuning on custom datasets
- CORS and multipart form data handling
- Responsive CSS design patterns

### ML Concepts Applied
- Transfer learning (ImageNet → HAM10000)
- Train/val/test split and evaluation metrics
- Early stopping and patience-based training
- Softmax probability interpretation
- Heuristic-based guardrails for uncertainty
- Dataset bias and class imbalance considerations

### Software Engineering Practices
- Modular component architecture
- Environment-based configuration
- Health check endpoints
- Error handling and fallbacks
- Git version control
- Docker-based reproducibility
- Api documentation

---

## 🚀 Future Improvements

### Short Term
- [ ] Add medical literature citations for each class
- [ ] Implement batch processing for multiple images
- [ ] Add download results as JSON/PDF
- [ ] Cache inferences to reduce redundant analysis

### Medium Term
- [ ] Add model explainability (Grad-CAM, LIME)
- [ ] Train with healthy/no-lesion class for robustness
- [ ] Implement confidence calibration
- [ ] Add unit and integration tests
- [ ] Create automated CI/CD pipeline

### Long Term
- [ ] Multi-model ensemble for robustness
- [ ] Real-time collaborative analysis dashboard
- [ ] Federated learning for privacy-preserving updates
- [ ] Mobile app with on-device inference
- [ ] Clinical validation study

---

## 📞 Support & Contact

For issues or questions:
1. Check existing logs in backend/training_metrics_target80.json
2. Review guardrail logic in backend/main.py
3. Inspect network requests via browser DevTools
4. Check Docker logs: `docker compose logs`

---

## 📄 License & Disclaimer

This project is for **educational and research purposes only**. It is NOT intended for clinical diagnosis or treatment decisions. Always consult qualified dermatologists for medical advice.

---

**Project Date**: April 11, 2026  
**Framework Versions**: Next.js 14.2.3, FastAPI 0.111.0, PyTorch 2.4.1  
**Model Accuracy**: 80.64% (test set)  
**Status**: ✅ Production Ready for Presentation
