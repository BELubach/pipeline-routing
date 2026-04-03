import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';

import { PipelineNode, ReachableNode } from '../models/pipeline-node.model';
import { GemPipelineSegment } from '../models/pipeline-segments';
import { PipelineService } from '../services/pipeline.service';
import { NodeMarkerUtil } from '../utils/node-marker.util';

interface NodeTypeFilter {
  type: string;
  label: string;
  color: string;
  selected: boolean;
  count: number;
}

@Component({
  selector: 'app-pipeline-map',
  imports: [FormsModule],
  templateUrl: './gem-pipeline-segments.component.html',
  styleUrl: './gem-pipeline-segments.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PipelineMapComponent implements OnInit, OnDestroy {
  private readonly pipelineService = inject(PipelineService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  private map: L.Map | null = null;
  private readonly segmentsLayer: L.LayerGroup = L.layerGroup();

  nodes: PipelineNode[] = [];
  nodeTypes: NodeTypeFilter[] = [];
  displayedNodesCount = 0;
  loading = true;
  error: string | null = null;

  // Pipeline segment datasets and toggles
  gemSegments: GemPipelineSegment[] = [];
  showIggielgnSegments = true;
  showGemSegments = true;

  ngOnInit(): void {
    this.initMap();
    this.loadNodes();
    this.loadPipelineSegments();
  }
  private loadPipelineSegments(): void {
    this.loading = true;
    this.pipelineService.getGemSegments().subscribe({
      next: (segments) => {
        this.gemSegments = segments;
        this.loading = false;
        this.updateSegmentsDisplay();
        this.changeDetectorRef.markForCheck();
      },
      error: (err) => {
        this.error = `Failed to load GEM segments: ${err.message || err.status || 'Unknown error'}`;
        this.loading = false;
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  private updateSegmentsDisplay(): void {
    if (!this.map || this.gemSegments.length === 0) {
      return;
    }

    this.segmentsLayer.clearLayers();

    const allCoords: [number, number][] = [];

    this.gemSegments.forEach(segment => {
      this.drawMultiLineString(segment.geometry.coordinates, {
        color: '#FF4136',
        weight: 4,
        opacity: 0.7,
        dashArray: '8, 8'
      });

      segment.geometry.coordinates.forEach(line => {
        line.forEach(([lon, lat]) => {
          allCoords.push([lat, lon]);
        });
      });
    });

    if (allCoords.length > 0) {
      this.map.fitBounds(L.latLngBounds(allCoords), { padding: [24, 24] });
    }
  }

  private drawMultiLineString(coordinates: [number, number][][] | null | undefined, style: L.PolylineOptions): void {
    if (!this.map || !coordinates) {
      return;
    }

    coordinates.forEach(line => {
      L.polyline(line.map(([lon, lat]) => [lat, lon] as [number, number]), style).addTo(this.segmentsLayer);
    });
  }


  ngOnDestroy(): void {
    this.map?.remove();
  }



  private initMap(): void {
    this.map = L.map('map', {
      center: [45.0, 10.0],
      zoom: 4
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    this.segmentsLayer.addTo(this.map);
    queueMicrotask(() => this.map?.invalidateSize());

  }

  private loadNodes(): void {
    this.pipelineService.getNodes().subscribe({
      next: (nodes) => {
        this.nodes = nodes;
        this.initializeNodeTypes(nodes);
        this.loading = false;
        this.changeDetectorRef.markForCheck();
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

  private initializeNodeTypes(nodes: PipelineNode[]): void {
    const typeCounts = new Map<string, number>();
    
    nodes.forEach(node => {
      const type = node.node_type || 'generic';
      typeCounts.set(type, (typeCounts.get(type) || 0) + 1);
    });

    this.nodeTypes = Array.from(typeCounts.entries()).map(([type, count]) => {
      const config = NodeMarkerUtil.getNodeTypeConfig(type);
      return {
        type,
        label: config.label,
        color: config.color,
        selected: true,
        count
      };
    });
  }
}