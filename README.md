# 🎮 AI Powered Online Game Addiction Monitor and Alert System

A comprehensive web-based application designed to monitor gaming behavior, detect game usage in real-time, analyze addiction patterns using AI, and send alert notifications to help maintain healthy gaming habits.

---

## 📋 Table of Contents

1. [Description](#description)
2. [Technologies Used](#technologies-used)
3. [Features](#features)
4. [Supported Games](#supported-games)
5. [Project Structure](#project-structure)
6. [Installation Setup](#installation-setup)
7. [How to Run](#how-to-run)
8. [Workflow](#workflow)
9. [Important Details](#important-details)
10. [Screenshots](#screenshots)

---

## 📖 Description

This is a full-stack web application developed to help users monitor and control their gaming habits. The system uses:

- **Real-time Process Monitoring**: Automatically detects when gaming applications are running on Windows
- **AI-Based Behavioral Analysis**: Analyzes gaming patterns and classifies users into risk categories (Normal, At Risk, Addicted)
- **Alert System**: Sends email notifications when games are detected
- **Desktop Application Mode**: Can run as a standalone desktop app with a floating monitoring bar
- **User Dashboard**: Provides statistics, charts, and recommendations for healthy gaming

The project is suitable for academic purposes and personal use.

---

## 🛠️ Technologies Used

### Backend
| Technology | Purpose |
|------------|---------|
| **Python** | Core programming language |
| **Flask** | Web framework for backend |
| **SQLite** | Lightweight database for storing user data |
| **Werkzeug** | Security (password hashing) |

### Frontend
| Technology | Purpose |
|------------|---------|
| **HTML5** | Markup language |
| **CSS3** | Styling and responsive design |
| **JavaScript** | Client-side interactivity |
| **Chart.js** | Weekly activity visualization |

### Desktop Application
| Technology | Purpose |
|------------|---------|
| **PyWebView** | Desktop GUI wrapper for Flask |
| **threading** | Concurrent monitoring |

### Additional Tools
| Technology | Purpose |
|------------|---------|
| **SMTP (Gmail)** | Email alerts |
| **subprocess** | Windows process detection |
| **pandas** | Data analysis |

---

## ✨ Features

### 🔐 User Authentication
- User registration with secure password hashing
- Login/logout functionality
- Session management

### 📊 Monitoring System
- Real-time game process detection
- Play time tracking (hours:minutes:seconds)
- Session history recording
- Floating monitoring bar (desktop mode)

### 🤖 AI Behavioral Analysis
- Rule-based addiction classification
- Risk score calculation (0-100)
- Three categories:
  - **Normal** (0-30): Healthy gaming habits
  - **At Risk** (31-60): Warning signs present
  - **Addicted** (61-100): Intervention needed

### 🔔 Alert System
- Email notifications when games are detected
- Configurable alert settings
- Alert history log
- Test alert functionality

### 📈 Dashboard & Analytics
- Today's play time display
- Session count tracking
- Weekly activity chart
- Personalized recommendations
- Risk level indicators

---

## 🎮 Supported Games

The system detects the following gaming platforms and games:

| Platform/Game | Process Name |
|---------------|--------------|
| Steam | `steam` |
| Epic Games Launcher | `epicgameslauncher` |
| Riot Client Services | `riotclientservices` |
| Valorant | `valorant` |
| League of Legends | `leagueclient` |
| Dota 2 | `dota2` |
| Counter-Strike 2 | `cs2` |
| CS:GO | `csgo` |
| Fortnite | `fortnite` |
| Minecraft | `minecraft` |
| Roblox | `roblox` |
| GTA V | `gta` |
| FIFA | `fifa` |
| eFootball | `efootball` |
| PUBG | `pubg` |

---

## 📁 Project Structure

```
AI Powered Online Game Addiction Monitor and Alert System/
│
├── app.py                    # Main Flask application
├── desktop_app.py            # Desktop launcher (PyWebView)
├── email_config.py           # Email configuration
├── model.py                  # AI behavioral analysis module
├── requirements.txt          # Python dependencies
├── users.db                  # SQLite database (auto-created)
│
├── data/
│   └── user_data.csv         # User data export
│
├── static/
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   ├── images/
│   │   ├── controller.png   # Login/register images
│   │   └── gaming_room.png  # Landing page image
│   └── js/
│       └── script.js         # Frontend JavaScript
│
└── templates/
    ├── index.html            # Landing page
    ├── login.html            # Login page
    ├── register.html         # Registration page
    ├── dashboard.html        # Main dashboard
    ├── monitor_bar.html      # Floating monitor bar
    ├── results.html          # Analysis results
    └── monitor_bar.html      # Desktop monitoring bar
```

---

## 💻 Installation Setup

### Prerequisites

1. **Python 3.8 or higher**
2. **Windows OS** (required for process detection)
3. **Gmail Account** (for email alerts)

### Step 1: Clone or Download the Project

```
bash
# If using Git
git clone <repository-url>
cd "AI Powered Online Game Addiction Monitor and Alert System"
```

### Step 2: Create Virtual Environment (Recommended)

```
bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```
bash
pip install -r requirements.txt
```

The required packages are:
- Flask>=2.3
- pandas>=2.1
- Werkzeug>=2.3
- Flask-Migrate>=4.0

### Step 4: Configure Email (Optional but Recommended)

For email alerts to work, you need to set up a Gmail App Password:

1. Go to [Google Account](https://myaccount.google.com)
2. Navigate to **Security** > **2-Step Verification** (enable it)
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Create a new app password for "Mail"
5. Update `email_config.py` with your Gmail and app password:

```
python
# In email_config.py
gmail_email = "your_email@gmail.com"
gmail_app_password = "your_16_char_app_password"
```

Or set environment variables:
```
bash
set GMAIL_EMAIL=your_email@gmail.com
set GMAIL_APP_PASSWORD=your_app_password
```

### Step 5: Run the Application

---

## 🚀 How to Run

### Option 1: Web Application Mode

```
bash
python app.py
```

Then open your browser and visit:
```
http://127.0.0.1:5000
```

### Option 2: Desktop Application Mode

```
bash
python desktop_app.py
```

This will open:
- Main application window (1200x800)
- Floating monitoring bar (always on top)

---

## 🔄 Workflow

### 1. User Registration & Login
```
Landing Page → Register → Login → Dashboard
```

### 2. Starting Monitoring
```
Dashboard → Click "Start Monitoring" → Monitoring begins
```

### 3. Game Detection Process
```
User starts a game → System detects process → 
Sends email alert → Records session → Updates stats
```

### 4. Stopping & Review
```
User stops monitoring → Session saved to database → 
View history & statistics → AI analysis displayed
```

### Detailed Workflow:

1. **Registration**: User creates an account with name, email, and password
2. **Login**: User authenticates with email and password
3. **Dashboard**: User sees overview of gaming stats and recommendations
4. **Start Monitoring**: User clicks "Start" to begin tracking
5. **Process Detection**: Background worker checks for game processes every 3 seconds
6. **Game Detected**: 
   - Alert triggered (email sent if enabled)
   - Floating bar updates to show "Playing: [game name]"
   - Session timer continues
7. **Stop Monitoring**: User clicks "Stop" to end session
8. **Data Recording**: Total play time saved to database
9. **Analysis**: AI analyzes behavior and provides recommendations

---

## ⚠️ Important Details

### Security Considerations

1. **Change Default Secret Key**: Edit `app.py` and change:
   
```
python
   app.secret_key = "change_this_secret_key"
   
```

2. **Email Configuration**: Never commit your email credentials to version control. Use environment variables or keep credentials private.

3. **Database**: The `users.db` file is created automatically. For production, consider using a more robust database.

### System Requirements

- **Operating System**: Windows (required for process detection via `tasklist`)
- **Browser**: Modern browser (Chrome, Firefox, Edge)
- **Python**: 3.8+
- **Internet**: Required for email alerts

### Configuration Options

You can modify various settings in the code:

| Setting | Location | Description |
|---------|----------|-------------|
| Game Keywords | `app.py` | Add/remove game process names |
| Monitor Interval | `app.py` | Detection frequency (default: 3 seconds) |
| Risk Thresholds | `model.py` | AI classification thresholds |
| Alert Settings | Dashboard | Email/SMS preferences |

### Testing the Application

1. Register a new account
2. Login with credentials
3. Configure email in Alerts section
4. Click "Start Monitoring"
5. Launch a game (e.g., Steam, Minecraft)
6. Observe detection and alerts

---

## 📸 Screenshots

### Landing Page
- Hero section with gaming illustration
- Login and Register buttons
- Professional gradient design

### Login/Register
- Split-screen layout
- Gaming controller imagery
- Clean form design

### Dashboard
- Quick actions panel
- Statistics cards (play time, risk level, status)
- Weekly activity chart
- Recent alerts
- Recommendations

### Monitoring Page
- Start/Pause/Stop controls
- Real-time timer display
- Game detection status
- Session history

### Alerts Page
- Email configuration status
- Test alert functionality
- Alert history log

---

## 🔧 Troubleshooting

### Issue: Game Not Detected

1. Make sure the game process is in the `GAME_KEYWORDS` list
2. Check if the process name matches exactly
3. Try running the game before starting monitoring

### Issue: Email Not Sending

1. Verify Gmail app password is correct
2. Check that 2-Step Verification is enabled
3. Ensure app password is generated for "Mail"
4. Check console for error messages

### Issue: Desktop App Not Opening

1. Install PyWebView: `pip install pywebview`
2. Check if port 5000 is available
3. Try running `app.py` first to test

---

## 📄 License

This project is for educational purposes. Use responsibly.

---

## 👨‍💻 Author

Created as an academic project for BCA (Bachelor of Computer Applications).

---

## 🙏 Acknowledgments

- Flask Documentation
- WHO Gaming Disorder Guidelines
- PyWebView Documentation
