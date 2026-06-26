import * as L from 'leaflet';
import { Node } from '../models/generic-node.model';

export interface NodeTypeConfig {
  type: string;
  label: string;
  color: string;
}

export const NODE_TYPE_CONFIGS: Record<string, NodeTypeConfig> = {
  generic: { type: 'generic', label: 'Generic Node', color: '#2563eb' },
  border: { type: 'border', label: 'Border Crossing', color: '#e67e22' },
  lng: { type: 'lng', label: 'LNG Terminal', color: '#9b59b6' }
};

export class NodeMarkerUtil {
  /**
   * Get the color for a node based on its type
   */
  static getNodeColor(nodeType: string | null | undefined): string {
    const type = nodeType || 'generic';
    return NODE_TYPE_CONFIGS[type]?.color || '#555555';
  }

  /**
   * Get the label for a node type
   */
  static getNodeTypeLabel(nodeType: string | null | undefined): string {
    const type = nodeType || 'generic';
    return NODE_TYPE_CONFIGS[type]?.label || 'Unknown Type';
  }

  /**
   * Create a circle marker for a node with consistent styling
   */
  static createNodeMarker(
    node: Node,
    options?: {
      radius?: number;
      weight?: number;
      opacity?: number;
      fillOpacity?: number;
    }
  ): L.CircleMarker {
    const color = this.getNodeColor(node.node_type);
    
    return L.circleMarker([node.lat, node.lon], {
      radius: options?.radius ?? 8,
      fillColor: color,
      color: '#fff',
      weight: options?.weight ?? 2,
      opacity: options?.opacity ?? 1,
      fillOpacity: options?.fillOpacity ?? 0.85
    });
  }

  /**
   * Create a standard popup content for a node
   */
  static createNodePopupContent(
    node: Node,
    additionalInfo?: string
  ): string {
    const nodeType = this.getNodeTypeLabel(node.node_type);
    
    return `
      <div class="node-popup">
        <p><strong>Type:</strong> ${nodeType}</p>
        <p><strong>ID:</strong> ${node.id}</p>
        ${additionalInfo || ''}
      </div>
    `;
  }

  /**
   * Get all available node type configurations
   */
  static getAllNodeTypeConfigs(): NodeTypeConfig[] {
    return Object.values(NODE_TYPE_CONFIGS);
  }

  /**
   * Get node type configuration by type string
   */
  static getNodeTypeConfig(nodeType: string | null | undefined): NodeTypeConfig {
    const type = nodeType || 'generic';
    return NODE_TYPE_CONFIGS[type] || {
      type: 'unknown',
      label: 'Unknown Type',
      color: '#555555'
    };
  }
}
