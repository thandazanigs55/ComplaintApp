# Database Cleaning Script

This script helps manage the development and testing environment for the DUT Student Grievance Management System by cleaning the Firebase database while preserving specific users.

## Features

- **Clean Grievances**: Removes all grievance records from the database
- **Preserve Specific Users**: Keeps admin, student, and manager users while removing all other users
- **Clean Storage**: Removes all attachment files from Firebase Storage
- **Reset Departments**: Option to reset departments to default values

## Prerequisites

- Python 3.6+
- Firebase Admin SDK
- Pyrebase
- Valid `service_account.json` file in the project root directory
- Environment variables (Web_API_Key, etc.) in `.env` file

## Installation

1. Make sure you're in the project root directory
2. Install the required dependencies:

```bash
pip install firebase-admin pyrebase4 python-dotenv
```

## Usage

```bash
python clean_db.py [options]
```

### Options

- `--force`: Skip confirmation prompt
- `--skip-storage`: Skip cleaning Storage files
- `--reset-departments`: Reset departments to default values

### Examples

**Clean everything with confirmation prompt:**
```bash
python clean_db.py
```

**Clean everything without confirmation prompt:**
```bash
python clean_db.py --force
```

**Clean grievances and users, but skip storage cleaning:**
```bash
python clean_db.py --skip-storage
```

**Clean everything and reset departments:**
```bash
python clean_db.py --reset-departments
```

## Default Preserved Users

The script preserves the following users by default:

- Admin: `admin@dut.ac.za`
- Student: `student@dut4life.ac.za`
- Manager: `manager@dut.ac.za`

To change which users are preserved, modify the `PRESERVE_USERS` list in the script.

## Caution

This script deletes data from your Firebase database. Always make sure you:

1. Use it only in development/testing environments
2. Have a backup of any important data
3. Understand which data will be deleted

## Troubleshooting

- **Firebase Authentication errors**: Make sure your `service_account.json` file is valid and has the correct permissions
- **Storage errors**: Check that your Firebase Storage is properly configured and accessible
- **Permission errors**: Ensure your service account has read/write permissions for all resources 