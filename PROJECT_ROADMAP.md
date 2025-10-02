# Optimal Build - Project Roadmap & Architecture

## Data Models (The "Tree")
Created and integrated in `/backend/app/models/`:

1. **users.py** - User authentication and profile
   - Singapore-specific fields (UEN number, etc.)

2. **projects.py** - Development project tracking
   - Budget, location, status, timelines

3. **singapore_property.py** - Property regulatory data
   - GFA, plot ratio, zoning, BCA/URA compliance

4. **ai_agents.py** - AI assistant configurations
   - Agent profiles, capabilities, sessions

## Feature Development Roadmap

### Phase 1: Core Foundation ✅ (COMPLETED)
- User authentication (JWT)
- User registration/login
- Database setup (SQLite)
- Basic frontend interface
- Projects CRUD API

### Phase 2: Project Management UI (NEXT)
- Project Dashboard
- Project Creation Form
- Project Details View
- Search and filtering

### Phase 3: Singapore Property Integration
- Property Data Model
- Compliance Checking (BCA/URA)
- Property Dashboard
- GPS location features (property site visits, location tagging)
- Plot ratio and GFA calculations

### Phase 4: AI Agent Integration
- AI Configuration
- Automated compliance analysis
- Cost estimation AI
- Risk assessment
- Development potential analysis
- AI Chat Interface

### Phase 5: Advanced Analytics
- Financial Dashboard
- Timeline Management
- Reports Generation
- ROI calculations

### Phase 6: Collaboration Features
- Team Management
- Document Management
- Comments & Notes
- Activity logs

### Phase 7: External Integrations
- Government APIs (BCA, URA, OneMap)
- Financial Systems
- Export/Import (Excel, AutoCAD, BIM)

### Phase 8: Mobile & Optimization
- Mobile App
- Performance optimization
- Security hardening
- PostgreSQL migration

## Technical Stack
- **Frontend**: HTML/CSS/JavaScript (current), React (future)
- **Backend**: FastAPI (Python)
- **Database**: SQLite (dev), PostgreSQL (production)
- **Authentication**: JWT tokens
- **AI**: Local AI agents (future: GPT integration)

## Current Status
- ✅ Authentication working
- ✅ User management complete
- ✅ Projects API ready
- ✅ Frontend login/signup working
- 🔄 Next: Project Management UI

## Important Files
- `/backend/app/models/` - All data models
- `/backend/app/api/v1/` - API endpoints
- `/frontend/simple-auth/` - Current frontend
- `/users.db` - User database
- `/projects.db` - Projects database

## Development Notes
- Using SQLite for development (simple, no installation)
- CORS configured for localhost:8080
- Security headers temporarily disabled for development
- JWT tokens stored in localStorage

Last Updated: 2025-09-29