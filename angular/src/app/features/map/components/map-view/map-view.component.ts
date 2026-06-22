import { ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import * as L from 'leaflet';

import { NodeTypeFilter, PipelineLayerComponent } from '../../layers/pipeline-layer/pipeline-layer.component';
import { CurrentRouteComponent } from '../map-legend/current-route.component';
import { DataSelectComponent } from '../map-legend/data-select-component';
import { CustomBoxComponent } from '../map-legend/custom-box.component';
@Component({
  selector: 'app-map-view',
  standalone: true,
  imports: [CurrentRouteComponent, DataSelectComponent, CustomBoxComponent],
  templateUrl: './map-view.component.html',
  styleUrl: './map-view.component.css'
})
export class MapViewComponent implements OnInit, OnDestroy {
  private map: L.Map | null = null;
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  readonly drawingLayer = inject(PipelineLayerComponent);
  readonly selectedRouteLayer = this.drawingLayer.selectedNodeLines;

  readonly legendVisibility = {
    showIggielgnSegments: true,
    showGemSegments: true,
    showShippingLanes: true, 
    showGenericNodes: true,
    showLngNodes: true,
    showBorderNodes: true

  };

  ngOnInit(): void {
    this.drawingLayer.setStateChangeHandler(() => this.changeDetectorRef.markForCheck());
    this.initMap();
    this.drawingLayer.loadData();
  }

  onLegendVisibilityChanged(): void {
    this.applyLegendVisibility();
    console.log('Legend visibility changed:', this.legendVisibility);
  }


  private applyLegendVisibility(): void {
    this.drawingLayer.renderSegments(this.legendVisibility);
    this.drawingLayer.renderMarkers(this.legendVisibility);
  }


  ngOnDestroy(): void {
    this.drawingLayer.setStateChangeHandler(null);
    this.drawingLayer.clear();
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

    this.drawingLayer.initialize(this.map);
    this.applyLegendVisibility();
    this.drawingLayer.renderMarkers(this.legendVisibility);
    queueMicrotask(() => this.map?.invalidateSize());
  }

  onClearCurrentRoute(): void {
    this.drawingLayer.onClearCurrentRoute();
  }
}
