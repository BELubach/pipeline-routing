export enum UserRole {
  CLUSTER_ADMIN = 'CLUSTER_ADMIN',  // Can see all data across all companies
  COMPANY_OWNER = 'COMPANY_OWNER',  // Can see own company data + public GIS
  UTILITY_PROVIDER = 'UTILITY_PROVIDER'  // Can see all plants for their utility type
}

export interface User {
  id: string;
  email: string;
  username?: string;
  name?: string;
  role: UserRole;
  
  company_id?: string;
  company_name?: string;
  
  utility_type?: string;   
  utility_provider_name?: string;
}

export interface Company {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
}

export interface Plant {
  id: string;
  name: string;
  company_id: string;
  company_name: string;
  utility_type: string;
  capacity?: number;
  status: 'active' | 'inactive' | 'maintenance';
  location?: {
    lat: number;
    lng: number;
    address?: string;
  };
}

export interface GISConnection {
  id: string;
  name: string;
  type: string;
  is_public: boolean;
  company_id?: string;
  data?: any;
}
