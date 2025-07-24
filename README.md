# ASHRAE Cooling Load Estimator

A professional-grade Streamlit web application for estimating HVAC cooling loads based on ASHRAE standards. This tool helps HVAC engineers, contractors, and facility managers quickly calculate cooling requirements for different building types.

## 🌐 Live Application

**Production URL:** [https://loadestimate.com](https://loadestimate.com) *(coming soon)*

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

### AWS Infrastructure

- **Compute**: AWS Fargate (serverless containers)
- **Load Balancing**: Application Load Balancer (ALB)
- **Networking**: VPC with public/private subnets across 2 AZs
- **Container Registry**: Amazon ECR
- **DNS**: Route53 (planned)
- **SSL/TLS**: AWS Certificate Manager (planned)

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

## 🔧 Configuration

### Environment Variables

- `STREAMLIT_SERVER_PORT`: Server port (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)

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

## 🚢 AWS Deployment

### Infrastructure as Code

The application is deployed using AWS CDK (Cloud Development Kit):

```bash
# Bootstrap CDK (one-time setup)
cdk bootstrap aws://ACCOUNT-ID/REGION --profile Production

# Deploy the application
cdk deploy --require-approval never
```

### Deployment Architecture

- **ECS Fargate**: Serverless container hosting
- **Application Load Balancer**: High availability and SSL termination
- **Auto Scaling**: Automatic scaling based on demand
- **Multi-AZ**: Deployment across multiple availability zones for resilience

### Container Configuration

- **Base Image**: Python 3.13 slim
- **Dependencies**: Poetry for package management
- **Port**: 8501 (Streamlit default)
- **Health Checks**: Built-in Streamlit health monitoring

## 📁 Project Structure

```
cooling-loads/
├── app.py                  # Main Streamlit application
├── ashrae_data.csv        # ASHRAE cooling load data
├── pyproject.toml         # Poetry dependencies and project config
├── poetry.lock           # Locked dependency versions
├── Dockerfile            # Container configuration
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

## 🚀 Performance

- **Caching**: Streamlit `@st.cache_data` for expensive calculations
- **Lazy Loading**: Data loaded only when needed
- **Optimized Queries**: Efficient data filtering and processing
- **CDN Ready**: Static assets can be served via CloudFront (future enhancement)

## 🛠️ Development Workflow

1. **Local Development**: Use Poetry and Streamlit for rapid iteration
2. **Version Control**: Git with proper `.gitignore` for build artifacts
3. **Containerization**: Docker for consistent deployment environments
4. **Infrastructure**: CDK for reproducible AWS deployments
5. **Monitoring**: CloudWatch logs and metrics (built-in)

## 📈 Future Enhancements

- [ ] Custom domain setup with SSL (loadestimate.com)
- [ ] User authentication and project saving
- [ ] Additional ASHRAE standards and calculations
- [ ] API endpoints for programmatic access
- [ ] Advanced reporting and analytics
- [ ] Integration with CAD/BIM software

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For technical support or feature requests, please open an issue in the GitHub repository.

---

**Built with ❤️ for the HVAC engineering community**
