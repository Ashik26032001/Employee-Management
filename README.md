# Employee Management System

A comprehensive Employee Management System built with Django REST Framework, featuring dynamic form creation, JWT authentication, and a modern responsive frontend.

## Features

### Authentication & Profile
- ✅ User Registration and Login
- ✅ JWT Access and Refresh Tokens
- ✅ Password Change Functionality
- ✅ User Profile Management
- ✅ Profile Picture Upload

### Employee Management
- ✅ Dynamic Form Builder with Drag & Drop
- ✅ Customizable Field Types (Text, Number, Date, Password, Select, File, etc.)
- ✅ Employee Creation and Update
- ✅ Advanced Search and Filtering
- ✅ Employee Listing with Pagination
- ✅ Employee Deletion with Audit Trail

### API Development
- ✅ REST API with Django REST Framework
- ✅ JWT Authentication
- ✅ Comprehensive CRUD Operations
- ✅ Dynamic Form Creation API
- ✅ Audit Logging
- ✅ File Upload Support

### Frontend
- ✅ Responsive Bootstrap UI
- ✅ AJAX/Axios Integration
- ✅ Drag & Drop Form Builder
- ✅ Real-time Form Validation
- ✅ Modern Dashboard with Statistics

## Technology Stack

- **Backend**: Python (Django 5.2.6)
- **API**: Django REST Framework
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite (default), PostgreSQL (production ready)
- **File Storage**: Local storage (configurable for cloud storage)

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- virtualenv (recommended)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd EmployeeManagementSystem/EmployeeManagement
```

### 2. Create Virtual Environment
```bash
python -m venv env
# Windows
env\Scripts\activate
# Linux/Mac
source env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
python manage.py runserver
```

The application will be available at:
- Frontend: http://localhost:8000/
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

## API Documentation

### Authentication Endpoints
- `POST /api/auth/register/` - User Registration
- `POST /api/auth/login/` - User Login
- `POST /api/auth/refresh/` - Refresh Token
- `POST /api/auth/change-password/` - Change Password
- `GET /api/auth/profile/` - Get Profile
- `PUT /api/auth/profile/` - Update Profile

### Form Template Endpoints
- `GET /api/form-templates/` - List Form Templates
- `POST /api/form-templates/` - Create Form Template
- `GET /api/form-templates/{id}/` - Get Form Template Details
- `PUT /api/form-templates/{id}/` - Update Form Template
- `DELETE /api/form-templates/{id}/` - Delete Form Template
- `GET /api/form-templates/{id}/fields/` - Get Form Fields
- `POST /api/form-templates/{id}/add_field/` - Add Field to Template
- `PUT /api/form-templates/{id}/reorder_fields/` - Reorder Fields

### Employee Endpoints
- `GET /api/employees/` - List Employees
- `POST /api/employees/` - Create Employee
- `GET /api/employees/{id}/` - Get Employee Details
- `PUT /api/employees/{id}/` - Update Employee
- `DELETE /api/employees/{id}/` - Delete Employee
- `GET /api/employees/search/` - Advanced Search

### Audit Log Endpoints
- `GET /api/audit-logs/` - List Audit Logs
- `GET /api/audit-logs/{id}/` - Get Audit Log Details

### Dashboard Endpoints
- `GET /api/dashboard/stats/` - Get Dashboard Statistics
- `GET /api/dashboard/settings/` - Get Dashboard Settings
- `PUT /api/dashboard/settings/` - Update Dashboard Settings
- `POST /api/dashboard/upload/` - File Upload

## Postman Collection

A comprehensive Postman collection is provided: `Employee_Management_System_API.postman_collection.json`

### Import Instructions:
1. Open Postman
2. Click "Import"
3. Select the JSON file
4. The collection will be imported with all endpoints and example requests

### Environment Variables:
Set up the following variables in Postman:
- `base_url`: http://localhost:8000/api
- `access_token`: (will be set automatically after login)
- `refresh_token`: (will be set automatically after login)
- `form_template_id`: (will be set after creating a form template)
- `employee_id`: (will be set after creating an employee)

## Usage Guide

### 1. User Registration & Login
- Visit http://localhost:8000/login/
- Click "Register here" to create a new account
- Or login with existing credentials

### 2. Create Form Templates
- Navigate to "Form Builder"
- Click "Add Field" to add form fields
- Choose field types: Text, Number, Date, Select, File Upload, etc.
- Configure field properties (required, placeholder, help text)
- Save the form template

### 3. Create Employees
- Navigate to "Employees" → "Create Employee"
- Select a form template
- Fill in the dynamic form fields
- Save the employee

### 4. Manage Employees
- View, edit, or delete employees
- Use search and filter options
- Export employee data (future feature)

### 5. View Audit Logs
- Navigate to "Audit Logs"
- View all system activities
- Filter by action type, employee, or date range

## Field Types Supported

- **Text**: Single line text input
- **Number**: Numeric input with validation
- **Email**: Email input with validation
- **Date**: Date picker
- **Password**: Password input (masked)
- **Text Area**: Multi-line text input
- **Select**: Dropdown selection
- **Checkbox**: Boolean checkbox
- **Radio**: Radio button selection
- **File Upload**: File upload with validation

## API Authentication

The API uses JWT (JSON Web Token) authentication:

1. **Login** to get access and refresh tokens
2. **Include** the access token in the Authorization header:
   ```
   Authorization: Bearer <access_token>
   ```
3. **Refresh** the access token using the refresh token when it expires

## File Structure

```
EmployeeManagement/
├── EmployeeManagement/
│   ├── settings.py          # Django settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py
├── api/
│   ├── models.py           # Database models
│   ├── serializers.py      # API serializers
│   ├── views.py            # API views
│   ├── views_forms.py      # Form-specific views
│   ├── views_employees.py  # Employee-specific views
│   ├── views_dashboard.py  # Dashboard views
│   ├── urls.py             # API URLs
│   └── admin.py            # Admin configuration
├── dashboard/
│   ├── views.py            # Frontend views
│   ├── urls.py             # Frontend URLs
│   ├── models.py           # Dashboard models
│   └── templates/
│       └── dashboard/      # HTML templates
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
└── README.md              # This file
```

## Customization

### Adding New Field Types
1. Update `FIELD_TYPES` in `api/models.py`
2. Add field rendering logic in frontend templates
3. Update validation in serializers

### Styling
- Modify CSS in `base.html` template
- Bootstrap 5 is used for responsive design
- Custom CSS classes are defined for consistent styling

### Database
- Default: SQLite (development)
- Production: Update `DATABASES` in `settings.py` for PostgreSQL/MySQL

## Security Features

- JWT token-based authentication
- CSRF protection
- Password validation
- Audit logging for all operations
- File upload validation
- Input sanitization

## Future Enhancements

- [ ] Email notifications
- [ ] Advanced reporting
- [ ] Data export (Excel, PDF)
- [ ] Role-based permissions
- [ ] API rate limiting
- [ ] Docker containerization
- [ ] Cloud storage integration
- [ ] Mobile app support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please create an issue in the repository or contact the development team.

