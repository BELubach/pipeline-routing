import * as L from 'leaflet';

import { PipelineNode } from '../../models/pipeline-node.model';
import { GemPipelineSegment, PipelineSegment, ShippingLane } from '../../models/pipeline-segments';
import { NodeMarkerUtil } from '../../utils/node-marker.util';

export interface NodeTypeFilter {
  type: string;
  label: string;
  color: string;
  selected: boolean;
  count: number;
}

interface SegmentRenderConfig {
  iggielgnSegments: PipelineSegment[];
  gemSegments: GemPipelineSegment[];
  shippingLanes: ShippingLane[];
  showIggielgnSegments: boolean;
  showGemSegments: boolean;
  showShippingLanes: boolean;
  selectedShippingLaneId: number | null;
  onShippingLaneClick: (laneId: number) => void;
}

interface MarkerRenderConfig {
  nodes: PipelineNode[];
  nodeTypes: NodeTypeFilter[];
  fitBounds: boolean;
  onMarkerClick: (node: PipelineNode) => void;
}

export class PipelineLayerComponent {
  private map: L.Map | null = null;
  private readonly markersLayer: L.LayerGroup = L.layerGroup();
  private readonly segmentsLayer: L.LayerGroup = L.layerGroup();
  private shippingLanePolylines: Map<number, L.Polyline> = new Map();

  initialize(map: L.Map): void {
    this.map = map;
    this.segmentsLayer.addTo(this.map);
    this.markersLayer.addTo(this.map);
  }

  clear(): void {
    this.markersLayer.clearLayers();
    this.segmentsLayer.clearLayers();
    this.shippingLanePolylines.clear();
  }

  renderSegments(config: SegmentRenderConfig): void {
    if (!this.map) {
      return;
    }

    this.segmentsLayer.clearLayers();
    this.shippingLanePolylines.clear();

    if (config.showIggielgnSegments) {
      config.iggielgnSegments.forEach((segment) => {
        this.drawLineString(segment.geometry.coordinates, {
          color: '#0074D9',
          weight: 4,
          opacity: 0.7
        });
      });
    }

    if (config.showGemSegments) {
      config.gemSegments.forEach((segment) => {
        this.drawMultiLineString(segment.geometry.coordinates, {
          color: '#FF4136',
          weight: 4,
          opacity: 0.7,
          dashArray: '8, 8'
        });
      });
    }

    if (config.showShippingLanes) {
      config.shippingLanes.forEach((lane) => {
        const isSelected = lane.id === config.selectedShippingLaneId;
        const polyline = this.drawShippingLane(lane, isSelected, config.onShippingLaneClick);
        if (polyline) {
          this.shippingLanePolylines.set(lane.id, polyline);
        }
      });
    }
  }

  renderMarkers(config: MarkerRenderConfig): number {
    if (!this.map) {
      return 0;
    }

    this.markersLayer.clearLayers();

    const selectedTypes = new Set(config.nodeTypes.filter((nodeType) => nodeType.selected).map((nodeType) => nodeType.type));
    const seenCoordinates = new Set<string>();
    const uniqueNodes: PipelineNode[] = [];

    for (const node of config.nodes) {
      if (!Number.isFinite(node.lat) || !Number.isFinite(node.lon)) {
        continue;
      }

      const nodeType = node.node_type || 'generic';
      if (selectedTypes.size > 0 && !selectedTypes.has(nodeType)) {
        continue;
      }

      const key = `${node.lat.toFixed(6)}|${node.lon.toFixed(6)}`;
      if (seenCoordinates.has(key)) {
        continue;
      }

      seenCoordinates.add(key);
      uniqueNodes.push(node);
    }

    uniqueNodes.forEach((node) => {
      const marker = NodeMarkerUtil.createNodeMarker(node).addTo(this.markersLayer);
      marker.on('click', () => config.onMarkerClick(node));
    });

    if (config.fitBounds && uniqueNodes.length > 0) {
      const bounds = L.latLngBounds(uniqueNodes.map((node) => [node.lat, node.lon] as [number, number]));
      this.map.fitBounds(bounds, { padding: [50, 50] });
    }

    return uniqueNodes.length;
  }

  private drawLineString(coordinates: [number, number][] | null | undefined, style: L.PolylineOptions): void {
    if (!coordinates) {
      return;
    }

    L.polyline(coordinates.map(([lon, lat]) => [lat, lon] as [number, number]), style).addTo(this.segmentsLayer);
  }

  private drawMultiLineString(coordinates: [number, number][][] | null | undefined, style: L.PolylineOptions): void {
    if (!coordinates) {
      return;
    }

    coordinates.forEach((line) => {
      L.polyline(line.map(([lon, lat]) => [lat, lon] as [number, number]), style).addTo(this.segmentsLayer);
    });
  }

  private drawShippingLane(
    lane: ShippingLane,
    isSelected: boolean,
    onShippingLaneClick: (laneId: number) => void
  ): L.Polyline | null {
    if (!lane.geometry.coordinates) {
      return null;
    }

    const style: L.PolylineOptions = {
      color: isSelected ? '#FF6B35' : '#2ECC71',
      weight: isSelected ? 5 : 3,
      opacity: isSelected ? 0.9 : 0.6,
      dashArray: isSelected ? '' : '10, 5'
    };

    const polyline = L.polyline(
      lane.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]),
      style
    );

    polyline.on('click', () => onShippingLaneClick(lane.id));
    polyline.addTo(this.segmentsLayer);
    return polyline;
  }
}
