# Role-Based Dashboard System

## Overview
The dashboard now supports three different user roles, each with a customized view showing relevant data and actions.

## User Roles

### 1. Cluster Administrator (`cluster_admin`)
**Description:** System administrator who can view and manage all data across all companies and utilities in the cluster.

**Access:**
- All companies and their data
- All plants across all utility types
- All utility providers
- All users in the system
- System-wide statistics and analytics

**Dashboard Features:**
- Total companies, plants, utilities, and users statistics
- List of all companies with their plant counts
- Recent activity across the entire cluster
- Full administrative controls

**Suggested Alternative Names:**
- Network Administrator
- Platform Administrator
- System Administrator
- Cluster Manager

---

### 2. Company Owner (`company_owner`)
**Description:** Owner of a specific company who can manage their own company's plants and access public GIS connections.

**Access:**
- Own company data only
- Own company's plants (all utility types)
- Public GIS connections (shared infrastructure data)
- Cannot see other companies' private data

**Dashboard Features:**
- Company-specific statistics (plants, active/inactive status)
- List of company's plants with detailed information
- Access to public GIS connections for infrastructure planning
- Add/manage plants within their company

**Required User Fields:**
- `company_id`: ID of the company they own
- `company_name`: Name of their company

---

### 3. Utility Provider (`utility_provider`)
**Description:** Provider of a specific utility type (electricity, gas, water, heating) who can view all plants for their utility across all companies.

**Access:**
- All plants of their specific utility type
- Data from all companies, but only for their utility
- Cannot see plants of other utility types
- Cannot see other utility providers' data

**Dashboard Features:**
- Statistics for all plants of their utility type
- Total capacity, active/maintenance plant counts
- Full list of plants by utility type across all companies
- Export and map view capabilities
- Plant monitoring and status tracking

**Required User Fields:**
- `utility_type`: Type of utility (electricity, gas, water, heating)
- `utility_provider_name`: Name of their utility provider company

**Capacity Units:**
- Electricity: MW (Megawatts)
- Gas: m³/h (Cubic meters per hour)
- Water: m³/h (Cubic meters per hour)
- Heating: MW (Megawatts)

---

## Implementation Details

### User Model
```typescript
interface User {
  id: string;
  email: string;
  username?: string;
  name?: string;
  role: UserRole;
  
  // Company-specific (for COMPANY_OWNER)
  company_id?: string;
  company_name?: string;
  
  // Utility-specific (for UTILITY_PROVIDER)
  utility_type?: string;
  utility_provider_name?: string;
}
```

### Role Enum
```typescript
enum UserRole {
  CLUSTER_ADMIN = 'cluster_admin',
  COMPANY_OWNER = 'company_owner',
  UTILITY_PROVIDER = 'utility_provider'
}
```

### Backend Requirements
Your backend `/api/v1/auth/me` endpoint should return a User object with:
1. The `role` field matching one of the UserRole enum values
2. Conditional fields based on role:
   - For `company_owner`: Include `company_id` and `company_name`
   - For `utility_provider`: Include `utility_type` and `utility_provider_name`

### Dashboard Components
- **Main Dashboard:** `dashboard.component.ts` - Routes to appropriate view based on role
- **Cluster Admin View:** `views/cluster-admin-view.component.ts`
- **Company Owner View:** `views/company-owner-view.component.ts`
- **Utility Provider View:** `views/utility-provider-view.component.ts`

Each view component receives the `User` object as input and displays role-specific data.

---

## Future Enhancements

1. **Real API Integration:**
   - Replace mock data with actual API calls
   - Create services for companies, plants, GIS connections
   - Implement real-time updates with WebSockets

2. **Additional Features:**
   - Map view integration with GIS data
   - Advanced filtering and search
   - Export capabilities (CSV, PDF reports)
   - Real-time notifications for plant status changes
   - User management interface for Cluster Admin

3. **Route Guards:**
   - Implement auth guards to protect routes
   - Role-based route access control
   - Redirect unauthorized users

4. **Analytics:**
   - Detailed charts and graphs
   - Energy consumption tracking
   - Performance metrics by utility type
   - Cost analysis and projections
