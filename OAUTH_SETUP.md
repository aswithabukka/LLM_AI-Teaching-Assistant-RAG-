# OAuth Setup Guide

This guide will help you set up social login with Google and GitHub.

## 🔧 Quick Setup Steps

### 1. Copy Environment File
```bash
cp .env.example .env
```

### 2. Add Your OAuth Credentials
Edit the `.env` file and uncomment/fill in the OAuth credentials:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_actual_google_client_id
GOOGLE_CLIENT_SECRET=your_actual_google_client_secret

# GitHub OAuth  
GITHUB_CLIENT_ID=your_actual_github_client_id
GITHUB_CLIENT_SECRET=your_actual_github_client_secret
```

## 📋 Provider Setup Instructions

### 🔍 Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Web application"
6. Add authorized redirect URI: `http://localhost:8501/oauth/callback`
7. Copy the Client ID and Client Secret to your `.env` file

### 🐙 GitHub OAuth Setup  
1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - Application name: StudyMate AI
   - Homepage URL: `http://localhost:8501`
   - Authorization callback URL: `http://localhost:8501/oauth/callback`
4. Copy the Client ID and Client Secret to your `.env` file


## 🚀 Testing Your Setup

1. Restart your application:
   ```bash
   # Stop current services
   pkill -f "uvicorn|streamlit"
   
   # Start again
   python run_app.py
   ```

2. Visit [http://localhost:8501](http://localhost:8501)

3. You should now see OAuth login buttons for the providers you configured!

## 🔒 Security Notes

- Keep your OAuth credentials secure and never commit them to version control
- For production deployment, update the redirect URIs to match your domain
- The `.env` file is already in `.gitignore` to prevent accidental commits

## 💡 Troubleshooting

**No OAuth buttons showing?**
- Check that your `.env` file has the correct variable names
- Ensure you've restarted the application after adding credentials
- Verify there are no typos in your environment variables

**OAuth login fails?**
- Double-check your redirect URIs match exactly: `http://localhost:8501/oauth/callback`
- Ensure your OAuth app is not in development/sandbox mode (for Facebook)
- Check the browser console for any error messages

## 📞 Need Help?

If you encounter issues:
1. Check the application logs in your terminal
2. Verify your OAuth app settings in the provider's console
3. Ensure all redirect URIs are correctly configured
