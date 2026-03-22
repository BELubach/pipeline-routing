export interface PipelineNode {
  id: number;
  name: string;
  node_type: 'border_crossing' | 'lng_terminal' | string;
  country: string;
  is_trading_hub: boolean;
  hub_code: string | null;
  lng_capacity_bcm: number | null;
  lng_type: 'export' | 'import' | null;
  lon: number;
  lat: number;
}
