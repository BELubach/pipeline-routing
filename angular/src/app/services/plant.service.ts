import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Plant } from '../models/plant.model';

@Injectable({
  providedIn: 'root'
})
export class PlantService {
  private apiUrl = '/api/v1/plants';

  constructor(private http: HttpClient) { }

  getAllPlants(): Observable<Plant[]> {
    return this.http.get<Plant[]>(this.apiUrl);
  }

  getPlantById(id: number): Observable<Plant> {
    return this.http.get<Plant>(`${this.apiUrl}/${id}`);
  }

  createPlant(plant: Plant): Observable<Plant> {
    return this.http.post<Plant>(this.apiUrl, plant);
  }

  updatePlant(id: number, plant: Partial<Plant>): Observable<Plant> {
    return this.http.put<Plant>(`${this.apiUrl}/${id}`, plant);
  }

  deletePlant(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }
}
