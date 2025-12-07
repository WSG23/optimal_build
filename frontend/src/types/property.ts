export enum PropertyType {
  OFFICE = 'office',
  RETAIL = 'retail',
  INDUSTRIAL = 'industrial',
  RESIDENTIAL = 'residential',
  MIXED_USE = 'mixed_use',
  HOTEL = 'hotel',
  WAREHOUSE = 'warehouse',
  LAND = 'land',
  SPECIAL_PURPOSE = 'special_purpose',
}

export enum PropertyStatus {
  EXISTING = 'existing',
  PLANNED = 'planned',
  APPROVED = 'approved',
  UNDER_CONSTRUCTION = 'under_construction',
  COMPLETED = 'completed',
  DEMOLISHED = 'demolished',
}

export enum TenureType {
  FREEHOLD = 'freehold',
  LEASEHOLD_99 = 'leasehold_99',
  LEASEHOLD_999 = 'leasehold_999',
  LEASEHOLD_60 = 'leasehold_60',
  LEASEHOLD_30 = 'leasehold_30',
  LEASEHOLD_OTHER = 'leasehold_other',
}

export interface Property {
  id: string
  name: string
  address: string
  postal_code?: string
  property_type: PropertyType
  status?: PropertyStatus
  location: {
    type: 'Point'
    coordinates: [number, number] // [longitude, latitude]
  }
  district?: string
  subzone?: string
  planning_area?: string
  land_area_sqm?: number
  gross_floor_area_sqm?: number
  net_lettable_area_sqm?: number
  building_height_m?: number
  floors_above_ground?: number
  floors_below_ground?: number
  units_total?: number
  year_built?: number
  year_renovated?: number
  developer?: string
  architect?: string
  tenure_type?: TenureType
  lease_start_date?: string
  lease_expiry_date?: string
  zoning_code?: string
  plot_ratio?: number
  is_conservation?: boolean
  conservation_status?: string
  heritage_constraints?: unknown
  created_at: string
  updated_at: string
}
