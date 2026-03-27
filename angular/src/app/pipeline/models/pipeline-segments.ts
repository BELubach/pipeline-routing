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