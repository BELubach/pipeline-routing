import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import * as L from 'leaflet';
import { forkJoin } from 'rxjs';

import { DataSelectComponent } from '../map-legend/data-select-component';
import { PipelineLayerComponent, NodeTypeFilter } from '../../layers/pipeline-layer/pipeline-layer.component';
import { PipelineService } from '../../services/pipeline.service';
import { PipelineNode } from '../../models/pipeline-node.model';

@Component({
  selector: 'app-map-view',
  standalone: true,
  imports: [DataSelectComponent],
  templateUrl: './map-view.component.html',
  styleUrl: './map-view.component.css'
})
export class MapViewComponent implements OnInit, OnDestroy {
  private map: L.Map | null = null;
  private readonly pipelineLayer = new PipelineLayerComponent();
  private readonly pipelineService = inject(PipelineService);

  private readonly defaultNodeTypes: NodeTypeFilter[] = [
    { type: 'generic', label: 'Generic', color: '#888888', selected: true, count: 0 },
    { type: 'LNG', label: 'LNG', color: '#0074D9', selected: true, count: 0 },
    { type: 'border', label: 'Border', color: '#FF4136', selected: true, count: 0 }
  ];

  readonly legendVisibility = {
    showIggielgnSegments: true,
    showGemSegments: true,
    showGenericNodes: true,
    showLngNodes: true,
    showBorderNodes: true,
    showMaritimeSegments: true
  };

  ngOnInit(): void {
    this.initMap();
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

    this.pipelineLayer.initialize(this.map);

    queueMicrotask(() => {
      this.map?.invalidateSize();
      this.loadAndRender();
    });
  }

  private loadAndRender(): void {
    forkJoin({
      nodes: this.pipelineService.getNodes(),
      iggielgnSegments: this.pipelineService.getPipelineSegments(),
      gemSegments: this.pipelineService.getGemSegments(),
      maritimeSegments: this.pipelineService.getMaritimeSegments()
    }).subscribe({
      next: ({ nodes, iggielgnSegments, gemSegments, maritimeSegments }) => {
        this.pipelineLayer.renderSegments({
          iggielgnSegments,
          gemSegments,
          maritimeSegments,
          showIggielgnSegments: this.legendVisibility.showIggielgnSegments,
          showGemSegments: this.legendVisibility.showGemSegments,
          showMaritimeSegments: this.legendVisibility.showMaritimeSegments
        });

        this.pipelineLayer.renderMarkers({
          nodes,
          nodeTypes: this.defaultNodeTypes,
          fitBounds: true,
          onMarkerClick: (node) => this.onMarkerClick(node)
        });
      },
      error: (err) => console.error('Failed to load pipeline data', err)
    });
  }

  private onMarkerClick(node: PipelineNode): void {
    console.log('Marker clicked:', node);
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }
}
