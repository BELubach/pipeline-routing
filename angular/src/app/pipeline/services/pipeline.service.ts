import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { BorderNode } from '../models/border-node.model';
import { NodeId, PipelineNode, ReachableNodesResponse } from '../models/pipeline-node.model';
import { PipelineSegment, RouteResponse } from '../models/pipeline-segments';

@Injectable({
  providedIn: 'root'
})
export class PipelineService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1';

  getNodes(): Observable<PipelineNode[]> {
    return this.http.get<PipelineNode[]>(`${this.apiUrl}/pipelines/nodes`);
  }

  getReachableNodes(nodeId: NodeId, maxCost: number): Observable<ReachableNodesResponse> {
    return this.http.get<ReachableNodesResponse>(
      `${this.apiUrl}/pipelines/nodes/${nodeId}/reachable?max_cost=${maxCost}`
    );
  }

  getBorderCrossings(): Observable<BorderNode[]> {
    return this.http.get<BorderNode[]>(`${this.apiUrl}/pipelines/border-crossings`);
  }

  getPipelineSegments(): Observable<PipelineSegment[]> {
    return this.http.get<PipelineSegment[]>(`${this.apiUrl}/pipelines/segments`);
  }

  getRoute(sourceNodeId: NodeId, targetNodeId: NodeId): Observable<RouteResponse> {
    return this.http.get<RouteResponse>(
      `${this.apiUrl}/pipelines/route/${sourceNodeId}/${targetNodeId}`
    );
  }
}

