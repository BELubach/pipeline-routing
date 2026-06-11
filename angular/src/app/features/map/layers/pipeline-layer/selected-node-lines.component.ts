import * as L from 'leaflet';

import { PipelineNode } from '../../models/pipeline-node.model';
import { RouteResponse } from '../../models/pipeline-segments';

export class SelectedNodeLinesComponent {
  private map: L.Map | null = null;
  private readonly linesLayer: L.LayerGroup = L.layerGroup();

  initialize(map: L.Map): void {
    this.map = map;
    this.linesLayer.addTo(this.map);
  }

  clear(): void {
    this.linesLayer.clearLayers();
  }

  showStartNode(node: PipelineNode): void {
    if (!this.map) {
      return;
    }

    this.linesLayer.clearLayers();

    L.circleMarker([node.lat, node.lon], {
      radius: 7,
      fillColor: '#e74c3c',
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95
    })
      .bindPopup(`<strong>Start:</strong> ${node.name}`)
      .addTo(this.linesLayer);
  }

  drawRoute(sourceNode: PipelineNode, targetNode: PipelineNode, route: RouteResponse, allNodes: PipelineNode[] = []): void {
    if (!this.map) {
      return;
    }

    this.linesLayer.clearLayers();

    if (route.path.length > 0) {
      route.path.forEach((segment) => {
        if (!segment.geometry?.coordinates || segment.geometry.coordinates.length < 2) {
          return;
        }

        L.polyline(
          segment.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]),
          {
            color: '#f39c12',
            weight: 4,
            opacity: 0.85
          }
        ).addTo(this.linesLayer);
      });
    } else if ((route.node_sequence?.length ?? 0) > 1) {
      const nodeMap = new Map(allNodes.map((node) => [String(node.id), node]));
      const coordinates: [number, number][] = (route.node_sequence ?? [])
        .map((nodeId) => nodeMap.get(String(nodeId)))
        .filter((node): node is PipelineNode => Boolean(node))
        .map((node) => [node.lat, node.lon]);

      if (coordinates.length > 1) {
        L.polyline(coordinates, {
          color: '#f39c12',
          weight: 4,
          opacity: 0.85
        }).addTo(this.linesLayer);
      }
    } else {
      L.polyline(
        [[sourceNode.lat, sourceNode.lon], [targetNode.lat, targetNode.lon]],
        {
          color: '#f39c12',
          weight: 3,
          opacity: 0.8,
          dashArray: '6, 6'
        }
      ).addTo(this.linesLayer);
    }

    L.circleMarker([sourceNode.lat, sourceNode.lon], {
      radius: 7,
      fillColor: '#e74c3c',
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95
    })
      .bindPopup(`<strong>Source:</strong> ${sourceNode.name}`)
      .addTo(this.linesLayer);

    L.circleMarker([targetNode.lat, targetNode.lon], {
      radius: 7,
      fillColor: '#16a085',
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95
    })
      .bindPopup(`<strong>Target:</strong> ${targetNode.name}`)
      .addTo(this.linesLayer);
  }
}
