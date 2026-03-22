import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PipelineNode } from '../models/pipeline-node.model';

@Injectable({
  providedIn: 'root'
})
export class PipelineService {
  private apiUrl = '/api/v1';

  constructor(private http: HttpClient) {}

  getNodes(): Observable<PipelineNode[]> {
    return this.http.get<PipelineNode[]>(`${this.apiUrl}/pipelines/nodes`);
  }
}
