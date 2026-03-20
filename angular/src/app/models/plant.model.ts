export interface PlantGeometry {
  type: string;
  coordinates: number[][][];
}

export interface Plant {
  id?: number;
  name: string;
  geometry: PlantGeometry;
  created_at?: string;
  updated_at?: string;
}
