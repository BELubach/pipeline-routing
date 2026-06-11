import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';

import { NodeTypeFilter, PipelineLayerComponent } from '../../layers/pipeline-layer/pipeline-layer.component';
import { SelectedNodeLinesComponent } from '../../layers/pipeline-layer/selected-node-lines.component';
import { PipelineNode } from '../../models/pipeline-node.model';
import { GemPipelineSegment, PipelineSegment, RouteResponse, ShippingLane } from '../../models/pipeline-segments';
import { PipelineService } from '../../services/pipeline.service';
import { NodeMarkerUtil } from '../../utils/node-marker.util';
import { CurrentRouteComponent } from '../map-legend/current-route.component';

@Component({
  selector: 'app-map-view',
  imports: [FormsModule, CurrentRouteComponent],
  templateUrl: './map-view.component.html',
  styleUrl: './map-view.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MapViewComponent implements OnInit, OnDestroy {
  private readonly pipelineService = inject(PipelineService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  private map: L.Map | null = null;
  private readonly pipelineLayer = new PipelineLayerComponent();
  readonly selectedNodeLines = new SelectedNodeLinesComponent();
  private selectedShippingLaneId: number | null = null;
  private startNode: PipelineNode | null = null;

  
  nodes: PipelineNode[] = [];
  nodeTypes: NodeTypeFilter[] = [];
  displayedNodesCount = 0;
  loading = true;
  error: string | null = null;
  currentRoute: RouteResponse | null = null;
  currentRouteSourceName = '';
  currentRouteTargetName = '';
  currentRouteNodes: string[] = [];

  // Pipeline segment datasets and toggles
  iggielgnSegments: PipelineSegment[] = [];
  gemSegments: GemPipelineSegment[] = [];
  shippingLanes: ShippingLane[] = [];
  showIggielgnSegments = true;
  showGemSegments = true;
  showShippingLanes = true;

  ngOnInit(): void {
    this.initMap();
    this.loadNodes();
    this.loadPipelineSegments();
    this.loadShippingLanes();
  }
  private loadPipelineSegments(): void {
    this.loading = true;
    this.pipelineService.getPipelineSegments().subscribe({
      next: (segments) => {
        this.iggielgnSegments = segments;
        this.loading = false;
        this.updateSegmentsDisplay();
        this.changeDetectorRef.markForCheck();
      },
      error: (err) => {
        this.error = `Failed to load IGGIELGN segments: ${err.message || err.status || 'Unknown error'}`;
        this.loading = false;
        this.changeDetectorRef.markForCheck();
      }
    });
    this.pipelineService.getGemSegments().subscribe({
      next: (segments) => {
        this.gemSegments = segments;
        this.updateSegmentsDisplay();
        this.changeDetectorRef.markForCheck();
      },
      error: (err) => {
        this.error = `Failed to load GEM segments: ${err.message || err.status || 'Unknown error'}`;
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  private loadShippingLanes(): void {
    this.pipelineService.getShippingLanes().subscribe({
      next: (lanes) => {
        this.shippingLanes = lanes;
        this.updateSegmentsDisplay();
        this.changeDetectorRef.markForCheck();
        console.log(`Loaded ${lanes.length} shipping lanes`);
      },
      error: (err) => {
        console.error('Failed to load shipping lanes:', err);
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  onToggleIggielgnSegments(): void {
    this.updateSegmentsDisplay();
  }

  onToggleGemSegments(): void {
    this.updateSegmentsDisplay();
  }

  onToggleShippingLanes(): void {
    this.updateSegmentsDisplay();
  }

  private updateSegmentsDisplay(): void {
    this.pipelineLayer.renderSegments({
      iggielgnSegments: this.iggielgnSegments,
      gemSegments: this.gemSegments,
      shippingLanes: this.shippingLanes,
      showIggielgnSegments: this.showIggielgnSegments,
      showGemSegments: this.showGemSegments,
      showShippingLanes: this.showShippingLanes,
      selectedShippingLaneId: this.selectedShippingLaneId,
      onShippingLaneClick: (laneId) => this.onShippingLaneClick(laneId)
    });
  }

  private onShippingLaneClick(laneId: number): void {
    if (this.selectedShippingLaneId === laneId) {
      this.selectedShippingLaneId = null;
    } else {
      this.selectedShippingLaneId = laneId;
    }

    this.updateSegmentsDisplay();
    this.changeDetectorRef.markForCheck();
  }

  ngOnDestroy(): void {
    this.pipelineLayer.clear();
    this.selectedNodeLines.clear();
    this.resetCurrentRouteData();
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

    this.pipelineLayer.initialize(this.map);
    this.selectedNodeLines.initialize(this.map);
    queueMicrotask(() => this.map?.invalidateSize());
  }

  private loadNodes(): void {
    this.pipelineService.getNodes().subscribe({
      next: (nodes) => {
        this.nodes = nodes;
        this.initializeNodeTypes(nodes);
        this.loading = false;
        this.changeDetectorRef.markForCheck();
        this.renderMarkers(true);
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

  private updateMarkersDisplay(): void {
    this.renderMarkers(false);
  }

  private renderMarkers(fitBounds = false): void {
    try {
      this.displayedNodesCount = this.pipelineLayer.renderMarkers({
        nodes: this.nodes,
        nodeTypes: this.nodeTypes,
        fitBounds,
        onMarkerClick: (node) => this.handleNodeClick(node)
      });

      this.changeDetectorRef.markForCheck();
    } catch (error) {
      console.error('Error adding markers to map:', error);
    }
  }

  private handleNodeClick(node: PipelineNode): void {
    if (!this.startNode) {
      this.startNode = node;
      this.selectedNodeLines.showStartNode(node);
      this.resetCurrentRouteData();
      this.changeDetectorRef.markForCheck();
      return;
    }

    if (String(this.startNode.id) === String(node.id)) {
      this.clearRouteAndSelection();
      this.changeDetectorRef.markForCheck();
      return;
    }

    const sourceNode = this.startNode;
    const targetNode = node;
    this.changeDetectorRef.markForCheck();

    this.pipelineService.getRoute(sourceNode.id, targetNode.id).subscribe({
      next: (route: RouteResponse) => {
        this.selectedNodeLines.drawRoute(sourceNode, targetNode, route, this.nodes);
        this.currentRoute = route;
        this.currentRouteSourceName = sourceNode.name || String(sourceNode.id);
        this.currentRouteTargetName = targetNode.name || String(targetNode.id);
        this.currentRouteNodes = this.getRouteNodeNames(route, sourceNode, targetNode);
        this.changeDetectorRef.markForCheck();
      },
      error: (err) => {
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  private clearRouteAndSelection(): void {
    this.startNode = null;
    this.selectedNodeLines.clear();
    this.resetCurrentRouteData();
  }

  onClearCurrentRoute(): void {
    this.clearRouteAndSelection();
    this.changeDetectorRef.markForCheck();
  }

  private resetCurrentRouteData(): void {
    this.currentRoute = null;
    this.currentRouteSourceName = '';
    this.currentRouteTargetName = '';
    this.currentRouteNodes = [];
  }

  private getRouteNodeNames(route: RouteResponse, sourceNode: PipelineNode, targetNode: PipelineNode): string[] {
    if ((route.node_sequence?.length ?? 0) > 0) {
      const nodeById = new Map(this.nodes.map((node) => [String(node.id), node]));
      return (route.node_sequence ?? [])
        .map((nodeId) => nodeById.get(String(nodeId))?.name || String(nodeId));
    }

    return [sourceNode.name || String(sourceNode.id), targetNode.name || String(targetNode.id)];
  }
}
