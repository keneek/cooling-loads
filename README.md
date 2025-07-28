# Cooling Load Estimator

A professional-grade Streamlit web application for estimating HVAC cooling loads based on ASHRAE standards. This tool helps HVAC engineers, contractors, and facility managers quickly calculate cooling requirements for different building types.

## 🌐 Live Application

**Production URL:** [https://loadestimator.com](https://loadestimator.com) ✅ **LIVE**

## ✨ Features

### Core Functionality

- **ASHRAE Standards Compliance**: Calculations based on official ASHRAE "Cooling Load Check Figures"
- **Multiple Building Types**: Support for various building categories (Office, Retail, Hotels, etc.)
- **Load Level Analysis**: Low, Average, and High load scenarios for comprehensive planning
- **Multi-Building Comparison**: Select and compare tonnage ranges across different building types
- **Interactive Visualizations**: Beautiful charts powered by Plotly for data analysis

### User Authentication & Enhanced Project Management ✨ **ENHANCED**

- **User Registration**: Secure sign-up with email verification via AWS Cognito
- **User Authentication**: Sign in/out with session management
- **Complete Project Configuration Saving**: Save full project state including building types, square footage, and range results
- **One-Click Project Loading**: Restore exact project configuration with all inputs and selections
- **Rich Project Previews**: See building type, square footage, tonnage, and creation date at a glance
- **Smart Project Management**: Load, delete with confirmation, and manage all saved projects
- **Session State Integration**: Visual indicators show loaded projects, auto-clear when inputs change
- **Legacy Project Support**: Backward compatibility with existing saved projects
- **Guest Mode**: Full functionality available without registration
- **Smart UX**: Authentication prompts only appear when saving projects

### User Experience

- **Clean Interface**: No authentication clutter on main screen for guest users
- **Sidebar Authentication**: Elegant user management in collapsible sidebar
- **Dark Mode**: Professional dark theme optimized for engineering workflows
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Calculations**: Instant updates as you modify inputs
- **Export Capabilities**: Generate PDF reports for documentation and client presentations

### Technical Features

- **Data Validation**: Robust input validation using Pydantic models
- **Performance Optimized**: Streamlit caching for fast load times
- **Error Handling**: Graceful handling of edge cases and invalid inputs
- **Secure Storage**: User data encrypted and isolated per account

## 🏗️ Architecture

### Application Stack

- **Frontend**: Streamlit (Python web framework)
- **Authentication**: AWS Cognito (user pools, email verification)
- **Database**: Amazon DynamoDB (project storage)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly Express
- **PDF Generation**: FPDF
- **Validation**: Pydantic v2
- **AWS SDK**: Boto3 for AWS service integration

### AWS Infrastructure (Deployed)

- **Compute**: AWS Fargate (serverless containers) ✅
- **Authentication**: AWS Cognito User Pools with email verification ✅
- **Database**: Amazon DynamoDB with per-user project isolation ✅
- **Load Balancing**: Application Load Balancer (ALB) with health checks ✅
- **Networking**: VPC with public/private subnets across 2 AZs ✅
- **Container Registry**: Amazon ECR ✅
- **DNS**: Route53 hosted zone with DNS delegation ✅
- **SSL/TLS**: AWS Certificate Manager with automatic validation ✅
- **Domain**: Custom domain `loadestimator.com` with GoDaddy DNS delegation ✅
- **IAM**: Secure role-based permissions for ECS tasks ✅

## 🚀 Local Development

### Prerequisites

- Python 3.13+
- Poetry (dependency management)
- AWS CLI configured with credentials
- Git

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd cooling-loads
   ```

2. **Install Poetry** (if not already installed)

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**

   ```bash
   poetry install
   ```

4. **Configure AWS credentials**

   ```bash
   # Option 1: AWS SSO (recommended for organizations)
   aws configure sso --profile your-profile-name
   aws sso login --profile your-profile-name
   
   # Option 2: Standard credentials (for personal accounts)
   aws configure --profile your-profile-name
   
   # Option 3: Use default profile
   aws configure
   
   # Set default region and profile (if using named profile)
   export AWS_DEFAULT_REGION=us-east-1
   export AWS_PROFILE=your-profile-name  # Skip if using default
   ```

5. **Set up environment variables**

   Create a `.env` file in the project root with your AWS service configuration:

   ```bash
   # Create .env file with your CDK deployment outputs
   cat > .env << EOF
   COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
   COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
   DYNAMODB_TABLE_NAME=StreamlitStack-CoolingProjectsTable-xxxxx
   AWS_DEFAULT_REGION=us-east-1
   AWS_PROFILE=your-profile-name
   EOF
   ```

   > **Note**: Replace `your-profile-name` with your actual AWS profile name, or omit `AWS_PROFILE` if using the default profile.

   The app will automatically load these variables using `python-dotenv`.

6. **Run the application**

   ```bash
   streamlit run app.py
   ```

The application will be available at `http://localhost:8501`

> **Note**: The `.env` file is automatically loaded by the app and contains sensitive AWS configuration, so it's excluded from git via `.gitignore`.

## 🚢 AWS Deployment

### Prerequisites

- AWS CLI configured with appropriate credentials
- AWS CDK installed (`npm install -g aws-cdk`)
- Docker running locally for container builds

> **Note**: Replace `your-profile-name` in all deployment commands with your actual AWS profile name, or omit `--profile` entirely to use the default profile.

### Initial Deployment

```bash
# Deploy the complete infrastructure
cdk deploy --profile your-profile-name

# Or if using default profile:
cdk deploy
```

This creates:

- **Cognito User Pool** for authentication
- **DynamoDB table** for project storage
- **ECS Fargate service** with updated environment variables
- **IAM roles** with permissions for Cognito and DynamoDB access

### Updating the Application

When you make changes to the code, redeploy with:

```bash
# For code changes (app.py, dependencies, etc.)
cdk deploy --profile your-profile-name

# Or if using default profile:
cdk deploy

# The process will:
# 1. Build a new Docker image with your changes
# 2. Push to ECR
# 3. Update the ECS service with new environment variables
# 4. Replace running containers with new version
# 5. Health checks ensure zero-downtime deployment
```

### Deployment Architecture

- **ECS Fargate**: Serverless container hosting with auto-scaling
- **AWS Cognito**: User authentication with email verification
- **Amazon DynamoDB**: NoSQL database for project storage
- **Application Load Balancer**: High availability, SSL termination, health checks
- **Route53 + Certificate Manager**: Custom domain with automatic SSL
- **Container Health Checks**: Streamlit health endpoint monitoring
- **Multi-AZ**: Deployment across multiple availability zones for resilience
- **DNS Delegation**: GoDaddy domain with Route53 DNS management

### Container Configuration

- **Base Image**: Python 3.13 slim (linux/amd64 for ECS compatibility)
- **Dependencies**: Poetry for package management
- **Port**: 8501 (Streamlit default)
- **Environment Variables**: Cognito User Pool ID, Client ID, DynamoDB table name
- **Health Check**: Built-in Streamlit `/_stcore/health` endpoint
- **Security**: Non-root user, minimal attack surface, IAM role permissions

### DNS Configuration

The domain uses **DNS delegation** from GoDaddy to Route53:

1. **Domain Registration**: Stays with GoDaddy
2. **DNS Management**: Handled by AWS Route53
3. **Nameservers**: Point GoDaddy to Route53 nameservers (from CDK output)
4. **SSL Certificate**: Automatic validation and renewal via AWS Certificate Manager

## 🔧 Configuration

### Environment Variables

**Production (ECS Container):**

- `STREAMLIT_SERVER_PORT`: Server port (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)
- `STREAMLIT_SERVER_HEADLESS`: Headless mode for server deployment (true)
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS`: Disable usage stats (false)
- `COGNITO_USER_POOL_ID`: AWS Cognito User Pool ID
- `COGNITO_CLIENT_ID`: Cognito User Pool Client ID
- `DYNAMODB_TABLE_NAME`: DynamoDB table name for project storage

**Local Development:**

```bash
export COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
export COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
export DYNAMODB_TABLE_NAME=StreamlitStack-CoolingProjectsTable-xxxxx
export AWS_DEFAULT_REGION=us-east-1
export AWS_PROFILE=your-profile-name  # Optional - omit if using default
```

### Streamlit Configuration

The app uses a custom dark theme configured in `.streamlit/config.toml`:

- Dark background with professional color scheme
- Optimized for engineering workflows
- Consistent branding colors

## 👤 User Authentication Flow

### New User Registration

1. User clicks "Sign Up" in sidebar or when trying to save a project
2. Enters username, email, and password
3. AWS Cognito sends verification email
4. User enters verification code to confirm account
5. Account activated and ready to use

### Existing User Sign In

1. User clicks "Sign In" in sidebar
2. Enters username and password
3. AWS Cognito validates credentials
4. User session established with access token
5. Projects loaded automatically in sidebar

### Guest Usage

- Full cooling load calculator access without registration
- Clean interface with no authentication prompts
- Authentication only appears when trying to save projects

## 💾 Enhanced Project Management

### Complete Configuration Saving

- **Full Project State**: Save complete project configuration including selected building types, square footage, current building selection, and all range results (Low/Average/High)
- **Comprehensive Data Storage**: Projects include creation/update timestamps, user preferences, and calculation parameters
- **Smart Session Integration**: Projects capture the exact state of your work session for perfect restoration
- **Secure Storage**: All project data stored with per-user isolation in DynamoDB with AWS Cognito authentication

### One-Click Project Loading

- **Exact State Restoration**: Load button restores complete project configuration in sidebar inputs
- **Smart Input Population**: Automatically selects saved building types, sets square footage, and chooses current building
- **Visual Feedback**: Loaded project indicator shows which project is active with option to clear
- **Seamless Workflow**: Continue working exactly where you left off with all settings intact

### Rich Project Management Interface

- **Enhanced Project Previews**: Each saved project displays:
  - 📅 Creation date for easy identification
  - 🏢 Building type and square footage 
  - ⚡ Key results (tonnage) for quick reference
  - 🏷️ Clear indicators for legacy vs. new format projects
- **Intuitive Actions**:
  - **📂 Load**: One-click restoration of complete project configuration
  - **🗑️ Delete**: Reliable deletion with explicit Yes/No confirmation system
- **Smart State Management**: 
  - Visual indicators show currently loaded project
  - Auto-clear loaded state when inputs are manually modified
  - Session persistence across browser refreshes

### Legacy Project Support

- **Backward Compatibility**: Existing projects saved before this update continue to work
- **Clear Indicators**: Legacy projects marked with "Legacy Format" for easy identification  
- **Graceful Handling**: Legacy projects display available data (tonnage, occupancy, electrical) but cannot be loaded due to missing configuration data
- **Migration Path**: Re-save legacy project data as new projects to gain full configuration loading capabilities

## 📊 Data Sources

The application uses ASHRAE cooling load check figures stored in `ashrae_data.csv`:

- **Building Types**: Various commercial and institutional building categories
- **Load Levels**: Low, Average, High scenarios for each building type
- **Parameters**: Refrigeration, Occupancy, Electrical loads per building type

## 📁 Project Structure

```text
cooling-loads/
├── app.py                  # Main Streamlit application with authentication
├── ashrae_data.csv        # ASHRAE cooling load data
├── pyproject.toml         # Poetry dependencies (includes boto3, python-dotenv)
├── poetry.lock           # Locked dependency versions
├── .env                  # Environment variables (not in git, create locally)
├── Dockerfile            # Container configuration (linux/amd64)
├── .dockerignore         # Docker build exclusions
├── cdk_app.py           # AWS CDK infrastructure (Cognito + DynamoDB)
├── cdk.json             # CDK configuration
├── .cursorrules         # AWS MCP tools documentation
├── .streamlit/
│   └── config.toml      # Streamlit theme configuration
└── README.md            # This file
```

## 🧪 Data Models

### BuildingData (Pydantic Model)

- Validates ASHRAE data from CSV
- Handles missing values gracefully
- Ensures data integrity for calculations

### DesignParams, Results & RangeResults

- **DesignParams**: Structured calculation parameters (refrigeration, occupancy, electrical rates)
- **Results**: Type-safe result objects for individual load levels
- **RangeResults**: Comprehensive model containing Low, Average, and High results
- **Validation**: Engineering calculations with proper error handling

### Project Configuration Models

- **ProjectConfig**: Complete project state model including:
  - Selected building types and current selection
  - Square footage and calculation parameters
  - Full range results (Low/Avg/High) with timestamps
  - Creation and update tracking for project history

### Authentication Models

- User session management with AWS Cognito tokens
- Project data validation before DynamoDB storage
- Secure user data isolation and access control
- Enhanced project configuration validation with backward compatibility

## 🔒 Security Features

- **Input Validation**: All user inputs validated using Pydantic
- **Authentication**: AWS Cognito with secure password policies
- **Data Isolation**: Per-user project storage with DynamoDB partition keys
- **Session Management**: Secure token-based authentication
- **Email Verification**: Required for account activation
- **Error Handling**: Graceful degradation for invalid data or auth failures
- **Container Security**: Minimal attack surface with slim base image
- **Network Security**: Private subnets for compute resources
- **IAM Permissions**: Least-privilege access for ECS tasks
- **SSL/TLS**: End-to-end encryption with AWS Certificate Manager
- **Health Monitoring**: Continuous container health checks

## 🚀 Performance

- **Caching**: Streamlit `@st.cache_data` for expensive calculations
- **Lazy Loading**: Data loaded only when needed
- **Optimized Queries**: Efficient DynamoDB queries with proper key design
- **Session State**: Efficient user state management
- **Auto-scaling**: ECS Fargate scales based on demand
- **CDN Ready**: Static assets can be served via CloudFront (future enhancement)

## 🛠️ Development Workflow

1. **Local Development**: Use Poetry and `.env` file for rapid iteration
2. **Code Changes**: Edit `app.py`, authentication flows, or CDK infrastructure
3. **Testing**: Test locally with `streamlit run app.py` (includes AWS services)
4. **Authentication Testing**: Test sign-up, sign-in, and project management flows
5. **Deployment**: Run `cdk deploy --profile your-profile-name` (or `cdk deploy` for default profile)
6. **Monitoring**: Check ECS console, Cognito console, and DynamoDB for service health
7. **Version Control**: Git with proper `.gitignore` for build artifacts and secrets

## 🔄 Update Process

### For Application Code Changes

```bash
# After modifying app.py, dependencies, or data files
cdk deploy --profile your-profile-name

# Or if using default profile:
cdk deploy

# This will:
# - Build new Docker image with updated dependencies
# - Push to ECR
# - Update ECS service with new environment variables
# - Zero-downtime deployment
```

### For Infrastructure Changes

```bash
# After modifying cdk_app.py (Cognito, DynamoDB, IAM changes)
cdk deploy --profile your-profile-name

# Or if using default profile:
cdk deploy

# This will:
# - Update CloudFormation stack
# - Apply authentication and database changes
# - Update IAM permissions
# - May require brief downtime for some changes
```

### DNS Updates (if needed)

If Route53 nameservers change, update GoDaddy:

1. Get nameservers from CDK deployment output
2. Update GoDaddy DNS settings
3. Wait 15-60 minutes for propagation

## 📈 Monitoring & Troubleshooting

### Health Checks

- **ECS Console**: Monitor task status and health
- **CloudWatch**: Container logs and metrics
- **Load Balancer**: Target group health status
- **Cognito Console**: User pool metrics and authentication logs
- **DynamoDB Console**: Table metrics and performance

### Common Issues

- **503 Service Unavailable**: Containers not healthy, check ECS logs
- **Authentication Failures**: Check Cognito configuration and IAM permissions
- **Project Save Errors**: Verify DynamoDB table permissions and connectivity
- **DNS Resolution**: Verify GoDaddy nameserver configuration
- **SSL Certificate**: Check Certificate Manager validation status
- **Environment Variables**: Verify all required AWS configuration is set

### AWS Service Dependencies

- **Cognito**: Required for user authentication
- **DynamoDB**: Required for project storage
- **IAM**: Required for service permissions

## 📈 Future Enhancements

- [x] Custom domain setup with SSL (loadestimator.com) ✅ **COMPLETED**
- [x] User authentication and project saving ✅ **COMPLETED**
- [x] AWS Cognito integration with email verification ✅ **COMPLETED**
- [x] DynamoDB project storage with user isolation ✅ **COMPLETED**
- [x] Enhanced project management with full configuration saving ✅ **COMPLETED**
- [x] Mobile-responsive design and UX improvements ✅ **COMPLETED**
- [x] Load range display (Low/Average/High simultaneously) ✅ **COMPLETED**
- [x] Rich project previews and reliable delete functionality ✅ **COMPLETED**
- [ ] Additional ASHRAE standards and calculations
- [ ] API endpoints for programmatic access
- [ ] Advanced reporting and analytics
- [ ] Project sharing and collaboration features
- [ ] Integration with CAD/BIM software
- [ ] CloudFront CDN for improved performance
- [ ] Multi-factor authentication (MFA)
- [ ] Social sign-in integration (Google, Microsoft)
- [ ] Project export/import functionality
- [ ] Advanced project filtering and search
- [ ] Project templates and presets
- [ ] Project history and version tracking
- [ ] Save and manage PDF reports for each project
- [ ] Project collaboration and sharing features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `streamlit run app.py` (ensure AWS services work with your `.env` file)
5. Test authentication flows (sign-up, sign-in, project management)
6. Deploy to test environment
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For technical support or feature requests, please open an issue in the GitHub repository.

---

**Built with ❤️ for the HVAC engineering community**  
**Live at [https://loadestimator.com](https://loadestimator.com)** 🌐  
**✨ Now with enhanced project management and mobile-responsive design!**
