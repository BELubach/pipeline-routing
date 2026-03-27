import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import * as L from 'leaflet';

import { PipelineNode } from './models/pipeline-node.model';
import { PipelineSegment } from './models/pipeline-segments';
import { PipelineService } from './services/pipeline.service';

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

  segments: PipelineSegment[] = [];
  nodes: PipelineNode[] = [];
  loading = true;
  error: string | null = null;

  
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
  }



  private loadSegments(): void {
    this.pipelineService.getPipelineSegments().subscribe({
      next: (segments) => {
        this.segments = segments;
        this.loadNodes();
        console.log('Loaded segments:', segments.length);
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

    // Collect all unique node IDs that are referenced in segments
    const referencedNodeIds = new Set<string | number>();
    this.segments.forEach((segment) => {
      referencedNodeIds.add(segment.from_node);
      referencedNodeIds.add(segment.to_node);
    });

    // Draw markers for ALL nodes with different colors
    this.nodes.forEach((node) => {
      if (!Number.isFinite(node.lat) || !Number.isFinite(node.lon)) {
        return;
      }

      const isSegmentEndpoint = referencedNodeIds.has(node.id);

      const marker = L.circleMarker([node.lat, node.lon], {
        radius: isSegmentEndpoint ? 6 : 5,
        fillColor: isSegmentEndpoint ? '#ef4444' : '#2563eb',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: isSegmentEndpoint ? 0.9 : 0.7
      }).addTo(this.markersLayer);

      marker.bindPopup(`
        <div class="node-popup">
          <h4>${node.name}</h4>
          <p><strong>ID:</strong> ${node.id}</p>
          ${node.country_code ? `<p><strong>Country:</strong> ${node.country_code}</p>` : ''}
          <p><em>${isSegmentEndpoint ? 'Segment endpoint' : 'Generic node'}</em></p>
        </div>
      `);
    });

    console.log(`Drew ${this.nodes.length} total nodes (${referencedNodeIds.size} segment endpoints)`);
  }


}
