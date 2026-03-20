import { Component, OnInit, signal, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
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
  selector: 'app-plant-detail',
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
  templateUrl: './plant-detail.component.html',
  styleUrl: './plant-detail.component.css'
})
export class PlantDetailComponent implements OnInit, AfterViewInit, OnDestroy {
  plant = signal<Plant | null>(null);
  plantName = signal('');
  loading = signal(true);
  isEditMode = signal(false);
  plantId: number | null = null;
  
  private map: L.Map | null = null;
  private drawnItems: L.FeatureGroup | null = null;
  private currentPolygon: L.Polygon | null = null;

  constructor(
    private plantService: PlantService,
    private route: ActivatedRoute,
    private router: Router,
    private messageService: MessageService
  ) { }

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.plantId = +params['id'];
      
      // Check if we're in edit mode from the URL
      this.isEditMode.set(this.route.snapshot.url.some(segment => segment.path === 'edit'));
      
      this.loadPlant();
    });
  }

  ngAfterViewInit() {
    setTimeout(() => {
      this.initMap();
    }, 100);
  }

  ngOnDestroy() {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }

  loadPlant() {
    if (this.plantId) {
      this.loading.set(true);
      this.plantService.getPlantById(this.plantId).subscribe({
        next: (plant) => {
          this.plant.set(plant);
          this.plantName.set(plant.name);
          this.loading.set(false);
          
          // Update map with plant geometry if map is ready
          if (this.map) {
            this.displayPlantGeometry(plant);
          }
        },
        error: (error) => {
          console.error('Error loading plant:', error);
          this.messageService.add({ 
            severity: 'error', 
            summary: 'Error', 
            detail: 'Failed to load plant details' 
          });
          this.loading.set(false);
        }
      });
    }
  }

  initMap() {
    // Initialize map
    this.map = L.map('map').setView([51.505, -0.09], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    this.drawnItems = new L.FeatureGroup();
    this.map.addLayer(this.drawnItems);

    // Display plant geometry if already loaded
    const currentPlant = this.plant();
    if (currentPlant) {
      this.displayPlantGeometry(currentPlant);
    }

    // Only enable drawing controls if in edit mode
    if (this.isEditMode()) {
      const drawControl = new L.Control.Draw({
        edit: {
          featureGroup: this.drawnItems
        },
        draw: {
          polygon: {},
          polyline: false,
          rectangle: false,
          circle: false,
          marker: false,
          circlemarker: false
        }
      });
      this.map.addControl(drawControl);

      // Handle drawing events
      this.map.on(L.Draw.Event.CREATED, (event: any) => {
        const layer = event.layer;
        
        // Remove existing polygon if any
        if (this.currentPolygon) {
          this.drawnItems?.removeLayer(this.currentPolygon);
        }
        
        this.drawnItems?.addLayer(layer);
        this.currentPolygon = layer;
      });
    }
  }

  displayPlantGeometry(plant: Plant) {
    if (!this.map || !this.drawnItems) return;

    // Clear existing layers
    this.drawnItems.clearLayers();

    if (plant.geometry && plant.geometry.coordinates) {
      // Convert GeoJSON coordinates to Leaflet LatLng
      const coordinates = plant.geometry.coordinates[0].map(coord => 
        L.latLng(coord[1], coord[0]) as L.LatLngExpression
      );

      this.currentPolygon = L.polygon(coordinates, {
        color: this.isEditMode() ? 'blue' : 'green',
        fillColor: this.isEditMode() ? '#3388ff' : '#30a530',
        fillOpacity: 0.4
      });

      this.drawnItems.addLayer(this.currentPolygon);
      this.map.fitBounds(this.currentPolygon.getBounds());
    }
  }

  toggleEditMode() {
    this.isEditMode.set(!this.isEditMode());
    
    // Reinitialize map when toggling edit mode
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
    
    setTimeout(() => {
      this.initMap();
    }, 100);
  }

  onUpdate() {
    if (!this.plantId) return;

    const updateData: Partial<Plant> = {
      name: this.plantName()
    };

    // If we have a drawn polygon, include the geometry
    if (this.currentPolygon && this.isEditMode()) {
      const latLngs = (this.currentPolygon.getLatLngs()[0] as L.LatLng[]);
      const coordinates = latLngs.map(latLng => [latLng.lng, latLng.lat]);
      
      updateData.geometry = {
        type: 'Polygon',
        coordinates: [coordinates]
      };
    }

    this.plantService.updatePlant(this.plantId, updateData).subscribe({
      next: (updatedPlant) => {
        this.plant.set(updatedPlant);
        this.messageService.add({ 
          severity: 'success', 
          summary: 'Success', 
          detail: 'Plant updated successfully' 
        });
        this.isEditMode.set(false);
        
        // Reinitialize map to show updated geometry in view mode
        if (this.map) {
          this.map.remove();
          this.map = null;
        }
        setTimeout(() => {
          this.initMap();
        }, 100);
      },
      error: (error) => {
        console.error('Error updating plant:', error);
        this.messageService.add({ 
          severity: 'error', 
          summary: 'Error', 
          detail: 'Failed to update plant' 
        });
      }
    });
  }

  goBack() {
    this.router.navigate(['/plants']);
  }
}
