import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { User } from '../../models/user.model';

@Component({
  selector: 'app-utility-provider-view',
  standalone: true,
  imports: [CommonModule, CardModule, TableModule, TagModule, ButtonModule],
  template: `
    <div class="space-y-6">
      <!-- Utility Provider Overview -->
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-burgundy-900 mb-2">{{ user.utility_provider_name }}</h2>
        <p class="text-stone-600">{{ getUtilityTypeDisplay() }} Infrastructure Dashboard</p>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">Total Plants</p>
              <p class="text-3xl font-bold text-burgundy-900">{{ stats.totalPlants }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-burgundy-100 flex items-center justify-center">
              <i [class]="getUtilityIcon() + ' text-burgundy-600 text-xl'"></i>
            </div>
          </div>
        </p-card>

        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">Active</p>
              <p class="text-3xl font-bold text-crimson-900">{{ stats.activePlants }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-crimson-100 flex items-center justify-center">
              <i class="pi pi-check-circle text-crimson-600 text-xl"></i>
            </div>
          </div>
        </p-card>

        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">Maintenance</p>
              <p class="text-3xl font-bold text-amber-900">{{ stats.maintenancePlants }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center">
              <i class="pi pi-wrench text-amber-600 text-xl"></i>
            </div>
          </div>
        </p-card>

        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">Total Capacity</p>
              <p class="text-3xl font-bold text-stone-900">{{ stats.totalCapacity }}</p>
              <p class="text-xs text-stone-500">{{ getCapacityUnit() }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center">
              <i class="pi pi-chart-line text-stone-600 text-xl"></i>
            </div>
          </div>
        </p-card>
      </div>

      <!-- All Plants for This Utility Type -->
      <p-card styleClass="shadow-md border border-sand-200">
        <ng-template pTemplate="header">
          <div class="px-6 pt-6 pb-4 border-b border-sand-200 flex justify-between items-center">
            <h3 class="text-lg font-semibold text-burgundy-900">
              All {{ getUtilityTypeDisplay() }} Plants
            </h3>
            <div class="flex gap-2">
              <p-button label="Export" icon="pi pi-download" [outlined]="true" size="small"></p-button>
              <p-button label="View Map" icon="pi pi-map-marker" size="small"></p-button>
            </div>
          </div>
        </ng-template>
        
        <p-table [value]="plants" styleClass="p-datatable-sm" [paginator]="true" [rows]="10">
          <ng-template pTemplate="header">
            <tr>
              <th>Plant Name</th>
              <th>Company</th>
              <th>Location</th>
              <th>Capacity</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </ng-template>
          <ng-template pTemplate="body" let-plant>
            <tr>
              <td>{{ plant.name }}</td>
              <td>{{ plant.company }}</td>
              <td>{{ plant.location }}</td>
              <td>{{ plant.capacity }} {{ getCapacityUnit() }}</td>
              <td>
                <p-tag 
                  [value]="plant.status" 
                  [severity]="plant.status === 'active' ? 'success' : plant.status === 'maintenance' ? 'warn' : 'danger'">
                </p-tag>
              </td>
              <td>
                <p-button icon="pi pi-eye" [text]="true" size="small"></p-button>
              </td>
            </tr>
          </ng-template>
        </p-table>
      </p-card>
    </div>
  `
})
export class UtilityProviderViewComponent {
  @Input() user!: User;

  // Mock data - replace with real API calls
  stats = {
    totalPlants: 48,
    activePlants: 42,
    maintenancePlants: 6,
    totalCapacity: 2850
  };

  plants = [
    { name: 'North District Plant', company: 'TechCorp Industries', location: 'District 1', capacity: 250, status: 'active' },
    { name: 'Central Hub Facility', company: 'Green Energy Ltd', location: 'Downtown', capacity: 420, status: 'active' },
    { name: 'South Production Unit', company: 'Prime Manufacturing', location: 'Industrial Zone', capacity: 180, status: 'maintenance' },
    { name: 'East Distribution Center', company: 'Urban Solutions', location: 'East Side', capacity: 310, status: 'active' },
    { name: 'West Regional Plant', company: 'TechCorp Industries', location: 'West End', capacity: 275, status: 'active' }
  ];

  getUtilityTypeDisplay(): string {
    const type = this.user.utility_type || 'utility';
    return type.charAt(0).toUpperCase() + type.slice(1);
  }

  getUtilityIcon(): string {
    switch(this.user.utility_type) {
      case 'electricity': return 'pi pi-bolt';
      case 'gas': return 'pi pi-circle';
      case 'water': return 'pi pi-droplet';
      case 'heating': return 'pi pi-sun';
      default: return 'pi pi-shield';
    }
  }

  getCapacityUnit(): string {
    switch(this.user.utility_type) {
      case 'electricity': return 'MW';
      case 'gas': return 'm³/h';
      case 'water': return 'm³/h';
      case 'heating': return 'MW';
      default: return 'units';
    }
  }
}
