import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PipelineNode, ReachableNodesResponse } from '../models/pipeline-node.model';

@Injectable({
  providedIn: 'root'
})
export class PipelineService {
  private apiUrl = '/api/v1';

  constructor(private http: HttpClient) {}

  getNodes(): Observable<PipelineNode[]> {
    return this.http.get<PipelineNode[]>(`${this.apiUrl}/pipelines/nodes`);
  }

  getReachableNodes(nodeId: number, maxCost: number): Observable<ReachableNodesResponse> {
    return this.http.get<ReachableNodesResponse>(
      `${this.apiUrl}/pipelines/nodes/${nodeId}/reachable?max_cost=${maxCost}`
    );
  }
}
