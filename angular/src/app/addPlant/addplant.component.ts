import { Component, signal, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { PlantService } from '../services/plant.service';
import { Plant } from '../models/plant.model';
import * as L from 'leaflet';
import 'leaflet-draw';

@Component({
  selector: 'app-add-plant',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    InputTextModule,
    ButtonModule,
    MessageModule,
    ToastModule
  ],
  providers: [MessageService],
  templateUrl: './addplant.component.html',
  styleUrl: './addplant.component.css'
})
export class AddPlantComponent implements OnInit, AfterViewInit, OnDestroy {

  name = signal('');
  loading = signal(false);

  private map!: L.Map;
  private drawnItems!: L.FeatureGroup;
  private currentPolygon: L.Polygon | null = null;
  polygonCoordinates = signal<number[][][]>([]);

  constructor(
    private router: Router,
    private plantService: PlantService,
    private messageService: MessageService
  ) { }

  ngOnInit() {
    // Fix Leaflet default icon issue with webpack
    const iconRetinaUrl = 'assets/marker-icon-2x.png';
    const iconUrl = 'assets/marker-icon.png';
    const shadowUrl = 'assets/marker-shadow.png';
    const iconDefault = L.icon({
      iconRetinaUrl,
      iconUrl,
      shadowUrl,
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      tooltipAnchor: [16, -28],
      shadowSize: [41, 41]
    });
    L.Marker.prototype.options.icon = iconDefault;
  }

  ngAfterViewInit() {
    this.initMap();
  }

  ngOnDestroy() {
    if (this.map) {
      this.map.remove();
    }
  }

  private initMap() {
    this.map = L.map('map', {
      doubleClickZoom: false,
    }).setView([51.505, -0.09], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    this.drawnItems = new L.FeatureGroup();
    this.map.addLayer(this.drawnItems);

    const drawControl = new L.Control.Draw({
      draw: {
        polygon: {
          allowIntersection: false,
          showArea: true,
          metric: true,
          shapeOptions: {
            color: '#662d91',
            weight: 3
          }
        },
        polyline: false,
        circle: false,
        rectangle: false,
        marker: false,
        circlemarker: false
      },
      edit: {
        featureGroup: this.drawnItems,
        remove: true
      }
    });
    this.map.addControl(drawControl);

    this.map.on(L.Draw.Event.CREATED, (event: any) => {
      const layer = event.layer;

      if (this.currentPolygon) {
        this.drawnItems.removeLayer(this.currentPolygon);
      }
      
      this.drawnItems.addLayer(layer);
      this.currentPolygon = layer;
      
      const latlngs = layer.getLatLngs()[0];
      const coordinates = latlngs.map((latlng: L.LatLng) => [latlng.lng, latlng.lat]);

      coordinates.push(coordinates[0]);
      this.polygonCoordinates.set([coordinates]);
      
      this.messageService.add({ 
        severity: 'success', 
        summary: 'Area Defined', 
        detail: 'Plant area has been drawn on the map' 
      });
    });

    this.map.on(L.Draw.Event.EDITED, (event: any) => {
      const layers = event.layers;
      layers.eachLayer((layer: any) => {
        const latlngs = layer.getLatLngs()[0];
        const coordinates = latlngs.map((latlng: L.LatLng) => [latlng.lng, latlng.lat]);
        coordinates.push(coordinates[0]);
        this.polygonCoordinates.set([coordinates]);
      });
    });

    this.map.on(L.Draw.Event.DELETED, () => {
      this.currentPolygon = null;
      this.polygonCoordinates.set([]);
    });
  }

  onSave() {
    this.loading.set(true);

    if (!this.name()) {
      this.messageService.add({ 
        severity: 'error', 
        summary: 'Validation Error', 
        detail: 'Please enter a name for the plant' 
      });
      this.loading.set(false);
      return;
    }

    if (this.polygonCoordinates().length === 0) {
      this.messageService.add({ 
        severity: 'error', 
        summary: 'Validation Error', 
        detail: 'Please draw a polygon on the map to define the plant area' 
      });
      this.loading.set(false);
      return;
    }

    const plantData: Plant = {
      name: this.name(),
      geometry: {
        type: 'Polygon',
        coordinates: this.polygonCoordinates()
      }
    };

    this.plantService.createPlant(plantData).subscribe({
      next: (response) => {
        this.messageService.add({ 
          severity: 'success', 
          summary: 'Success', 
          detail: 'Plant created successfully!' 
        });
        this.loading.set(false);

        setTimeout(() => {
          this.router.navigate(['/plants']);
        }, 1500);
      },
      error: (error) => {
        console.error('Save error:', error);
        this.messageService.add({ 
          severity: 'error', 
          summary: 'Error', 
          detail: error.error?.message || 'Failed to save plant. Please try again.' 
        });
        this.loading.set(false);
      }
    });
  }

  goBack() {
    this.router.navigate(['/dashboard']);
  }

}
