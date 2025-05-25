# Smart Budget App - Installation Guide

## 📋 Prerequisites

1. **Python 3.8 or higher** - Download from [python.org](https://python.org)
2. **pip** (Python package installer) - Usually comes with Python
3. **Firebase Project** - Set up at [Firebase Console](https://console.firebase.google.com)
4. **Google AI Studio Account** - For Gemini API access

## 🚀 Installation Steps

### 1. Install Python Dependencies

Run this command in your project directory:

```bash
pip install -r requirements.txt
```

Or install packages individually:

```bash
pip install streamlit>=1.28.0
pip install firebase-admin>=6.2.0
pip install pyrebase4>=4.8.0
pip install google-generativeai>=0.3.0
pip install plotly>=5.17.0
pip install pandas>=2.0.0
pip install requests>=2.31.0
pip install python-dotenv>=1.0.0
pip install numpy>=1.24.0
```

### 2. Firebase Configuration Files

You need these two Firebase configuration files in your project root:

#### `firebase_key.json`
- Download from Firebase Console → Project Settings → Service Accounts
- Generate new private key for Firebase Admin SDK

#### `firebase_config.json`
- Download from Firebase Console → Project Settings → General → Your apps
- Web app configuration

Example structure:
```json
{
  "apiKey": "your-api-key",
  "authDomain": "your-project.firebaseapp.com",
  "projectId": "your-project-id",
  "storageBucket": "your-project.appspot.com",
  "messagingSenderId": "123456789",
  "appId": "your-app-id"
}
```

### 3. Environment Variables

Create or update `.env` file with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

**⚠️ Security Note**: Never commit these files to Git! They're already in your `.gitignore`.

### 4. Firebase Setup

In your Firebase Console:

1. **Enable Authentication**:
   - Go to Authentication → Sign-in method
   - Enable Email/Password authentication

2. **Set up Firestore Database**:
   - Go to Firestore Database
   - Create database in production mode
   - Set up security rules as needed

3. **Create Collections**:
   Your app will automatically create these collections:
   - `users` - User profiles and budget data
   - User documents will contain: income, categories, budget_allocations, etc.

### 5. Get API Keys

#### Gemini API Key:
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Add it to your `.env` file

#### GROQ API Key (Optional):
1. Go to [GROQ Console](https://console.groq.com/)
2. Create an account and get API key
3. Add it to your `.env` file

## 🏃‍♂️ Running the Application

1. Navigate to your project directory:
```bash
cd e:\smart_budget
```

2. Run the Streamlit app:
```bash
streamlit run main.py
```

3. Open your browser to `http://localhost:8501`

## 📁 Project Structure

```
smart_budget/
├── main.py                 # Main application
├── auth.py                 # Authentication logic
├── onboarding.py          # User onboarding
├── budget_setup.py        # Budget creation & management
├── budget_ai.py           # AI budget recommendations
├── finance_chatbot.py     # Financial assistant chatbot
├── shared.py              # Firebase configuration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (DO NOT COMMIT)
├── .gitignore            # Git ignore file
├── firebase_key.json     # Firebase service account (DO NOT COMMIT)
├── firebase_config.json  # Firebase config (DO NOT COMMIT)
└── budget-buddy/         # React app (currently unused)
```

## 🔧 Features Available

✅ **User Authentication** - Email/password login and signup
✅ **User Onboarding** - Income, currency, and category selection
✅ **Budget Setup** - Manual budget allocation or AI-assisted
✅ **AI Budget Recommendations** - Powered by Gemini AI
✅ **Financial Assistant** - Interactive chatbot for financial advice
✅ **Gamification** - Login streaks, achievements, budget health scores
✅ **Data Visualization** - Charts and graphs with Plotly
✅ **Savings Goals** - Track progress toward financial goals
✅ **Transaction Management** - Add and categorize expenses

## 🐛 Troubleshooting

### Common Issues:

1. **Firebase Authentication Error**:
   - Check `firebase_config.json` is correct
   - Verify Email/Password is enabled in Firebase Console

2. **Firestore Permission Error**:
   - Update Firestore security rules
   - Check `firebase_key.json` has proper permissions

3. **Gemini API Error**:
   - Verify `GEMINI_API_KEY` in `.env` file
   - Check API quota limits in Google AI Studio

4. **Module Import Error**:
   - Ensure all packages from `requirements.txt` are installed
   - Try updating pip: `pip install --upgrade pip`

## 🎯 Next Steps

After installation:

1. **Create your first user account**
2. **Complete the onboarding process**
3. **Set up your budget categories**
4. **Try the AI budget recommendations**
5. **Explore the financial assistant chatbot**
6. **Start tracking your expenses**

## 🔐 Security Reminders

- Never commit API keys or Firebase credentials to Git
- Keep your `.env` file local only
- Regularly rotate API keys
- Monitor Firebase usage and costs
- Set up proper Firestore security rules

Happy budgeting! 💰
