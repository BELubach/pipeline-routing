import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { User } from '../../models/user.model';

@Component({
  selector: 'app-company-owner-view',
  standalone: true,
  imports: [CommonModule, CardModule, TableModule, TagModule, ButtonModule],
  template: `
    <div class="space-y-6">
      <!-- Company Overview -->
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-burgundy-900 mb-2">{{ user.company_name }}</h2>
        <p class="text-stone-600">Manage your plants and view public GIS connections</p>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">My Plants</p>
              <p class="text-3xl font-bold text-burgundy-900">{{ stats.myPlants }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-burgundy-100 flex items-center justify-center">
              <i class="pi pi-shield text-burgundy-600 text-xl"></i>
            </div>
          </div>
        </p-card>

        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">Active Plants</p>
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
              <p class="text-stone-600 text-sm font-medium mb-1">GIS Connections</p>
              <p class="text-3xl font-bold text-amber-900">{{ stats.gisConnections }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center">
              <i class="pi pi-map text-amber-600 text-xl"></i>
            </div>
          </div>
        </p-card>
      </div>

      <!-- My Plants & Public GIS -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <p-card styleClass="shadow-md border border-sand-200">
          <ng-template pTemplate="header">
            <div class="px-6 pt-6 pb-4 border-b border-sand-200 flex justify-between items-center">
              <h3 class="text-lg font-semibold text-burgundy-900">My Plants</h3>
              <p-button label="Add Plant" icon="pi pi-plus" size="small"></p-button>
            </div>
          </ng-template>
          
          <p-table [value]="plants" styleClass="p-datatable-sm">
            <ng-template pTemplate="header">
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-plant>
              <tr>
                <td>{{ plant.name }}</td>
                <td>{{ plant.type }}</td>
                <td>
                  <p-tag 
                    [value]="plant.status" 
                    [severity]="plant.status === 'active' ? 'success' : plant.status === 'maintenance' ? 'warn' : 'danger'">
                  </p-tag>
                </td>
              </tr>
            </ng-template>
          </p-table>
        </p-card>

        <p-card styleClass="shadow-md border border-sand-200">
          <ng-template pTemplate="header">
            <div class="px-6 pt-6 pb-4 border-b border-sand-200 flex justify-between items-center">
              <h3 class="text-lg font-semibold text-burgundy-900">Public GIS Connections</h3>
              <p-button label="View Map" icon="pi pi-map-marker" [text]="true" size="small"></p-button>
            </div>
          </ng-template>
          
          <div class="space-y-3">
            @for (gis of publicGIS; track gis.id) {
              <div class="flex items-start gap-3 p-3 rounded-lg hover:bg-sand-50 transition-colors border border-sand-100">
                <div class="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <i class="pi pi-map text-amber-600"></i>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-stone-900">{{ gis.name }}</p>
                  <p class="text-xs text-stone-500 mt-1">{{ gis.type }} • {{ gis.provider }}</p>
                </div>
                <p-button icon="pi pi-external-link" [text]="true" size="small"></p-button>
              </div>
            }
          </div>
        </p-card>
      </div>
    </div>
  `
})
export class CompanyOwnerViewComponent {
  @Input() user!: User;

  // Mock data - replace with real API calls
  stats = {
    myPlants: 12,
    activePlants: 10,
    gisConnections: 5
  };

  plants = [
    { name: 'Main Production Plant', type: 'Electricity', status: 'active' },
    { name: 'Heating Facility North', type: 'Heating', status: 'active' },
    { name: 'Water Treatment #1', type: 'Water', status: 'maintenance' },
    { name: 'Gas Distribution Hub', type: 'Gas', status: 'active' }
  ];

  publicGIS = [
    { id: 1, name: 'City Power Grid', type: 'Electricity', provider: 'Municipal Authority' },
    { id: 2, name: 'Regional Gas Network', type: 'Gas', provider: 'Gas Corp' },
    { id: 3, name: 'Water Supply Map', type: 'Water', provider: 'Water Services' }
  ];
}
