import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { User } from '../../models/user.model';

@Component({
  selector: 'app-cluster-admin-view',
  standalone: true,
  imports: [CommonModule, CardModule, TableModule, TagModule, ButtonModule],
  template: `
    <div class="space-y-6">
      <!-- Overview Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">Total Companies</p>
              <p class="text-3xl font-bold text-burgundy-900">{{ stats.totalCompanies }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-burgundy-100 flex items-center justify-center">
              <i class="pi pi-building text-burgundy-600 text-xl"></i>
            </div>
          </div>
        </p-card>

        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">Total Plants</p>
              <p class="text-3xl font-bold text-crimson-900">{{ stats.totalPlants }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-crimson-100 flex items-center justify-center">
              <i class="pi pi-shield text-crimson-600 text-xl"></i>
            </div>
          </div>
        </p-card>

        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">Active Utilities</p>
              <p class="text-3xl font-bold text-amber-900">{{ stats.activeUtilities }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center">
              <i class="pi pi-bolt text-amber-600 text-xl"></i>
            </div>
          </div>
        </p-card>

        <p-card styleClass="shadow-md border border-sand-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-stone-600 text-sm font-medium mb-1">Total Users</p>
              <p class="text-3xl font-bold text-stone-900">{{ stats.totalUsers }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center">
              <i class="pi pi-users text-stone-600 text-xl"></i>
            </div>
          </div>
        </p-card>
      </div>

      <!-- Recent Companies & Plants -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <p-card styleClass="shadow-md border border-sand-200">
          <ng-template pTemplate="header">
            <div class="px-6 pt-6 pb-4 border-b border-sand-200 flex justify-between items-center">
              <h3 class="text-lg font-semibold text-burgundy-900">All Companies</h3>
              <p-button label="View All" [text]="true" size="small"></p-button>
            </div>
          </ng-template>
          
          <p-table [value]="companies" styleClass="p-datatable-sm">
            <ng-template pTemplate="header">
              <tr>
                <th>Company</th>
                <th>Plants</th>
                <th>Status</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-company>
              <tr>
                <td>{{ company.name }}</td>
                <td>{{ company.plantCount }}</td>
                <td>
                  <p-tag 
                    [value]="company.status" 
                    [severity]="company.status === 'active' ? 'success' : 'warn'">
                  </p-tag>
                </td>
              </tr>
            </ng-template>
          </p-table>
        </p-card>

        <p-card styleClass="shadow-md border border-sand-200">
          <ng-template pTemplate="header">
            <div class="px-6 pt-6 pb-4 border-b border-sand-200 flex justify-between items-center">
              <h3 class="text-lg font-semibold text-burgundy-900">Recent Activity</h3>
            </div>
          </ng-template>
          
          <div class="space-y-3">
            @for (activity of recentActivity; track activity.id) {
              <div class="flex items-start gap-3 p-3 rounded-lg hover:bg-sand-50 transition-colors">
                <div class="w-10 h-10 rounded-full bg-burgundy-100 flex items-center justify-center flex-shrink-0">
                  <i [class]="activity.icon + ' text-burgundy-600'"></i>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-stone-900">{{ activity.title }}</p>
                  <p class="text-xs text-stone-500 mt-1">{{ activity.company }} • {{ activity.time }}</p>
                </div>
              </div>
            }
          </div>
        </p-card>
      </div>
    </div>
  `
})
export class ClusterAdminViewComponent {
  @Input() user!: User;

  // Mock data - replace with real API calls
  stats = {
    totalCompanies: 24,
    totalPlants: 156,
    activeUtilities: 4,
    totalUsers: 89
  };

  companies = [
    { name: 'TechCorp Industries', plantCount: 12, status: 'active' },
    { name: 'Green Energy Ltd', plantCount: 8, status: 'active' },
    { name: 'Prime Manufacturing', plantCount: 15, status: 'active' },
    { name: 'Urban Solutions', plantCount: 6, status: 'maintenance' }
  ];

  recentActivity = [
    { id: 1, icon: 'pi pi-plus', title: 'New plant registered', company: 'TechCorp Industries', time: '2 hours ago' },
    { id: 2, icon: 'pi pi-building', title: 'Company created', company: 'New Ventures Inc', time: '5 hours ago' },
    { id: 3, icon: 'pi pi-bolt', title: 'Utility connection updated', company: 'Green Energy Ltd', time: '1 day ago' }
  ];
}
