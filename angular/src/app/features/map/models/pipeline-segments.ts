export type NodeId = string | number;


export interface GemPipelineSegment {
  id: number;
  pipeline_name: string;
  geometry: {
    type: 'MultiLineString';
    coordinates: [number, number][][];
  };
}

export interface RouteSegment {
  segment_id: number;
  from_node_id: number;
  to_node_id: number;
  length_km: number;
  geometry: {
    type: 'LineString';
    coordinates: [number, number][];
  } | null;
}

export interface RouteResponse {
  source_node_id: number;
  target_node_id: number;
  total_distance_km: number;
  num_segments: number;
  path: RouteSegment[];
  node_sequence?: number[];
}


