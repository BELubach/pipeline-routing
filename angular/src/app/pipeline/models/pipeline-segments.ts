export type NodeId = string | number;

export interface PipelineSegment {
  id: number;
  IGGIELGN_id: string;
  from_node: NodeId;
  to_node: NodeId;
  length_km: number;
  country_code_from: string;
  country_code_to: string;
  is_H_gas: boolean;
  geometry: {
    type: 'LineString';
    coordinates: [number, number][];
  };
}

export interface RouteSegment {
  segment_id: number;
  from_node_id: NodeId;
  to_node_id: NodeId;
  length_km: number;
  geometry: {
    type: 'LineString';
    coordinates: [number, number][];
  } | null;
}

export interface RouteResponse {
  source_node_id: NodeId;
  target_node_id: NodeId;
  total_distance_km: number;
  num_segments: number;
  path: RouteSegment[];
}