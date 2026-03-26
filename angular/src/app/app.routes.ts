import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'add-plant',
    loadComponent: () => import('./addPlant/addplant.component').then(m => m.AddPlantComponent)
  },
  {
    path: 'plants',
    loadComponent: () => import('./plants/plants-list.component').then(m => m.PlantsListComponent)
  },
  {
    path: 'plants/:id',
    loadComponent: () => import('./plants/plant-detail.component').then(m => m.PlantDetailComponent)
  },
  {
    path: 'plants/:id/edit',
    loadComponent: () => import('./plants/plant-detail.component').then(m => m.PlantDetailComponent)
  },
  {
    path: 'pipeline-map',
    loadChildren: () => import('./pipeline-map/pipeline-map.routes').then(m => m.PIPELINE_MAP_ROUTES)
  },
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  }
];
