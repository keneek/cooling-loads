# ASHRAE Cooling Load Estimator

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

### User Experience

- **Dark Mode**: Professional dark theme optimized for engineering workflows
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Calculations**: Instant updates as you modify inputs
- **Export Capabilities**: Generate PDF reports for documentation and client presentations

### Technical Features

- **Data Validation**: Robust input validation using Pydantic models
- **Performance Optimized**: Streamlit caching for fast load times
- **Error Handling**: Graceful handling of edge cases and invalid inputs

## 🏗️ Architecture

### Application Stack

- **Frontend**: Streamlit (Python web framework)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly Express
- **PDF Generation**: FPDF
- **Validation**: Pydantic v2

### AWS Infrastructure (Deployed)

- **Compute**: AWS Fargate (serverless containers) ✅
- **Load Balancing**: Application Load Balancer (ALB) with health checks ✅
- **Networking**: VPC with public/private subnets across 2 AZs ✅
- **Container Registry**: Amazon ECR ✅
- **DNS**: Route53 hosted zone with DNS delegation ✅
- **SSL/TLS**: AWS Certificate Manager with automatic validation ✅
- **Domain**: Custom domain `loadestimator.com` with GoDaddy DNS delegation ✅

## 🚀 Local Development

### Prerequisites

- Python 3.13+
- Poetry (dependency management)
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

4. **Activate the environment**

   ```bash
   poetry shell
   ```

5. **Run the application**

   ```bash
   streamlit run app.py
   ```

The application will be available at `http://localhost:8501`

## 🚢 AWS Deployment

### Prerequisites

- AWS CLI configured with appropriate credentials
- AWS CDK installed (`npm install -g aws-cdk`)
- Docker running locally for container builds

### Initial Deployment

```bash
# Deploy the application
cdk deploy --profile prodAdmin
```

### Updating the Application

When you make changes to the code, redeploy with:

```bash
# For code changes (app.py, dependencies, etc.)
cdk deploy --profile prodAdmin

# The process will:
# 1. Build a new Docker image with your changes
# 2. Push to ECR
# 3. Update the ECS service
# 4. Replace running containers with new version
# 5. Health checks ensure zero-downtime deployment
```

### Deployment Architecture

- **ECS Fargate**: Serverless container hosting with auto-scaling
- **Application Load Balancer**: High availability, SSL termination, health checks
- **Route53 + Certificate Manager**: Custom domain with automatic SSL
- **Container Health Checks**: Streamlit health endpoint monitoring
- **Multi-AZ**: Deployment across multiple availability zones for resilience
- **DNS Delegation**: GoDaddy domain with Route53 DNS management

### Container Configuration

- **Base Image**: Python 3.13 slim (linux/amd64 for ECS compatibility)
- **Dependencies**: Poetry for package management
- **Port**: 8501 (Streamlit default)
- **Health Check**: Built-in Streamlit `/_stcore/health` endpoint
- **Security**: Non-root user, minimal attack surface

### DNS Configuration

The domain uses **DNS delegation** from GoDaddy to Route53:

1. **Domain Registration**: Stays with GoDaddy
2. **DNS Management**: Handled by AWS Route53
3. **Nameservers**: Point GoDaddy to Route53 nameservers (from CDK output)
4. **SSL Certificate**: Automatic validation and renewal via AWS Certificate Manager

## 🔧 Configuration

### Environment Variables

- `STREAMLIT_SERVER_PORT`: Server port (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)
- `STREAMLIT_SERVER_HEADLESS`: Headless mode for server deployment (true)
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS`: Disable usage stats (false)

### Streamlit Configuration

The app uses a custom dark theme configured in `.streamlit/config.toml`:

- Dark background with professional color scheme
- Optimized for engineering workflows
- Consistent branding colors

## 📊 Data Sources

The application uses ASHRAE cooling load check figures stored in `ashrae_data.csv`:

- **Building Types**: Various commercial and institutional building categories
- **Load Levels**: Low, Average, High scenarios for each building type
- **Parameters**: Refrigeration, Occupancy, Electrical loads per building type

## 📁 Project Structure

```
cooling-loads/
├── app.py                  # Main Streamlit application
├── ashrae_data.csv        # ASHRAE cooling load data
├── pyproject.toml         # Poetry dependencies and project config
├── poetry.lock           # Locked dependency versions
├── Dockerfile            # Container configuration (linux/amd64)
├── .dockerignore         # Docker build exclusions
├── cdk_app.py           # AWS CDK infrastructure code
├── cdk.json             # CDK configuration
├── .streamlit/
│   └── config.toml      # Streamlit theme configuration
└── README.md            # This file
```

## 🧪 Data Models

### BuildingData (Pydantic Model)

- Validates ASHRAE data from CSV
- Handles missing values gracefully
- Ensures data integrity for calculations

### DesignParams & Results

- Structured calculation parameters
- Type-safe result objects
- Validation for engineering calculations

## 🔒 Security Features

- **Input Validation**: All user inputs validated using Pydantic
- **Error Handling**: Graceful degradation for invalid data
- **Container Security**: Minimal attack surface with slim base image
- **Network Security**: Private subnets for compute resources
- **SSL/TLS**: End-to-end encryption with AWS Certificate Manager
- **Health Monitoring**: Continuous container health checks

## 🚀 Performance

- **Caching**: Streamlit `@st.cache_data` for expensive calculations
- **Lazy Loading**: Data loaded only when needed
- **Optimized Queries**: Efficient data filtering and processing
- **Auto-scaling**: ECS Fargate scales based on demand
- **CDN Ready**: Static assets can be served via CloudFront (future enhancement)

## 🛠️ Development Workflow

1. **Local Development**: Use Poetry and Streamlit for rapid iteration
2. **Code Changes**: Edit `app.py`, `pyproject.toml`, or related files
3. **Testing**: Test locally with `streamlit run app.py`
4. **Deployment**: Run `cdk deploy --profile prodAdmin`
5. **Monitoring**: Check ECS console for container health
6. **Version Control**: Git with proper `.gitignore` for build artifacts

## 🔄 Update Process

### For Application Code Changes

```bash
# After modifying app.py, dependencies, or data files
cdk deploy --profile prodAdmin

# This will:
# - Build new Docker image
# - Push to ECR
# - Update ECS service
# - Zero-downtime deployment
```

### For Infrastructure Changes

```bash
# After modifying cdk_app.py
cdk deploy --profile prodAdmin

# This will:
# - Update CloudFormation stack
# - Apply infrastructure changes
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

### Common Issues
- **503 Service Unavailable**: Containers not healthy, check ECS logs
- **DNS Resolution**: Verify GoDaddy nameserver configuration
- **SSL Certificate**: Check Certificate Manager validation status

## 📈 Future Enhancements

- [x] Custom domain setup with SSL (loadestimator.com) ✅
- [ ] User authentication and project saving
- [ ] Additional ASHRAE standards and calculations
- [ ] API endpoints for programmatic access
- [ ] Advanced reporting and analytics
- [ ] Integration with CAD/BIM software
- [ ] CloudFront CDN for improved performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `streamlit run app.py`
5. Deploy to test environment
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For technical support or feature requests, please open an issue in the GitHub repository.

---

**Built with ❤️ for the HVAC engineering community**  
**Live at [https://loadestimator.com](https://loadestimator.com)** 🌐
