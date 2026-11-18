# 🚀 Deploying to Vercel

Your project has been prepared for Vercel Serverless deployment with:
* `vercel.json` (Vercel Serverless Python routing)
* `api/index.py` (Serverless FastAPI entrypoint)
* `/api/set-webhook` (One-click Telegram webhook registration)

---

## Method 1: Deploy via GitHub & Vercel Dashboard (Easiest)

1. Push this folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/gmail-updates.git
   git push -u origin main
   ```
2. Go to [vercel.com/new](https://vercel.com/new) and import your repository.
3. Under **Environment Variables**, add:
   * `TELEGRAM_BOT_TOKEN`: (Your Telegram Bot Token from @BotFather)
   * `GOOGLE_CLIENT_ID`: (Your Google Client ID from Google Cloud Console)
   * `GOOGLE_CLIENT_SECRET`: (Your Google Client Secret)
   * `GEMINI_API_KEY`: (Your Gemini API Key from Google AI Studio)
   * `BASE_URL`: `https://YOUR-APP-NAME.vercel.app`
   * `GOOGLE_REDIRECT_URI`: `https://YOUR-APP-NAME.vercel.app/api/auth/callback`
   * `SUPABASE_URL`: (Your Supabase URL, optional)
   * `SUPABASE_KEY`: (Your Supabase Anon Key, optional)
4. Click **Deploy**!

---

## Method 2: Deploy via Terminal (Vercel CLI)

1. Log in to Vercel:
   ```bash
   npx vercel login
   ```
2. Deploy to production:
   ```bash
   npx vercel --prod
   ```

---

## Post-Deployment (2 Steps):

1. **Activate Telegram Webhook**:
   Once deployed, simply open this link in your browser:
   ```text
   https://YOUR-APP-NAME.vercel.app/api/set-webhook
   ```
   *(Telegram will respond: `{"ok": true, "result": true, "description": "Webhook was set"}`)*

2. **Add to Google Cloud Console**:
   In [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials):
   Add to **Authorized redirect URIs**:
   ```text
   https://YOUR-APP-NAME.vercel.app/api/auth/callback
   ```
