# 🚀 Deployment Guide for Canairy

## Deployment to Render

### Prerequisites
1. A Render account (sign up at https://render.com)
2. GitHub repository connected to Render
3. API keys for various services (see below)

### Step 1: Connect GitHub Repository
1. Log in to your Render dashboard
2. Click "New +" and select "Web Service"
3. Connect your GitHub account if not already connected
4. Select the `manavpthaker/canairy` repository
5. Select the `main` branch

### Step 2: Configure Services
The `render.yaml` file is already configured with the following services:

#### Frontend (Static Site)
- **Name**: canairy
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `./dist`
- Automatically deployed from the repository

#### Backend API (Web Service)
- **Name**: canairy-api
- **Build Command**: Automatic from render.yaml
- **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

#### Database (PostgreSQL)
- **Name**: canairy-db
- Automatically provisioned with free tier

#### Cache (Redis)
- **Name**: canairy-redis
- Optional, will work without it

### Step 3: Set Environment Variables
In the Render dashboard for the `canairy-api` service, add these environment variables:

#### Required API Keys
```bash
# Financial Data
FRED_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here

# News & Information
NEWS_API_KEY=your_key_here

# Government Data
CONGRESS_API_KEY=your_key_here
BLS_API_KEY=your_key_here
LEGISCAN_API_KEY=your_key_here

# Conflict Data (optional)
ACLED_API_KEY=your_key_here
ACLED_EMAIL=your_email_here

# AI Features (optional)
OPENAI_API_KEY=your_key_here
```

#### How to Get API Keys:

1. **FRED API** (Federal Reserve Economic Data)
   - Sign up at: https://fred.stlouisfed.org/docs/api/api_key.html
   - Free tier available

2. **Alpha Vantage** (Stock Market Data)
   - Sign up at: https://www.alphavantage.co/support/#api-key
   - Free tier: 5 API calls/minute

3. **News API** (News Headlines)
   - Sign up at: https://newsapi.org/register
   - Free tier: 500 requests/day

4. **Congress API**
   - Sign up at: https://api.congress.gov/sign-up/
   - Free tier available

5. **BLS API** (Bureau of Labor Statistics)
   - Sign up at: https://www.bls.gov/developers/
   - Free tier available

6. **LegiScan API** (Legislative Data)
   - Sign up at: https://legiscan.com/legiscan
   - Free tier available

7. **ACLED** (Armed Conflict Data) - Optional
   - Request access at: https://acleddata.com/register/
   - Academic/non-profit access available

8. **OpenAI API** - Optional for AI features
   - Sign up at: https://platform.openai.com/
   - Paid service

### Step 4: Deploy via Render Dashboard

#### Option A: Manual Deployment
1. Go to your Render dashboard
2. Click "New +" → "Blueprint"
3. Connect to your GitHub repository
4. Select the `render.yaml` file
5. Click "Apply"

#### Option B: Deploy via Git Push
Once connected, Render will automatically deploy on every push to the main branch.

### Step 5: Verify Deployment

1. **Frontend**: Visit `https://canairy.onrender.com`
2. **API Health Check**: Visit `https://canairy-api.onrender.com/health`
3. **API Docs**: Visit `https://canairy-api.onrender.com/api/docs` (if DEBUG=true)

### Monitoring & Logs

Access logs in Render dashboard:
- Click on your service
- Go to "Logs" tab
- Filter by timestamp or search

### Troubleshooting

#### Common Issues:

1. **Build Failures**
   - Check Python version (should be 3.11)
   - Verify all dependencies in requirements.txt
   - Check build logs in Render dashboard

2. **API Connection Issues**
   - Verify VITE_API_URL in frontend environment
   - Check CORS settings in backend
   - Ensure API is running (check health endpoint)

3. **Missing Data**
   - Verify API keys are set correctly
   - Check rate limits for free tiers
   - Look for errors in API logs

4. **Performance Issues**
   - Free tier has limitations
   - Services may sleep after inactivity
   - Consider upgrading for production use

### Local Development

To run locally with Docker:
```bash
docker-compose up
```

To run without Docker:
```bash
# Backend
cd brown-man-bunker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload

# Frontend (in another terminal)
npm install
npm run dev
```

### Production Considerations

For production deployment:
1. Upgrade from free tier for better performance
2. Set up proper monitoring (Sentry, DataDog)
3. Configure backup strategies
4. Implement rate limiting per user
5. Set up CI/CD pipeline
6. Use environment-specific configurations
7. Enable HTTPS (automatic on Render)
8. Set up custom domain

### Support

- **Render Documentation**: https://render.com/docs
- **Project Issues**: https://github.com/manavpthaker/canairy/issues
- **API Documentation**: Once deployed, visit `/api/docs`

## 🎉 Deployment Complete!

Your Canairy Early Warning System should now be live at:
- Frontend: https://canairy.onrender.com
- API: https://canairy-api.onrender.com

Note: Free tier services may take 30-60 seconds to wake up after inactivity.