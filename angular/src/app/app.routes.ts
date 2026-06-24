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
    path: 'pipeline-map',
    loadComponent: () => import('./features/map/components/map-view/map-view.component').then((m) => m.MapViewComponent)
  },
  {
    path: "datasets",
    loadComponent: () => import('./datasets/dataset-list-page/dataset-list-page.component').then((m) => m.DatasetListComponent)
  },
  {
    path: "datasets/:id",
    loadComponent: () => import('./datasets/dataset-detail-page/dataset-detail-page.component').then((m) => m.DatasetDetailPageComponent)
  },
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  }
];
