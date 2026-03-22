import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';
import { PipelineService } from '../services/pipeline.service';
import { PipelineNode } from '../models/pipeline-node.model';

interface NodeTypeFilter {
  type: string;
  label: string;
  color: string;
  selected: boolean;
  count: number;
}

@Component({
  selector: 'app-pipeline-map',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './pipeline-map.component.html',
  styleUrls: ['./pipeline-map.component.css']
})
export class PipelineMapComponent implements OnInit, OnDestroy {
  private map: L.Map | null = null;
  private markersLayer: L.LayerGroup = L.layerGroup();
  private isInitialLoad = true;
  nodes: PipelineNode[] = [];
  nodeTypes: NodeTypeFilter[] = [];
  displayedNodesCount = 0;
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
    
    // Add markers layer
    this.markersLayer.addTo(this.map);
  }

  private loadNodes(): void {
    this.pipelineService.getNodes().subscribe({
      next: (nodes) => {
        this.nodes = nodes;
        this.extractNodeTypes(nodes);
        this.loading = false;
        this.cdr.detectChanges();
        this.addMarkersToMap(nodes, true);
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

  private extractNodeTypes(nodes: PipelineNode[]): void {
    const typeMap = new Map<string, number>();
    
    nodes.forEach(node => {
      const count = typeMap.get(node.node_type) || 0;
      typeMap.set(node.node_type, count + 1);
    });

    this.nodeTypes = Array.from(typeMap.entries()).map(([type, count]) => ({
      type,
      label: this.formatNodeType(type),
      color: this.getNodeColor(type),
      selected: true,
      count
    }));
  }

  private formatNodeType(type: string): string {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  }

  private getNodeColor(nodeType: string): string {
    switch (nodeType) {
      case 'border_crossing':
        return '#3498db'; // Blue
      case 'lng_terminal':
        return '#e74c3c'; // Red
      default:
        return '#95a5a6'; // Gray
    }
  }

  onTypeToggle(nodeType: NodeTypeFilter): void {
    this.updateMarkersDisplay();
  }

  private updateMarkersDisplay(): void {
    this.markersLayer.clearLayers();
    this.addMarkersToMap(this.nodes, false);
  }

  private addMarkersToMap(nodes: PipelineNode[], fitBounds: boolean = false): void {
    try {
      
      if (!this.map) {
        console.error('Map not initialized!');
        return;
      }

      // Clear existing markers
      this.markersLayer.clearLayers();

      // Get selected types
      const selectedTypes = new Set(this.nodeTypes.filter(t => t.selected).map(t => t.type));
      
      // If no types selected yet (on initial load), show all
      const shouldFilterByType = this.nodeTypes.length > 0;

      // Filter nodes by selected types
      const filteredNodes = shouldFilterByType 
        ? nodes.filter(node => selectedTypes.has(node.node_type))
        : nodes;

      // Remove duplicates based on coordinates
      const uniqueNodes = filteredNodes.filter((node, index, self) =>
        index === self.findIndex((n) => n.lat === node.lat && n.lon === node.lon)
      );
      
      console.log('Unique nodes:', uniqueNodes.length);
      this.displayedNodesCount = uniqueNodes.length;

      uniqueNodes.forEach((node, index) => {
        const marker = L.circleMarker([node.lat, node.lon], {
          radius: 8,
          fillColor: this.getNodeColor(node.node_type),
          color: '#fff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(this.markersLayer);

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

      // Fit map to show all markers only on initial load
      if (fitBounds && uniqueNodes.length > 0) {
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
