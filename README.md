# FloodScope - An AI-Driven Flood Mapping System Using Dual Satellite Imagery

An advanced AI-powered flood detection and monitoring system that provides comprehensive, real-time flood risk assessments using cutting-edge technologies and multi-source data integration.

## 🌊 Key Features

### Advanced Analytics
- **Multi-source data validation** for enhanced accuracy
- **AI-powered risk assessment** with confidence scoring
- **Interactive flood maps** with real-time updates
- **Professional satellite data display** with acquisition details

### Enhanced User Experience
- **Clean, modern interface** with professional design
- **Improved AI assistant** with quick analysis buttons
- **Real-time data freshness** indicators
- **Comprehensive flood analytics** and metrics

## 🚀 Quick Start

### Option 1: Docker Installation (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd floodscope-ai
   ```

   <!-- major project  -->

2. **Set up environment variables:**
   ```bash
   cp .env.sample .env
   # Edit .env with your API keys (Sentinel Hub credentials are required)
   ```

3. **Run with Docker:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   Open http://localhost:5000 in your browser

### Option 2: Local Installation

#### Windows
```bash
./install.bat
```

#### Mac/Linux
```bash
chmod +x install.sh
./install.sh
```

## 🔐 Credential Configuration

Sentinel Hub credentials are mandatory for any feature that fetches satellite imagery. FloodScope reads them from the `SENTINEL_HUB_CLIENT_ID` and `SENTINEL_HUB_CLIENT_SECRET` environment variables. The application can also load them from a `.env` file so that local development remains convenient.

```bash
# Example .env (see .env.sample for the full template)
SENTINEL_HUB_CLIENT_ID=your_sentinel_hub_client_id_here
SENTINEL_HUB_CLIENT_SECRET=your_sentinel_hub_client_secret_here
```

### Local development

- Copy `.env.sample` to `.env` and fill in your credentials before running Streamlit.
- Alternatively export the variables directly (`export SENTINEL_HUB_CLIENT_ID=...`).
- Use the `FLOODSCOPE_ENV_FILE` variable if you need to point the app at a different credentials file (e.g., when running multiple projects side by side).

### Docker

- `docker-compose.yml` reads the credentials from your shell environment. You can either export them before running `docker compose up` or supply an env file via `docker compose --env-file my.env up`.
- When building custom images, pass the variables at runtime (`docker run -e SENTINEL_HUB_CLIENT_ID=... -e SENTINEL_HUB_CLIENT_SECRET=... floodscope-ai`).

### Continuous Integration / Deployment

- Store the credentials as encrypted secrets in your CI platform (e.g., `SENTINEL_HUB_CLIENT_ID`, `SENTINEL_HUB_CLIENT_SECRET`).
- Inject them into the workflow environment before running tests or deployment steps. The config module fails fast with a descriptive error if the values are missing, so misconfigurations surface immediately.

## 📱 How to Use

1. **Select Location:** Click on the map or use the search feature
2. **Run Analysis:** Click "Analyze Flood Risk" to get real-time assessment
3. **View Results:** Check flood risk levels, satellite data, and analytics
4. **Get Insights:** Use the AI assistant for instant analysis and recommendations

## 🛠 Technical Features

- **Multi-sensor Analysis:** Combines Sentinel-1 (radar) and Sentinel-2 (optical) data
- **Real-time Processing:** Live data integration with automatic updates
- **Enhanced Accuracy:** Multi-source validation for reliable flood detection
- **Professional Interface:** Clean, modern design with intuitive navigation
- **Time Accuracy:** Proper IST timezone handling for Indian locations


## 🐳 Docker Configuration

The system includes:
- **Automated health checks** for reliability
- **Persistent data storage** for caching
- **Proper timezone configuration** (Asia/Kolkata)
- **Environment variable management** for API keys

## 📖 Management Commands

### Docker
```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update and rebuild
git pull && docker-compose build && docker-compose up -d
```

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate.bat  # Windows

# Run the application
streamlit run app.py --server.port 5000

# Install new dependencies
pip install -r requirements-local.txt
```

## 🌍 Global Coverage

FloodScope AI provides accurate flood monitoring for locations worldwide, with enhanced focus on:
- **Indian subcontinent** with IST timezone support
- **Real-time validation** against actual ground conditions
- **Multi-language support** for international deployment

## 🔧 System Requirements

- **Python 3.8+** for local installation
- **Docker & Docker Compose** for containerized deployment
- **4GB RAM** minimum (8GB recommended)
- **Internet connection** for real-time API access

## 📞 Support

For issues, questions, or feature requests:
1. Check the troubleshooting section in docs
2. Review API key configuration
3. Verify Docker/Python installation
4. Contact support team

## 🎯 Accuracy Improvements

Recent enhancements ensure:
- **Realistic flood risk levels** that match actual conditions
- **Proper time correlation** with weather events
- **Enhanced precipitation detection** for better accuracy
- **Multi-source validation** for reliable assessments

---

**FloodScope AI** - Providing accurate, real-time flood monitoring for safer communities.

**Developed by Savitha M @2025
