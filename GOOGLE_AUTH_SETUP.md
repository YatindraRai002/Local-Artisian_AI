# Google Authentication Setup Guide

## The Issue
You're seeing "Google authentication is not properly configured" because the Google sign-in provider is not enabled in your Firebase console.

## Step-by-Step Fix

### 1. Enable Google Authentication in Firebase Console

1. **Go to Firebase Console**: https://console.firebase.google.com/
2. **Select your project**: "artisian-ai-9377c"
3. **Navigate to Authentication**:
   - Click "Authentication" in the left sidebar
   - Click "Sign-in method" tab
4. **Enable Google Provider**:
   - Find "Google" in the list of sign-in providers
   - Click on "Google"
   - Toggle the "Enable" switch to ON
   - Enter your email as the "Project support email"
   - Click "Save"

### 2. Enable Email/Password Authentication (if not already enabled)

1. In the same "Sign-in method" tab
2. Find "Email/Password" provider
3. Click on it and enable it
4. Click "Save"

### 3. Configure OAuth Consent Screen (if you encounter OAuth errors)

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Select the same project**: "artisian-ai-9377c"
3. **Navigate to OAuth consent screen**:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" user type
   - Fill in required fields:
     - App name: "Kala-Kaart"
     - User support email: your email
     - Developer contact information: your email
   - Save and continue through all steps

### 4. Verify Authorized Domains (if needed)

In Firebase Console → Authentication → Settings → Authorized domains:
- Ensure `localhost` is present (should be there by default)
- Add your production domain when you deploy

## What the Code Changes Fixed

1. **Enhanced Error Handling**: Added specific error messages for different Google auth issues
2. **Provider Validation**: Added checks to ensure Google provider is properly initialized
3. **Fallback Configuration**: Added fallback for Google provider initialization
4. **Better User Experience**: More descriptive error messages to help users understand the issue

## Testing the Fix

After enabling Google authentication in Firebase Console:

1. Refresh your application
2. Try clicking the "Continue with Google" button
3. You should now see the Google sign-in popup instead of the configuration error

## Common Error Messages and Solutions

- **"Google authentication is not enabled in Firebase Console"**: Enable Google sign-in method
- **"This domain is not authorized for Google authentication"**: Add domain to authorized domains
- **"Google authentication is not supported in this environment"**: Check browser settings or try incognito mode

## Verification

Once properly configured, you should see:
- Google sign-in popup opens when clicking the button
- No configuration errors in the browser console
- Successful authentication and redirect to the dashboard

If you still encounter issues after following these steps, check the browser console for specific error codes and refer to Firebase documentation.