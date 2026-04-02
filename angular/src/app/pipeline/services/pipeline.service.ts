import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
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
    return this.http.get<{ metadata: any; data: PipelineNode[] }>(`${this.apiUrl}/pipelines/nodes-unified`)
      .pipe(map(res => res.data));
  }


  getBorderCrossings(): Observable<BorderNode[]> {
    return this.http.get<BorderNode[]>(`${this.apiUrl}/pipelines/border-crossings`);
  }

  getPipelineSegments(): Observable<PipelineSegment[]> {
    return this.http
      .get<{ metadata: any; data: PipelineSegment[] }>(`${this.apiUrl}/pipelines/segments`)
      .pipe(map(res => res.data));
  }

  getRoute(sourceNodeId: NodeId, targetNodeId: NodeId): Observable<RouteResponse> {
    return this.http
      .get<{
        metadata: any;
        data: RouteResponse;
      }>(
        `${this.apiUrl}/pipelines/route/${sourceNodeId}/${targetNodeId}`
      )
      .pipe(map(res => res.data));
  }
}

