# Google OAuth Setup Guide

## Step-by-Step Instructions to Enable Google Identity Services

### 1. Access Google Cloud Console
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Select your project or create a new one

### 2. Enable Required APIs
Navigate to **APIs & Services** → **Library** and enable these APIs:

#### A. Google Identity Services API
1. Search for "Google Identity Services API"
2. Click on it and press **"Enable"**

#### B. People API (Alternative to Google+ API)
1. Search for "People API"
2. Click on it and press **"Enable"**
3. This replaces the deprecated Google+ API

#### C. Google Sign-In API (Optional)
1. Search for "Google Sign-In API" 
2. Click on it and press **"Enable"**
3. This may also be listed as "Google Identity"


### 3. Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"**
3. Select **"OAuth 2.0 Client ID"**

### 4. Configure OAuth Consent Screen (if not done)
If prompted, configure the OAuth consent screen:
1. Choose **"External"** (for testing)
2. Fill in required fields:
   - **App name**: StudyMate AI
   - **User support email**: Your email
   - **Developer contact email**: Your email
3. Add scopes:
   - `email`
   - `profile`
   - `openid`
4. Add test users (your email) for testing

### 5. Create OAuth Client ID
1. **Application type**: Web application
2. **Name**: StudyMate AI
3. **Authorized JavaScript origins**: 
   ```
   http://localhost:8501
   ```
4. **Authorized redirect URIs**:
   ```
   http://localhost:8501/oauth/callback
   ```
5. Click **"CREATE"**

### 6. Copy Credentials
1. Copy the **Client ID** and **Client Secret**
2. Add them to your `.env` file:
   ```
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```

### 7. Test the Integration
1. Restart your StudyMate AI application
2. Try the Google OAuth login

## Troubleshooting

### Common Issues:
- **404 Error**: Check redirect URI matches exactly
- **Access Denied**: Ensure APIs are enabled
- **Invalid Client**: Verify Client ID and Secret are correct

### Required APIs Summary:
✅ Google Identity Services API
✅ People API  
✅ Google OAuth2 API

### Correct Redirect URI:
```
http://localhost:8501/oauth/callback
```

**Note**: Make sure to use `http://` (not `https://`) for localhost development.
