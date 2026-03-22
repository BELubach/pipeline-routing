import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';
import { PipelineService } from '../services/pipeline.service';
import { PipelineNode } from '../models/pipeline-node.model';

@Component({
  selector: 'app-pipeline-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pipeline-map.component.html',
  styleUrls: ['./pipeline-map.component.css']
})
export class PipelineMapComponent implements OnInit, OnDestroy {
  private map: L.Map | null = null;
  nodes: PipelineNode[] = [];
  loading = true;
  error: string | null = null;

  constructor(
    private pipelineService: PipelineService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.initMap();
    this.loadNodes();
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

  private initMap(): void {
    // Initialize map centered on Europe
    this.map = L.map('map', {
      center: [45.0, 10.0],
      zoom: 4
    });

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);
    
    console.log('Map initialized:', this.map);
  }

  private loadNodes(): void {
    console.log('Loading pipeline nodes...');
    this.pipelineService.getNodes().subscribe({
      next: (nodes) => {
        console.log('Received nodes:', nodes);
        console.log('Nodes length:', nodes?.length);
        console.log('Map exists:', !!this.map);
        this.nodes = nodes;
        this.loading = false;
        this.cdr.detectChanges();
        this.addMarkersToMap(nodes);
      },
      error: (err) => {
        console.error('Error loading nodes:', err);
        this.error = `Failed to load pipeline nodes: ${err.message || err.status || 'Unknown error'}`;
        this.loading = false;
        this.cdr.detectChanges();
      },
      complete: () => {
        console.log('Observable completed');
      }
    });
  }

  private addMarkersToMap(nodes: PipelineNode[]): void {
    try {
      console.log('Adding markers to map. Nodes:', nodes?.length, 'Map:', !!this.map);
      
      if (!this.map) {
        console.error('Map not initialized!');
        return;
      }

      // Remove duplicates based on coordinates
      const uniqueNodes = nodes.filter((node, index, self) =>
        index === self.findIndex((n) => n.lat === node.lat && n.lon === node.lon)
      );
      
      console.log('Unique nodes:', uniqueNodes.length);

      // Color mapping for different node types
      const getNodeColor = (nodeType: string): string => {
        switch (nodeType) {
          case 'border_crossing':
            return '#3498db'; // Blue
          case 'lng_terminal':
            return '#e74c3c'; // Red
          default:
            return '#95a5a6'; // Gray
        }
      };

      uniqueNodes.forEach((node, index) => {
        console.log(`Adding marker ${index + 1}:`, node.name, node.lat, node.lon);
        
        const marker = L.circleMarker([node.lat, node.lon], {
          radius: 8,
          fillColor: getNodeColor(node.node_type),
          color: '#fff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(this.map!);

        // Create popup content
        const popupContent = `
          <div class="node-popup">
            <h3>${node.name}</h3>
            <p><strong>Type:</strong> ${node.node_type.replace('_', ' ')}</p>
            <p><strong>Country:</strong> ${node.country}</p>
            ${node.lng_capacity_bcm ? `<p><strong>LNG Capacity:</strong> ${node.lng_capacity_bcm} BCM</p>` : ''}
            ${node.lng_type ? `<p><strong>LNG Type:</strong> ${node.lng_type}</p>` : ''}
            ${node.is_trading_hub ? '<p><strong>Trading Hub</strong></p>' : ''}
          </div>
        `;

        marker.bindPopup(popupContent);
      });

      // Fit map to show all markers
      if (uniqueNodes.length > 0) {
        const bounds = L.latLngBounds(uniqueNodes.map(node => [node.lat, node.lon]));
        this.map.fitBounds(bounds, { padding: [50, 50] });
        console.log('Map bounds set to:', bounds);
      }
    
    console.log('Markers added successfully');
    } catch (error) {
      console.error('Error adding markers to map:', error);
    }
  }
}
