export interface DatasetSummary {
    id: string; 
    name: string;
    source: string;
    description: string;
    dataset_date: string;
    website: string;
}


export interface DatasetDetails { 
    id: string;
    name: string; 
    node_count: number;
    edge_count: number;
    nodes: any[];
    edges: any[];
}

interface DatasetComponent {
    key: string;
    label: string;
    kind: string;
    description: string;
    record_count: number;
    derivation: string;
}

export interface DatasetMetadata {
    id: string;
    name: string;
    description: string;
    has_nodes: boolean;
    has_edges: boolean;
    primary_network_type: string;
    components: DatasetComponent[];
}