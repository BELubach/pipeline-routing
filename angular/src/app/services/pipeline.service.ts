import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PipelineNode, ReachableNodesResponse } from '../models/pipeline-node.model';
import { BorderNode } from '../models/border-node.model';

@Injectable({
  providedIn: 'root'
})
export class PipelineService {
  private apiUrl = '/api/v1';

  constructor(private http: HttpClient) {}

  getNodes(): Observable<PipelineNode[]> {
    return this.http.get<PipelineNode[]>(`${this.apiUrl}/pipelines/border-nodes`);
  }

  getReachableNodes(nodeId: number, maxCost: number): Observable<ReachableNodesResponse> {
    return this.http.get<ReachableNodesResponse>(
      `${this.apiUrl}/pipelines/nodes/${nodeId}/reachable?max_cost=${maxCost}`
    );
  }

  getBorderCrossings(): Observable<BorderNode[]> {
    return this.http.get<BorderNode[]>(`${this.apiUrl}/pipelines/border-crossings`);
  }
}
