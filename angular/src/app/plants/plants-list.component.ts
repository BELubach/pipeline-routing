import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmationService, MessageService } from 'primeng/api';
import { PlantService } from '../services/plant.service';
import { Plant } from '../models/plant.model';

@Component({
  selector: 'app-plants-list',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    TableModule,
    TagModule,
    ConfirmDialogModule,
    ToastModule
  ],
  providers: [ConfirmationService, MessageService],
  templateUrl: './plants-list.component.html',
  styleUrl: './plants-list.component.css'
})
export class PlantsListComponent implements OnInit {
  plants = signal<Plant[]>([]);
  loading = signal(true);

  constructor(
    private plantService: PlantService,
    private router: Router,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) { }

  ngOnInit() {
    this.loadPlants();
  }

  loadPlants() {
    this.loading.set(true);
    this.plantService.getAllPlants().subscribe({
      next: (plants) => {
        this.plants.set(plants);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Error loading plants:', error);
        this.messageService.add({ 
          severity: 'error', 
          summary: 'Error', 
          detail: 'Failed to load plants' 
        });
        this.loading.set(false);
      }
    });
  }

  viewPlant(plant: Plant) {
    if (plant.id) {
      this.router.navigate(['/plants', plant.id]);
    }
  }

  editPlant(plant: Plant) {
    if (plant.id) {
      this.router.navigate(['/plants', plant.id, 'edit']);
    }
  }

  deletePlant(plant: Plant) {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete ${plant.name}?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        if (plant.id) {
          this.plantService.deletePlant(plant.id).subscribe({
            next: () => {
              this.messageService.add({ 
                severity: 'success', 
                summary: 'Success', 
                detail: 'Plant deleted successfully' 
              });
              this.loadPlants();
            },
            error: (error) => {
              console.error('Error deleting plant:', error);
              this.messageService.add({ 
                severity: 'error', 
                summary: 'Error', 
                detail: 'Failed to delete plant' 
              });
            }
          });
        }
      }
    });
  }

  goToAddPlant() {
    this.router.navigate(['/add-plant']);
  }

  goToDashboard() {
    this.router.navigate(['/dashboard']);
  }
}
