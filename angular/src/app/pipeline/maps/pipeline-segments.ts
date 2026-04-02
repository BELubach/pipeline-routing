import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import * as L from 'leaflet';

import { PipelineNode } from '../models/pipeline-node.model';
import { PipelineSegment, RouteResponse } from '../models/pipeline-segments';
import { PipelineService } from '../services/pipeline.service';
import { NodeMarkerUtil } from '../utils/node-marker.util';

@Component({
  selector: 'app-pipeline-segments',
  imports: [],
  templateUrl: './pipeline-segments.html',
  styleUrl: './pipeline-segments.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PipelineSegments implements OnInit, OnDestroy {
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  private readonly pipelineService = inject(PipelineService);
  private map: L.Map | null = null;
  private readonly segmentsLayer: L.LayerGroup = L.layerGroup();
  private readonly markersLayer: L.LayerGroup = L.layerGroup();
  private readonly routeLayer: L.LayerGroup = L.layerGroup();

  segments: PipelineSegment[] = [];
  nodes: PipelineNode[] = [];
  loading = true;
  error: string | null = null;

  // Routing state
  private selectedNodes: { first: PipelineNode | null; second: PipelineNode | null } = {
    first: null,
    second: null
  };
  private nodeMarkers: Map<string | number, L.CircleMarker> = new Map();
  private segmentPolylines: Map<string | number, L.Polyline> = new Map();
  private currentRoute: RouteResponse | null = null;
  


  ngOnInit(): void {
    this.initMap();
    this.loadSegments();
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }

  private initMap(): void {
    this.map = L.map('map', {
      center: [48.0, 15.0],
      zoom: 4
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    this.segmentsLayer.addTo(this.map);
    this.markersLayer.addTo(this.map);
    this.routeLayer.addTo(this.map);
  }



  private loadSegments(): void {
    this.pipelineService.getPipelineSegments().subscribe({
      next: (segments) => {
        this.segments = segments;
        this.loadNodes();
      },
      error: (err) => {
        console.error('Error loading segments:', err);
        this.error = `Failed to load pipeline segments: ${err.message || 'Unknown error'}`;
        this.loading = false;
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  private loadNodes(): void {
    this.pipelineService.getNodes().subscribe({
      next: (nodes) => {
        this.nodes = nodes;
        this.loading = false;
        this.changeDetectorRef.markForCheck();
        this.drawSegments();
        this.drawNodes();
        console.log('Loaded nodes:', nodes.length);
      },
      error: (err) => {
        console.error('Error loading nodes:', err);
        this.error = `Failed to load pipeline nodes: ${err.message || err.status || 'Unknown error'}`;
        this.loading = false;
        this.changeDetectorRef.markForCheck();
      },
      complete: () => {
        console.log('Observable completed');
      }
    });
  }

  private drawSegments(): void {
    if (!this.map) {
      return;
    }

    this.segmentsLayer.clearLayers();
    this.segmentPolylines.clear();

    this.segments.forEach((segment) => {
      if (!segment.geometry?.coordinates || segment.geometry.coordinates.length < 2) {
        return;
      }

      // Convert GeoJSON coordinates [lon, lat] to Leaflet LatLng [lat, lon]
      const latLngs: [number, number][] = segment.geometry.coordinates.map(
        ([lon, lat]) => [lat, lon]
      );

      const color = segment.is_H_gas ? '#3b82f6' : '#10b981'; // Blue for H-gas, Green for L-gas

      const polyline = L.polyline(latLngs, {
        color,
        weight: 3,
        opacity: 0.7
      }).addTo(this.segmentsLayer);

      // Store segment data on polyline for later reference
      (polyline as any)._segmentData = segment;
      
      // Cache polyline reference
      this.segmentPolylines.set(segment.id, polyline);

      polyline.bindPopup(`
        <div class="segment-popup">
          <h4>Pipeline Segment</h4>
          <p><strong>ID:</strong> ${segment.IGGIELGN_id}</p>
          <p><strong>From:</strong> ${segment.from_node}</p>
          <p><strong>To:</strong> ${segment.to_node}</p>
          <p><strong>Length:</strong> ${segment.length_km.toFixed(2)} km</p>
          <p><strong>Gas Type:</strong> ${segment.is_H_gas ? 'H-gas' : 'L-gas'}</p>
          <p><strong>Countries:</strong> ${segment.country_code_from} → ${segment.country_code_to}</p>
        </div>
      `);
    });

    // Fit bounds to show all segments
    if (this.segments.length > 0) {
      const allCoords: [number, number][] = [];
      this.segments.forEach((segment) => {
        if (segment.geometry?.coordinates) {
          segment.geometry.coordinates.forEach(([lon, lat]) => {
            allCoords.push([lat, lon]);
          });
        }
      });

      if (allCoords.length > 0) {
        const bounds = L.latLngBounds(allCoords);
        this.map.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  }

  private drawNodes(): void {
    if (!this.map) {
      return;
    }

    this.markersLayer.clearLayers();
    this.nodeMarkers.clear();

    // Collect all unique node IDs that are referenced in segments
    const referencedNodeIds = new Set<string | number>();
    this.segments.forEach((segment) => {
      referencedNodeIds.add(segment.from_node);
      referencedNodeIds.add(segment.to_node);
    });

    // Draw markers for ALL nodes with different colors based on node_type
    this.nodes.forEach((node) => {
      if (!Number.isFinite(node.lat) || !Number.isFinite(node.lon)) {
        return;
      }

      const isSegmentEndpoint = referencedNodeIds.has(node.id);

      const marker = NodeMarkerUtil.createNodeMarker(node, {
        radius: isSegmentEndpoint ? 6 : 5,
        fillOpacity: isSegmentEndpoint ? 0.9 : 0.7
      }).addTo(this.markersLayer);

      // Store marker reference
      this.nodeMarkers.set(node.id, marker);

      // Add click handler for routing
      marker.on('click', () => this.onNodeClick(node));

      const nodeTypeLabel = NodeMarkerUtil.getNodeTypeLabel(node.node_type);
      const additionalInfo = `<p><em>${isSegmentEndpoint ? 'Segment endpoint' : 'Generic node'}</em></p>`;
      const popupContent = NodeMarkerUtil.createNodePopupContent(node, additionalInfo);
      marker.bindPopup(popupContent);
    });

    console.log(`Drew ${this.nodes.length} total nodes (${referencedNodeIds.size} segment endpoints)`);
  }

  private onNodeClick(node: PipelineNode): void {
    console.log('Node clicked:', node);

    if (!this.selectedNodes.first) {
      // First node selection
      this.selectedNodes.first = node;
      this.highlightSelectedNode(node, '#fbbf24'); // Yellow/amber for first node
      console.log('First node selected:', node.id);
    } else if (!this.selectedNodes.second) {
      // Second node selection
      if (this.selectedNodes.first.id === node.id) {
        // Clicked same node, reset
        this.clearRouting();
        return;
      }

      this.selectedNodes.second = node;
      this.highlightSelectedNode(node, '#22c55e'); // Green for second node
      console.log('Second node selected:', node.id);

      // Fetch and display route
      this.fetchAndDisplayRoute();
    } else {
      // Already have two nodes selected, reset and start over
      this.clearRouting();
      this.onNodeClick(node);
    }
  }

  private highlightSelectedNode(node: PipelineNode, color: string): void {
    const marker = this.nodeMarkers.get(node.id);
    if (marker) {
      marker.setStyle({
        fillColor: color,
        radius: 8,
        fillOpacity: 1,
        weight: 3
      });
    }
  }

  private resetSelectedNodes(): void {
    // Only reset the two highlighted nodes back to their original appearance
    if (this.selectedNodes.first) {
      const firstNode = this.selectedNodes.first;
      const isSegmentEndpoint = this.segments.some(s => s.from_node === firstNode.id || s.to_node === firstNode.id);
      const marker = this.nodeMarkers.get(firstNode.id);
      if (marker) {
        marker.setStyle({
          fillColor: NodeMarkerUtil.getNodeColor(firstNode.node_type),
          radius: isSegmentEndpoint ? 6 : 5,
          fillOpacity: isSegmentEndpoint ? 0.9 : 0.7,
          weight: 2
        });
      }
    }

    if (this.selectedNodes.second) {
      const secondNode = this.selectedNodes.second;
      const isSegmentEndpoint = this.segments.some(s => s.from_node === secondNode.id || s.to_node === secondNode.id);
      const marker = this.nodeMarkers.get(secondNode.id);
      if (marker) {
        marker.setStyle({
          fillColor: NodeMarkerUtil.getNodeColor(secondNode.node_type),
          radius: isSegmentEndpoint ? 6 : 5,
          fillOpacity: isSegmentEndpoint ? 0.9 : 0.7,
          weight: 2
        });
      }
    }
  }

  private fetchAndDisplayRoute(): void {
    if (!this.selectedNodes.first || !this.selectedNodes.second) {
      return;
    }

    console.log('Fetching route between:', this.selectedNodes.first.id, 'and', this.selectedNodes.second.id);

    this.pipelineService.getRoute(this.selectedNodes.first.id, this.selectedNodes.second.id)
      .subscribe({
        next: (route) => {
          console.log('Route received:', route);
          this.currentRoute = route;
          this.displayRoute(route);
        },
        error: (err) => {
          console.error('Error fetching route:', err);
          alert(`Failed to find route: ${err.error?.detail || err.message || 'Unknown error'}`);
          this.clearRouting();
        }
      });
  }

  private displayRoute(route: RouteResponse): void {
    if (!this.map) {
      return;
    }

    this.routeLayer.clearLayers();

    // Draw each segment in the route
    route.path.forEach((routeSegment) => {
      if (!routeSegment.geometry?.coordinates || routeSegment.geometry.coordinates.length < 2) {
        return;
      }

      const latLngs: [number, number][] = routeSegment.geometry.coordinates.map(
        ([lon, lat]) => [lat, lon]
      );

      const routeLine = L.polyline(latLngs, {
        color: '#f59e0b', // Orange/amber for route
        weight: 5,
        opacity: 1,
        className: 'route-line'
      }).addTo(this.routeLayer);

      routeLine.bindPopup(`
        <div class="route-segment-popup">
          <h4>Route Segment</h4>
          <p><strong>From:</strong> ${routeSegment.from_node_id}</p>
          <p><strong>To:</strong> ${routeSegment.to_node_id}</p>
          <p><strong>Length:</strong> ${routeSegment.length_km.toFixed(2)} km</p>
        </div>
      `);
    });

    // Add route info popup
    if (this.selectedNodes.first && this.selectedNodes.second) {
      const marker = this.nodeMarkers.get(this.selectedNodes.second.id);
      if (marker) {
        const routeInfoPopup = `
          <div class="route-info-popup">
            <h4>Route Found!</h4>
            <p><strong>From:</strong> ${this.selectedNodes.first.name}</p>
            <p><strong>To:</strong> ${this.selectedNodes.second.name}</p>
            <p><strong>Total Distance:</strong> ${route.total_distance_km} km</p>
            <p><strong>Segments:</strong> ${route.num_segments}</p>
          </div>
        `;
        marker.bindPopup(routeInfoPopup).openPopup();
      }
    }

    console.log(`Route displayed: ${route.num_segments} segments, ${route.total_distance_km} km`);
  }

  public clearRouting(): void {
    // Reset the highlighted nodes before clearing references
    this.resetSelectedNodes();
    
    // Clear the route visualization
    this.routeLayer.clearLayers();
    
    // Clear state
    this.selectedNodes.first = null;
    this.selectedNodes.second = null;
    this.currentRoute = null;
    
    console.log('Routing cleared');
  }


  
}
