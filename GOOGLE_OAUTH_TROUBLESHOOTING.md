# Google OAuth 403 Error Troubleshooting Guide

## Common Causes of 403 Error

### 1. **Authorized Origins Not Set**
The most common cause of 403 errors is missing authorized origins in Google Console.

**Fix:**
1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Select your project
3. Go to "APIs & Services" > "Credentials"
4. Click on your OAuth 2.0 Client ID
5. Add these to "Authorized JavaScript origins":
   - `http://localhost:3000` (for development)
   - `https://yourdomain.com` (for production)
   - `http://127.0.0.1:3000` (alternative localhost)

### 2. **Wrong Client ID Type**
Make sure you're using a "Web application" client ID, not "Desktop" or "Mobile".

**Fix:**
1. In Google Console, go to "Credentials"
2. Create a new OAuth 2.0 Client ID
3. Select "Web application" as the application type
4. Add authorized origins as above

### 3. **Environment Variable Issues**
The client ID might not be loaded properly.

**Fix:**
1. Create `.env` file in the `website/` directory:
   ```
   REACT_APP_GOOGLE_CLIENT_ID=your-actual-client-id-here
   ```
2. Restart your development server after adding the env file
3. Check browser console for "Google Client ID: Set" message

### 4. **Google APIs Not Enabled**
Required Google APIs might not be enabled.

**Fix:**
1. Go to "APIs & Services" > "Library"
2. Enable these APIs:
   - Google+ API (deprecated but still needed)
   - Google Identity Services API
   - People API

### 5. **Domain Verification**
For production domains, you might need to verify ownership.

**Fix:**
1. Go to "APIs & Services" > "OAuth consent screen"
2. Add your domain to "Authorized domains"
3. Verify domain ownership if required

## Debugging Steps

### Step 1: Check Console Logs
Open browser developer tools and look for:
- "Google Client ID: Set" or "Not set"
- "Google Identity Services initialized successfully"
- Any error messages

### Step 2: Verify Client ID Format
Your client ID should look like:
```
123456789-abcdefghijklmnop.apps.googleusercontent.com
```

### Step 3: Test with Different Origins
Try adding these origins to your Google Console:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:3001` (if using different port)

### Step 4: Check Network Tab
In browser dev tools, go to Network tab and look for:
- Failed requests to `accounts.google.com`
- 403 status codes
- CORS errors

## Quick Test

To test if your setup is working:

1. Open browser console
2. Click the login button
3. Look for these messages:
   - "Attempting Google login..."
   - "Google Identity Services initialized successfully"
   - Any error messages

## Still Having Issues?

If you're still getting 403 errors:

1. **Double-check the client ID** - Make sure it's copied correctly
2. **Wait a few minutes** - Google Console changes can take time to propagate
3. **Try incognito mode** - Clear any cached authentication states
4. **Check browser console** - Look for specific error messages

## Alternative: Use One Tap Instead

If the popup continues to fail, you can try using Google's One Tap:

```javascript
// In initializeGoogleAuth method, change:
window.google.accounts.id.prompt();

// To:
window.google.accounts.id.renderButton(
  document.getElementById('google-signin-button'),
  { theme: 'outline', size: 'large' }
);
```

This renders a button directly instead of using a popup.
