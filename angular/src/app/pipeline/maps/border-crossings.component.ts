import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import * as L from 'leaflet';

import { BorderNode } from '../models/border-node.model';
import { PipelineService } from '../services/pipeline.service';

@Component({
  selector: 'app-border-crossings',
  templateUrl: './border-crossings.component.html',
  styleUrl: './border-crossings.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class BorderCrossingsComponent implements OnInit, OnDestroy {
  private readonly pipelineService = inject(PipelineService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  private map: L.Map | null = null;
  private readonly markersLayer: L.LayerGroup = L.layerGroup();

  nodes: BorderNode[] = [];
  loading = true;
  error: string | null = null;

  ngOnInit(): void {
    this.initMap();
    this.loadBorderCrossings();
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }

  private initMap(): void {
    this.map = L.map('border-map', {
      center: [48.0, 15.0],
      zoom: 4
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    this.markersLayer.addTo(this.map);
  }

  private loadBorderCrossings(): void {
    this.pipelineService.getBorderCrossings().subscribe({
      next: (nodes) => {
        this.nodes = nodes;
        this.loading = false;
        this.changeDetectorRef.markForCheck();
        this.addMarkersToMap(nodes);
      },
      error: (err) => {
        console.error('Error loading border crossings:', err);
        this.error = `Failed to load border crossings: ${err.message || err.status || 'Unknown error'}`;
        this.loading = false;
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  private addMarkersToMap(nodes: BorderNode[]): void {
    if (!this.map) {
      return;
    }

    this.markersLayer.clearLayers();

    nodes.forEach((node) => {
      const marker = L.circleMarker([node.lat, node.lon], {
        radius: 8,
        fillColor: '#e67e22',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(this.markersLayer);

      const popupContent = this.createPopup(node);
      marker.bindPopup(L.popup({ minWidth: 220 }).setContent(popupContent));
    });

    if (nodes.length > 0) {
      const bounds = L.latLngBounds(nodes.map((node) => [node.lat, node.lon] as [number, number]));
      this.map.fitBounds(bounds, { padding: [50, 50] });
    }
  }

  private createPopup(node: BorderNode): HTMLElement {
    const container = document.createElement('div');
    container.className = 'node-popup';
    container.innerHTML = `
      <h3>${node.name}</h3>
      <p><strong>ID:</strong> ${node.id}</p>
      <p><strong>Country Code:</strong> ${node.country_code}</p>
      <p><strong>From Country:</strong> ${node.from_country}</p>
      <p><strong>To Country:</strong> ${node.to_country}</p>
      ${node.from_TSO ? `<p><strong>From TSO:</strong> ${node.from_TSO}</p>` : ''}
      ${node.to_TSO ? `<p><strong>To TSO:</strong> ${node.to_TSO}</p>` : ''}
    `;
    return container;
  }
}