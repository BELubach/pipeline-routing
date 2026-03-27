export type NodeId = string | number;

export interface PipelineNode {
  id: NodeId;
  name: string;
  country_code?: string | null;
  lon: number;
  lat: number;
}

export interface ReachableNode {
  id: NodeId;
  name: string;
  node_type: string;
  country: string | null;
  lon: number;
  lat: number;
  cost_eur_mwh: number;
}

export interface ReachableNodesResponse {
  source_node_id: NodeId;
  max_cost_eur_mwh: number;
  reachable_count: number;
  nodes: ReachableNode[];
}