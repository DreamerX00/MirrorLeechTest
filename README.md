# WZML-X: Advanced Mirror-Leech Telegram Bot

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=flat-square&logo=docker)](https://www.docker.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?style=flat-square&logo=telegram)](https://telegram.org/)
[![Version](https://img.shields.io/badge/Version-1.4.0--x-green?style=flat-square)](https://github.com/weebzone/WZML-X)
[![License](https://img.shields.io/badge/License-GPL--3.0-red?style=flat-square)](LICENSE)

**A powerful, feature-rich Telegram bot for mirroring and leeching files to multiple cloud platforms**

[🚀 Features](#-features) • [⚡ Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [🔧 Configuration](#-configuration) • [🤝 Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation Methods](#-installation-methods)
- [Configuration](#-configuration)
- [Commands](#-commands)
- [Advanced Features](#-advanced-features)
- [Authorization System](#-authorization-system)
- [Contributing](#-contributing)
- [Support](#-support)
- [License](#-license)

## 🎯 Overview

WZML-X is an advanced, feature-rich Telegram bot designed for efficient file mirroring and leeching operations. Built with modern asynchronous architecture, it supports multiple download sources and upload destinations, making it the perfect solution for file management and distribution.

### What makes WZML-X special?

- **Multi-platform Support**: Mirror to Google Drive, Telegram, and any rclone-supported cloud service
- **High Performance**: Asynchronous operations with queue management and concurrent downloads
- **Comprehensive Format Support**: Torrents, direct links, YouTube videos, and Telegram files
- **Advanced Features**: File compression, extraction, thumbnail generation, and media information
- **Enterprise-grade**: Built-in authorization system, user management, and analytics

## ✨ Features

### 🔄 **Core Functionality**
- **Mirror**: Download and upload files to Google Drive or rclone cloud storage
- **Leech**: Download and upload files directly to Telegram
- **Clone**: Directly clone Google Drive files/folders
- **Multi-source Support**: Torrents, magnets, direct links, YouTube, Telegram files

### 🛠️ **Download Engines**
- **Aria2c**: High-speed HTTP/FTP/SFTP downloads
- **qBittorrent**: Advanced BitTorrent client with selection support
- **yt-dlp**: YouTube and 1000+ sites video/audio extraction
- **Mega**: Mega.nz direct integration
- **Telegram**: Native Telegram file handling

### ☁️ **Upload Destinations**
- **Google Drive**: Team Drive and personal drive support
- **Rclone**: 40+ cloud storage providers
- **Telegram**: Split large files automatically
- **DDL Servers**: Direct download link generation

### 🎛️ **Advanced Features**
- **File Operations**: Zip/Unzip, 7z extraction, file joining
- **Media Processing**: Thumbnail generation, screenshots, metadata extraction
- **Queue Management**: Download/upload queues with priority handling
- **User Management**: Authorization system with subscription support
- **Real-time Monitoring**: Live status updates and progress tracking

### 🔐 **Security & Management**
- **Token-based Authorization**: Secure user verification system
- **Subscription Management**: Tiered access control
- **Admin Controls**: Comprehensive bot administration
- **Blacklist/Whitelist**: User and chat access control

## ⚡ Quick Start

### Prerequisites

- Python 3.8+ 
- MongoDB database
- Telegram Bot Token ([Get from BotFather](https://t.me/BotFather))
- Google Drive API credentials (optional but recommended)

### 🚀 One-Click Deployment

#### Heroku
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

#### Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

#### Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### 🐳 Docker Deployment

```bash
# Clone the repository
git clone https://github.com/weebzone/WZML-X.git
cd WZML-X

# Configure environment
cp config_sample.env config.env
# Edit config.env with your settings

# Build and run with Docker Compose
docker-compose up -d
```

### 📱 Local Installation

```bash
# Clone repository
git clone https://github.com/weebzone/WZML-X.git
cd WZML-X

# Install dependencies
pip install -r requirements.txt

# Configure bot
cp config_sample.env config.env
# Edit config.env file

# Run bot
python -m bot
```

## 🔧 Configuration

### Essential Configuration

Create `config.env` file with the following required variables:

```env
# Bot Configuration
BOT_TOKEN = "your_bot_token_here"
OWNER_ID = "your_telegram_user_id"
TELEGRAM_API = "your_api_id"
TELEGRAM_HASH = "your_api_hash"

# Database
DATABASE_URL = "mongodb_connection_string"

# Google Drive (Optional)
GDRIVE_ID = "your_google_drive_folder_id"
```

### Complete Configuration Options

<details>
<summary>Click to see all configuration variables</summary>

#### **Authentication & Access**
```env
AUTHORIZED_CHATS = ""          # Authorized chat IDs
SUDO_USERS = ""               # Sudo user IDs
BLACKLIST_USERS = ""          # Blacklisted user IDs
USER_SESSION_STRING = ""      # Pyrogram session string
```

#### **Download Configuration**
```env
DOWNLOAD_DIR = "/downloads/"   # Download directory
DEFAULT_UPLOAD = "gd"         # Default upload destination
STATUS_UPDATE_INTERVAL = "10" # Status update interval (seconds)
```

#### **File Management**
```env
EXTENSION_FILTER = ""         # File extension filter
STOP_DUPLICATE = "False"      # Stop duplicate uploads
AUTO_DELETE_MESSAGE_DURATION = "60" # Auto-delete messages
```

#### **Google Drive Settings**
```env
USE_SERVICE_ACCOUNTS = "False" # Use service accounts
IS_TEAM_DRIVE = "False"       # Team drive support
INDEX_URL = ""                # Index URL for direct links
```

#### **Advanced Features**
```env
YT_DLP_OPTIONS = ""           # yt-dlp custom options
RCLONE_FLAGS = ""             # Rclone flags
METADATA = "False"            # Extract metadata
```

</details>

## 📚 Commands

### 🔄 **Mirror Commands**
```
/mirror [url] - Mirror files to Google Drive
/qbmirror [url] - Mirror torrents using qBittorrent
/ytdl [url] - Mirror YouTube videos/playlists
/clone [gdrive_url] - Clone Google Drive files
```

### 📤 **Leech Commands**
```
/leech [url] - Upload files to Telegram
/qbleech [url] - Leech torrents to Telegram
/ytdlleech [url] - Leech YouTube content to Telegram
```

### 🛠️ **Utility Commands**
```
/status - Show download status
/list [query] - Search Google Drive
/count [gdrive_url] - Count Drive files
/del [gdrive_url] - Delete Drive files
/speedtest - Test server speed
/stats - Bot statistics
```

### 👑 **Admin Commands**
```
/users - User statistics
/authorize - Authorize users
/unauthorize - Remove authorization
/broadcast - Broadcast messages
/shell - Execute shell commands
/eval - Execute Python code
```

### Command Flags & Options

Most commands support various flags for customization:

```
-n <name>     : Custom filename
-e/-uz        : Extract archives
-z            : Compress to ZIP
-s            : Select files from torrent
-d            : Seed after download
-up <dest>    : Upload destination
-rcf <flags>  : Custom rclone flags
```

**Example Usage:**
```
/mirror https://example.com/file.zip -n "MyFile" -e -up gdrive
/leech magnet:?xt=... -s -d 2:5
/ytdl https://youtube.com/watch?v=... -z
```

## 🔐 Authorization System

WZML-X includes a sophisticated authorization bot for user management:

### Features
- **Token-based verification** with 6-hour expiration
- **Subscription tiers** (7-day, 30-day, 90-day)
- **Payment gateway integration**
- **Admin dashboard** for user management
- **URL shortening** integration

### Setup Authorization Bot

```bash
cd auth_bot
cp .env.sample .env
# Configure auth bot settings
python -m auth_bot
```

## 🎨 Advanced Features

### **Multi-source Downloads**
- Direct HTTP/HTTPS links
- BitTorrent files and magnet links
- YouTube and 1000+ supported sites
- Google Drive links
- Mega.nz links
- Telegram files

### **Smart File Handling**
- Automatic file type detection
- Compression and extraction support
- File joining and splitting
- Thumbnail generation
- Media metadata extraction

### **Queue Management**
- Intelligent download queuing
- Upload queue with priority
- Concurrent operation limits
- Real-time progress tracking

### **Cloud Integration**
- Google Drive with Team Drive support
- 40+ cloud providers via rclone
- Service account rotation
- Index page generation

## 🛡️ Security Features

- **User Authorization**: Token-based verification system
- **Rate Limiting**: Prevents spam and abuse
- **Blacklist System**: Block malicious users
- **Secure Configuration**: Environment-based secrets
- **Access Control**: Chat and user-based permissions

## 🔧 Development

### Project Structure
```
WZML-X/
├── bot/                    # Main bot code
│   ├── helper/            # Helper utilities
│   ├── modules/           # Command modules
│   └── __main__.py        # Bot entry point
├── auth_bot/              # Authorization system
├── web/                   # Web interface
├── requirements.txt       # Dependencies
├── config_sample.env      # Sample configuration
└── Dockerfile            # Docker configuration
```

### Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/weebzone/WZML-X.git
cd WZML-X

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up development environment
cp config_sample.env config.env
# Configure for development

# Run bot
python -m bot
```

## 📊 Performance & Monitoring

- **Real-time Status**: Live download/upload progress
- **System Monitoring**: CPU, RAM, disk usage tracking
- **Analytics Dashboard**: User activity and bot statistics
- **Error Logging**: Comprehensive error tracking and reporting

## 🌐 Multi-language Support

WZML-X supports multiple languages and can be easily localized:
- English (default)
- Custom language files supported
- RTL language support
- Unicode and emoji support

## 🤝 Support & Community

### Get Help
- 📢 **Updates Channel**: [@WZML_X](https://t.me/WZML_X)
- 💬 **Support Group**: [Join Discussion](https://t.me/WZML_X_Support)
- 📖 **Documentation**: [Wiki](https://github.com/weebzone/WZML-X/wiki)
- 🐛 **Bug Reports**: [Issues](https://github.com/weebzone/WZML-X/issues)

### FAQs

<details>
<summary>Common Questions</summary>

**Q: How do I get Google Drive API credentials?**
A: Follow our [Google Drive Setup Guide](docs/gdrive-setup.md)

**Q: Can I use custom rclone configs?**
A: Yes! Upload your rclone.conf to the bot or use the built-in setup

**Q: How do I enable qBittorrent?**
A: Set up qBittorrent Web UI and configure the connection in your config

**Q: What's the maximum file size limit?**
A: Depends on your storage provider. Telegram has a 2GB limit per file

</details>

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### Third-party Components
- [Pyrogram](https://pyrogram.org/) - Telegram client library
- [aria2](https://aria2.github.io/) - Download utility
- [qBittorrent](https://www.qbittorrent.org/) - BitTorrent client
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Media downloader
- [rclone](https://rclone.org/) - Cloud storage sync

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=weebzone/WZML-X&type=Date)](https://star-history.com/#weebzone/WZML-X&Date)

## 📈 Statistics

![GitHub stars](https://img.shields.io/github/stars/weebzone/WZML-X?style=social)
![GitHub forks](https://img.shields.io/github/forks/weebzone/WZML-X?style=social)
![GitHub issues](https://img.shields.io/github/issues/weebzone/WZML-X)
![GitHub pull requests](https://img.shields.io/github/issues-pr/weebzone/WZML-X)

---

<div align="center">

**⭐ If you find WZML-X useful, please give it a star! ⭐**

Made with ❤️ by the WeebZone Team

[🔝 Back to Top](#wzml-x-advanced-mirror-leech-telegram-bot)

</div>
