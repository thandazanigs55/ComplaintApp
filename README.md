# DUT Student Grievance Management System

A web-based application for handling student complaints at Durban University of Technology (DUT) in a transparent and timely manner.

## Features

- **Student Portal**: Students can register, login, file complaints, track progress, and receive notifications.
- **Admin Dashboard**: Administrators can filter complaints by department, update status, and manage the grievance process.
- **Automated Notifications**: Email notifications are sent at every stage of the complaint process.
- **Document Upload**: Students can upload supporting documents or evidence related to their complaints.
- **Status Tracking**: Real-time progress tracking for all grievances.
- **Reporting**: Comprehensive reports and statistics for administrators.

## Technology Stack

- **Backend**: Python with Flask framework
- **Database**: Firebase Firestore
- **Authentication**: Firebase Authentication
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Email**: SMTP for email notifications

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/thandazanigs55/dut-grievance-system.git
   cd dut-grievance-system
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up Firebase:
   - Create a Firebase project at [firebase.google.com](https://firebase.google.com)
   - Enable Authentication (Email/Password) and Firestore Database
   - Download your service account key and save it as `service_account.json` in the project root
   - Create a `.env` file with your Firebase Web API Key:
     ```
     Web_API_Key=your-api-key
     ```

5. Run the application:
   ```
   python run.py
   ```

6. Access the application at `http://localhost:5000`

## Usage

### For Students

1. Register with your DUT email address
2. Login to the system
3. Submit a new grievance with details and supporting documents
4. Track the status of your grievances
5. Receive email notifications about status updates

### For Administrators

1. Login with admin credentials
2. View all grievances or filter by department/status
3. Update grievance status and add notes
4. View reports and statistics
5. Manage the grievance process

## Project Structure

```
dut-grievance-system/
├── app/
│   ├── models/
│   │   ├── firebase_utils.py
│   │   └── email_utils.py
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── student_routes.py
│   │   └── admin_routes.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   ├── templates/
│   │   ├── admin/
│   │   ├── auth/
│   │   ├── student/
│   │   └── shared/
│   └── __init__.py
├── service_account.json
├── .env
├── requirements.txt
├── run.py
└── README.md
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Durban University of Technology
- Firebase for authentication and database services
- Bootstrap for the UI framework 