import { Injectable, signal } from '@angular/core';
import { DatasetMetadata, DatasetSummary } from '../models/dataset.models';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs/internal/Observable';
import { map } from 'rxjs/internal/operators/map';

@Injectable({
  providedIn: 'root',
})
export class DatasetService {
  datasets = signal<DatasetSummary[]>([]);

  constructor(private http: HttpClient) { }

  getDatasetSummaries(): Observable<DatasetSummary[] > {
    return this.http.get<{ datasets: DatasetSummary[] }>('/api/v1/datasets').pipe(
      map(response => response.datasets)
    );
  }

  getDatasetDetails(datasetId: string): Observable<DatasetMetadata> {
    return this.http.get<DatasetMetadata>(`/api/v1/datasets/${datasetId}`);
  }
}
