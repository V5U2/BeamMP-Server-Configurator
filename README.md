# BeamMP Server Configurator

A simple web-based configuration tool for BeamMP servers that allows you to easily modify your `ServerConfig.toml` file through a modern, user-friendly interface.

## Features

- 🎛️ **Easy Configuration**: Modify all BeamMP server settings through a web interface
- 🔄 **Automatic Backups**: Creates backups before saving changes
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🔒 **Safe Operations**: Confirms before restoring backups
- 🎨 **Modern UI**: Beautiful, intuitive interface with Bootstrap 5

## Prerequisites

- Python 3.7 or higher
- Your `ServerConfig.toml` file in the same directory

## Installation

1. **Clone or download this repository** to your BeamMP server directory

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your configuration**:
   ```bash
   # Copy the example configuration
   cp ServerConfig.example.toml ServerConfig.toml
   
   # Edit the configuration with your settings
   # Or use the web interface after starting the app
   ```

## Usage

1. **Start the web configurator**:
   ```bash
   python app.py
   ```

2. **Open your web browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Configure your server**:
   - Use the "General Settings" tab to modify server name, port, max players, etc.
   - Use the "Misc Settings" tab for error reporting and update preferences
   - Use the "Backups" tab to restore previous configurations

4. **Save your changes** by clicking the "Save Configuration" button

## Configuration Sections

### General Settings
- **Server Name**: The name displayed in the server list
- **Description**: Brief description of your server
- **Port**: Server port (default: 30814)
- **Max Players**: Maximum number of players allowed
- **Max Cars**: Maximum cars per player
- **Map**: Path to the map file
- **Resource Folder**: Folder containing server resources
- **Tags**: Comma-separated tags for server identification
- **Auth Key**: Your BeamMP authentication key
- **Private Server**: Whether the server is private
- **Debug Mode**: Enable debug logging
- **Log Chat**: Log chat messages to console

### Misc Settings
- **Show Error Messages**: Display error messages on startup
- **Send Errors**: Send error reports to BeamMP developers
- **Hide Update Messages**: Hide periodic update notifications

## Backup System

The configurator automatically creates backups before saving changes. Backups are stored in the `backups/` directory with timestamps.

### Restoring Backups
1. Go to the "Backups" tab
2. Click "Restore" next to the backup you want to restore
3. Confirm the restoration

## Security Notes

- The web interface runs on `0.0.0.0:5000` by default, making it accessible from other devices on your network
- Consider using a firewall or running the application only when needed
- The application includes a secret key for session management

## Git Repository Setup

To set up this project as a Git repository:

1. **Install Git** (if not already installed):
   - Windows: Download from https://git-scm.com/
   - macOS: `brew install git`
   - Linux: `sudo apt-get install git` (Ubuntu/Debian)

2. **Initialize the repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: BeamMP Server Configurator"
   ```

3. **Create a remote repository** (GitHub, GitLab, etc.):
   - Go to your preferred Git hosting service
   - Create a new repository
   - Follow their instructions to push your local repository

4. **Push to remote**:
   ```bash
   git remote add origin <your-repository-url>
   git branch -M main
   git push -u origin main
   ```

## Troubleshooting

### Common Issues

1. **"Error loading configuration"**
   - Ensure `ServerConfig.toml` exists in the same directory as `app.py`
   - Check file permissions

2. **"Failed to save configuration"**
   - Ensure you have write permissions in the directory
   - Check if the file is being used by another process

3. **Port already in use**
   - Change the port in `app.py` (line 108) or stop other services using port 5000

4. **Git not found**
   - Install Git from https://git-scm.com/
   - Add Git to your system PATH

### File Structure
```
beammp_server_tool/
├── app.py                 # Main Flask application
├── ServerConfig.toml      # Your BeamMP server configuration (not in repo)
├── ServerConfig.example.toml # Example configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── LICENSE               # MIT License
├── .gitignore            # Git ignore rules
├── install_and_run.bat   # Windows installation script
├── run.bat               # Windows run script
├── templates/            # HTML templates
│   ├── index.html        # Main configuration interface
│   └── backups.html      # Backup management interface
└── backups/              # Automatic backup directory (created on first save)
```

## Development

To modify the application:

1. **Add new configuration fields**: Update the HTML form in `templates/index.html`
2. **Modify styling**: Edit the CSS in the `<style>` sections
3. **Add new features**: Extend the Flask routes in `app.py`

## License

This project is open source and available under the MIT License.

## Support

For issues related to:
- **BeamMP Server**: Visit [BeamMP Documentation](https://docs.beammp.com/)
- **This Configurator**: Check the troubleshooting section above or create an issue in the repository 