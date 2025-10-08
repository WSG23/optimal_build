# Optimal Build - Complete Data Models Tree Structure

## 📊 Database Architecture Overview

```
optimal_build_database/
│
├── users/                    [User Authentication & Management]
│   ├── id (UUID, Primary Key)
│   ├── email (String, Unique, Required)
│   ├── username (String, Unique, Required)
│   ├── hashed_password (String, Required)
│   ├── full_name (String, Required)
│   ├── company_name (String, Optional)
│   ├── uen_number (String, Optional) - Singapore company identifier
│   ├── phone_number (String, Optional)
│   ├── role (Enum: admin/user/developer/consultant)
│   ├── is_active (Boolean, Default: true)
│   ├── is_verified (Boolean, Default: false)
│   ├── last_login (DateTime, Optional)
│   ├── created_at (DateTime, Required)
│   └── updated_at (DateTime, Required)
│
├── projects/                  [Development Projects]
│   ├── id (UUID, Primary Key)
│   ├── name (String, Required)
│   ├── description (Text, Optional)
│   ├── project_type (Enum: residential/commercial/industrial/mixed)
│   ├── status (Enum: planning/approval/construction/completed)
│   ├── location (String, Optional)
│   ├── latitude (Float, Optional) - GPS coordinates
│   ├── longitude (Float, Optional) - GPS coordinates
│   ├── budget (Float, Optional)
│   ├── estimated_cost (Float, Optional)
│   ├── actual_cost (Float, Optional)
│   ├── start_date (Date, Optional)
│   ├── completion_date (Date, Optional)
│   ├── owner_id (UUID, Foreign Key → users.id)
│   ├── created_at (DateTime, Required)
│   ├── updated_at (DateTime, Required)
│   └── is_active (Boolean, Default: true)
│
├── singapore_property/        [Singapore Property Regulatory Data]
│   ├── id (UUID, Primary Key)
│   ├── project_id (UUID, Foreign Key → projects.id)
│   ├── land_area (Float, Required) - in sqm
│   ├── gfa (Float, Required) - Gross Floor Area
│   ├── gfa_approved (Float, Optional) - Approved GFA
│   ├── plot_ratio (Float, Required)
│   ├── site_coverage (Float, Optional) - percentage
│   ├── building_height (Float, Optional) - in meters
│   ├── storeys (Integer, Optional)
│   ├── zoning (String, Required) - URA zoning type
│   ├── land_use (String, Required)
│   ├── tenure (Enum: freehold/99-year/60-year/30-year)
│   ├── region (String, Required) - Planning region
│   ├── district (Integer, Optional) - District number (1-28)
│   ├── mukim (String, Optional) - Mukim lot number
│   ├── lot_number (String, Optional)
│   ├── lease_start_date (Date, Optional)
│   ├── lease_end_date (Date, Optional)
│   ├── ura_approval_status (String, Optional)
│   ├── ura_approval_date (Date, Optional)
│   ├── bca_approval_status (String, Optional)
│   ├── bca_approval_date (Date, Optional)
│   ├── bca_submission_number (String, Optional)
│   ├── green_mark_rating (String, Optional)
│   ├── accessibility_rating (String, Optional)
│   ├── created_at (DateTime, Required)
│   └── updated_at (DateTime, Required)
│
└── ai_agents/                [AI Assistant Configurations]
    ├── id (UUID, Primary Key)
    ├── name (String, Required)
    ├── agent_type (Enum: compliance/cost_estimator/design/analysis)
    ├── description (Text, Optional)
    ├── capabilities (JSON, Required) - List of capabilities
    ├── configuration (JSON, Optional) - Agent-specific settings
    ├── model_version (String, Optional) - AI model version
    ├── is_active (Boolean, Default: true)
    ├── created_by (UUID, Foreign Key → users.id)
    ├── created_at (DateTime, Required)
    ├── updated_at (DateTime, Required)
    │
    └── ai_agent_sessions/     [AI Interaction History]
        ├── id (UUID, Primary Key)
        ├── agent_id (UUID, Foreign Key → ai_agents.id)
        ├── user_id (UUID, Foreign Key → users.id)
        ├── project_id (UUID, Foreign Key → projects.id, Optional)
        ├── session_start (DateTime, Required)
        ├── session_end (DateTime, Optional)
        ├── messages (JSON, Required) - Conversation history
        ├── context (JSON, Optional) - Session context
        ├── recommendations (JSON, Optional) - AI recommendations
        ├── analysis_results (JSON, Optional) - Analysis output
        ├── feedback_rating (Integer, Optional) - User rating (1-5)
        ├── feedback_text (Text, Optional)
        └── created_at (DateTime, Required)
```

## 🔗 Relationships Between Models

```
users (1) ──────< (many) projects
   │                        │
   │                        │
   └──< ai_agent_sessions >─┘
                │
                │
           ai_agents

projects (1) ────── (1) singapore_property
    │
    └──────< (many) ai_agent_sessions
```

## 📋 Key Features Enabled by These Models

### Users Model Enables:
- User authentication and authorization
- Multi-role support (developers, consultants)
- Singapore company integration (UEN)
- Activity tracking

### Projects Model Enables:
- Project lifecycle management
- Budget tracking
- Timeline management
- GPS location tracking
- Multi-project portfolio view

### Singapore Property Model Enables:
- BCA compliance checking
- URA regulation validation
- Plot ratio calculations
- GFA tracking
- Green building certifications
- Lease management
- Zoning compliance

### AI Agents Model Enables:
- Automated compliance checking
- Cost estimation assistance
- Design recommendations
- Risk analysis
- Conversation history
- Learning from feedback
- Multi-agent collaboration

## 🎯 Use Cases

1. **Compliance Check Flow**:
   User → Project → Singapore Property → AI Agent (compliance) → Recommendations

2. **Cost Estimation Flow**:
   User → Project → AI Agent (cost_estimator) → Analysis Results

3. **Development Potential**:
   Singapore Property → AI Agent (analysis) → GFA/Plot Ratio Optimization

4. **Project Planning**:
   User → Multiple Projects → Dashboard View → AI Insights

## 💾 Current Implementation Status

✅ **Implemented:**
- Users model (with authentication)
- Projects model (with CRUD API)
- Singapore Property model (structure defined)
- AI Agents model (structure defined)

🔄 **Next Steps:**
- Connect Singapore Property to Projects
- Implement AI Agent API
- Create GPS tracking features
- Build compliance checking logic

---

*This document represents the complete data architecture for Optimal Build.*
*Last Updated: 2025-09-29*
