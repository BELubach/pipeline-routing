import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';

import { PipelineNode, ReachableNode } from '../models/pipeline-node.model';
import { PipelineService } from '../services/pipeline.service';

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
  templateUrl: './pipeline-map.component.html',
  styleUrl: './pipeline-map.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PipelineMapComponent implements OnInit, OnDestroy {
  private readonly pipelineService = inject(PipelineService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  private map: L.Map | null = null;
  private readonly markersLayer: L.LayerGroup = L.layerGroup();
  private readonly reachableLayer: L.LayerGroup = L.layerGroup();

  nodes: PipelineNode[] = [];
  nodeTypes: NodeTypeFilter[] = [];
  displayedNodesCount = 0;
  loading = true;
  error: string | null = null;

  ngOnInit(): void {
    this.initMap();
    this.loadNodes();
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }

  onTypeToggle(_nodeType: NodeTypeFilter): void {
    this.updateMarkersDisplay();
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

    this.reachableLayer.addTo(this.map);
    this.markersLayer.addTo(this.map);
  }

  private loadNodes(): void {
    this.pipelineService.getNodes().subscribe({
      next: (nodes) => {
        this.nodes = nodes;
        this.loading = false;
        this.changeDetectorRef.markForCheck();
        this.addMarkersToMap(nodes, true);
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

  private updateMarkersDisplay(): void {
    this.markersLayer.clearLayers();
    this.addMarkersToMap(this.nodes, false);
  }

  private addMarkersToMap(nodes: PipelineNode[], fitBounds = false): void {
    try {
      if (!this.map) {
        console.error('Map not initialized!');
        return;
      }

      this.markersLayer.clearLayers();

      const uniqueNodes = nodes.filter((node, index, self) => {
        if (!Number.isFinite(node.lat) || !Number.isFinite(node.lon)) {
          return false;
        }

        return index === self.findIndex((candidate) => candidate.lat === node.lat && candidate.lon === node.lon);
      });

      this.displayedNodesCount = uniqueNodes.length;

      uniqueNodes.forEach((node) => {
        const marker = L.circleMarker([node.lat, node.lon], {
          radius: 8,
          fillColor: '#2563eb',
          color: '#fff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.85
        }).addTo(this.markersLayer);

        const popupContent = this.createNodePopup(node);
        const popup = L.popup({ minWidth: 250 }).setContent(popupContent);
        marker.bindPopup(popup);

        marker.on('popupopen', () => {
          this.setupPopupInteraction(node);
        });
      });

      if (fitBounds && uniqueNodes.length > 0) {
        const bounds = L.latLngBounds(uniqueNodes.map((node) => [node.lat, node.lon] as [number, number]));
        this.map.fitBounds(bounds, { padding: [50, 50] });
        console.log('Map bounds set to:', bounds);
      }

      console.log('Markers added successfully:', uniqueNodes.length);
      this.changeDetectorRef.markForCheck();
    } catch (error) {
      console.error('Error adding markers to map:', error);
    }
  }

  private createNodePopup(node: PipelineNode): HTMLElement {
    const container = document.createElement('div');
    container.className = 'node-popup';
    container.innerHTML = `
      <h3>${node.name}</h3>
      ${node.country_code ? `<p><strong>Country Code:</strong> ${node.country_code}</p>` : ''}
      <hr>
      <div class="reachable-section">
        <h4>Find Reachable Nodes</h4>
        <label for="maxCost-${node.id}">Max Cost (EUR/MWh):</label>
        <input type="number" id="maxCost-${node.id}" value="1000" step="100" min="0">
        <button id="findReachable-${node.id}">Find Reachable</button>
        <button id="clearReachable-${node.id}" style="margin-left: 5px;">Clear</button>
        <div id="reachableResult-${node.id}" class="reachable-result"></div>
      </div>
    `;
    return container;
  }

  private setupPopupInteraction(node: PipelineNode): void {
    const findButton = document.getElementById(`findReachable-${node.id}`);
    const clearButton = document.getElementById(`clearReachable-${node.id}`);
    const maxCostInput = document.getElementById(`maxCost-${node.id}`) as HTMLInputElement | null;
    const resultDiv = document.getElementById(`reachableResult-${node.id}`);

    if (findButton && maxCostInput && resultDiv) {
      findButton.addEventListener('click', () => {
        const maxCost = Number.parseFloat(maxCostInput.value);
        if (maxCost > 0) {
          this.findReachableNodes(node, maxCost, resultDiv);
        }
      });
    }

    if (clearButton) {
      clearButton.addEventListener('click', () => {
        this.clearReachableNodes();
        if (resultDiv) {
          resultDiv.innerHTML = '';
        }
      });
    }
  }

  private findReachableNodes(sourceNode: PipelineNode, maxCost: number, resultDiv: HTMLElement): void {
    resultDiv.innerHTML = '<p class="loading-text">Loading...</p>';

    this.pipelineService.getReachableNodes(sourceNode.id, maxCost).subscribe({
      next: (response) => {
        this.visualizeReachableNodes(sourceNode, response.nodes);
        resultDiv.innerHTML = `
          <p class="success-text">Found ${response.reachable_count} reachable nodes</p>
        `;
      },
      error: (err) => {
        console.error('Error fetching reachable nodes:', err);
        resultDiv.innerHTML = `<p class="error-text">Error: ${err.message || 'Failed to load'}</p>`;
      }
    });
  }

  private visualizeReachableNodes(sourceNode: PipelineNode, reachableNodes: ReachableNode[]): void {
    this.reachableLayer.clearLayers();

    if (!this.map) {
      return;
    }

    reachableNodes.forEach((targetNode) => {
      const line = L.polyline(
        [[sourceNode.lat, sourceNode.lon], [targetNode.lat, targetNode.lon]],
        {
          color: '#2ecc71',
          weight: 2,
          opacity: 0.6,
          dashArray: '5, 5'
        }
      ).addTo(this.reachableLayer);

      line.bindPopup(`
        <div class="path-popup">
          <p><strong>From:</strong> ${sourceNode.name}</p>
          <p><strong>To:</strong> ${targetNode.name}</p>
          <p><strong>Cost:</strong> ${targetNode.cost_eur_mwh.toFixed(4)} EUR/MWh</p>
        </div>
      `);
    });

    reachableNodes.forEach((node) => {
      const marker = L.circleMarker([node.lat, node.lon], {
        radius: 6,
        fillColor: '#2ecc71',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(this.reachableLayer);

      marker.bindPopup(`
        <div class="reachable-node-popup">
          <h4>${node.name}</h4>
          <p><strong>Type:</strong> ${node.node_type.replace(/_/g, ' ')}</p>
          <p><strong>Cost:</strong> ${node.cost_eur_mwh.toFixed(4)} EUR/MWh</p>
        </div>
      `);
    });

    const sourceMarker = L.circleMarker([sourceNode.lat, sourceNode.lon], {
      radius: 10,
      fillColor: '#e74c3c',
      color: '#fff',
      weight: 3,
      opacity: 1,
      fillOpacity: 0.9
    }).addTo(this.reachableLayer);

    sourceMarker.bindPopup('<div class="source-node-popup"><strong>Source Node</strong></div>');
  }

  private clearReachableNodes(): void {
    this.reachableLayer.clearLayers();
  }
}