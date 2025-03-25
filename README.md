# DUT Student Grievance Management System

A comprehensive web-based application designed to efficiently handle student complaints at Durban University of Technology (DUT). The system ensures transparent, timely management of grievances, allowing students to voice their concerns and track their resolution in real-time.

## Features

### **For Students**
- **Register & Login**: Students can register using their DUT email address and securely log into the portal.
- **File Complaints**: Students can submit grievances with detailed descriptions and attach supporting documents.
- **Track Progress**: Real-time tracking of complaint statuses with the ability to monitor resolution steps.
- **Document Upload**: Students can upload relevant documents as evidence to support their grievances.
  
### **For Administrators**
- **Admin Dashboard**: A centralized dashboard where administrators can view and manage complaints, filter them by department or status, and oversee the grievance process.
- **Update Status**: Admins can update the grievance status (e.g., resolved, in-progress) and add comments or notes to each grievance.
- **Reporting**: Generate comprehensive reports and statistics on grievances for analysis and decision-making.

## Technology Stack

- **Backend**: Python with the Flask framework
- **Database**: Firebase Firestore for storing student complaints and data
- **Authentication**: Firebase Authentication for secure login and user management
- **Frontend**: HTML, CSS, JavaScript, and Bootstrap 5 for responsive design
- **Hosting**: Azure for cloud hosting

## Deployment

The application is deployed and can be accessed online via the following link:
- [DUT Grievance Management System](https://grievanceapp.azurewebsites.net/)

## Installation

To set up the project locally:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/thandazanigs55/dut-grievance-system.git
   cd dut-grievance-system
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Firebase**:
   - Create a Firebase project at [firebase.google.com](https://firebase.google.com)
   - Enable Authentication (Email/Password) and Firestore Database
   - Download your service account key and save it as `service_account.json` in the project root
   - Create a `.env` file with the Firebase Web API Key:
     ```bash
     Web_API_Key=your-api-key
     ```

5. **Run the application locally**:
   ```bash
   python run.py
   ```

6. **Access the application**:
   Open a web browser and go to [http://localhost:5000](http://localhost:5000) to use the system locally.

## Usage

### **For Students**:

1. **Registration**: Register using your DUT email address.
2. **Login**: Login to the system using the credentials you registered with.
3. **File Complaints**: Submit grievances by entering complaint details and uploading any relevant documents.
4. **Track Complaint Status**: Monitor the status of your complaints in real-time.

### **For Administrators**:

1. **Login**: Access the admin dashboard with the provided admin credentials.
2. **Manage Complaints**: View all submitted complaints, filter them by department, or search by status.
3. **Update Status**: Change the status of complaints (e.g., resolved, pending) and add notes for tracking purposes.
4. **Reporting**: Generate and view detailed reports regarding grievances and their resolution progress.

## Project Structure

The project structure is organized as follows:

```
dut-grievance-system/
├── app/
│   ├── models/
│   │   ├── firebase_utils.py      # Firebase utility functions
│   │   └── email_utils.py         # Email notification functions
│   ├── routes/
│   │   ├── auth_routes.py         # Routes for authentication
│   │   ├── student_routes.py      # Routes for student-related actions
│   │   └── admin_routes.py        # Routes for admin-related actions
│   ├── static/
│   │   ├── css/                   # CSS files for styling
│   │   ├── js/                    # JavaScript files for client-side interactions
│   │   └── img/                   # Image files (logos, etc.)
│   ├── templates/
│   │   ├── admin/                 # Admin dashboard templates
│   │   ├── auth/                  # Authentication templates (login, register)
│   │   ├── student/               # Student interface templates (grievance submission, status tracking)
│   │   └── shared/                # Shared templates (e.g., header, footer)
│   └── __init__.py                # Flask app initialization
├── service_account.json           # Firebase service account credentials
├── .env                           # Environment variables (Firebase API key)
├── requirements.txt               # List of Python dependencies
├── run.py                         # Main application entry point
└── README.md                      # Project documentation
```

## Hosting on Azure

This application is hosted on Azure. You can access the deployed version of the DUT Student Grievance Management System here:

- [DUT Grievance Management System on Azure](https://grievanceapp.azurewebsites.net/)

The Azure deployment ensures that the application is available globally, with high reliability and performance.

This updated README provides a more detailed explanation of the Platform Based Development Module project, setup instructions, and deployment details, helping users understand both the installation and usage of the system.
