# Setup Instructions

## Option 1: Docker (Recommended - Easiest) ✅

### What you need:
- Docker Desktop

### Steps:

1. **Download Docker Desktop**
   - Windows: https://www.docker.com/products/docker-desktop
   - Mac: https://www.docker.com/products/docker-desktop
   - Linux: `sudo apt-get install docker.io docker-compose`

2. **Navigate to project folder**
   ```bash
   cd "C:\Study material\SKIN_CANCER"
   ```

3. **Run the startup script**
   
   **Windows (Command Prompt or PowerShell):**
   ```bash
   run-docker.bat
   ```
   
   **Linux/Mac:**
   ```bash
   bash run-docker.sh
   ```

4. **Wait for services to start** (~30 seconds)

5. **Open in browser:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

6. **Stop services:**
   ```bash
   docker-compose down
   ```

---

## Option 2: Manual Setup (Without Docker)

### What you need:
- Python 3.9 or higher
- Node.js 18 or higher
- pip and npm (usually included)

### Backend Setup

1. **Open PowerShell/Terminal in backend folder**
   ```bash
   cd backend
   ```

2. **Create Python virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start backend server**
   ```bash
   python main.py
   ```
   You should see: `Uvicorn running on http://0.0.0.0:8000`

### Frontend Setup (in new terminal)

1. **Navigate to frontend folder**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```
   You should see: `Local: http://localhost:3000`

4. **Open browser**
   - Frontend: http://localhost:3000

---

## Verification Checklist

- [ ] Backend API is running (check http://localhost:8000/health)
- [ ] Frontend is running (check http://localhost:3000)
- [ ] Can see "DermAI" title on homepage
- [ ] Can upload an image
- [ ] Analysis completes with results

---

## Troubleshooting

### Docker Issues

**"Docker is not installed"**
- Download Docker Desktop: https://www.docker.com/products/docker-desktop
- Restart your computer after installation

**"docker-compose command not found"**
- On Linux: `sudo apt-get install docker-compose`
- On Mac/Windows: Docker Desktop includes docker-compose

**Services won't start**
- Check if ports 3000 or 8000 are already in use
- Kill processes: `docker-compose down -v`
- Try again: `docker-compose up -d`

### Python Issues

**"Python not found"**
- Install Python 3.9+: https://www.python.org/downloads

**"pip: command not found"**
- Reinstall Python with pip option checked

**"Module not found" errors**
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

### Node.js Issues

**"npm: command not found"**
- Install Node.js 18+: https://nodejs.org

**"Cannot find module" errors**
- Delete node_modules: `rm -rf node_modules`
- Run: `npm install`

### Connection Issues

**"Failed to connect to API"**
- Ensure backend is running on port 8000
- Check: http://localhost:8000/health
- If using Docker, services might still be starting (~30 seconds)

**CORS errors**
- Backend has CORS enabled by default
- If frontend/backend on different ports, this is normal

---

## Getting Help

Check the README.md for more information or review logs:

```bash
# Docker logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```
