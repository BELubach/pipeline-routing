import { Routes } from '@angular/router';

export const PIPELINE_MAP_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./pipeline-map-shell.component').then(m => m.PipelineMapShellComponent),
    children: [
      {
        path: '',
        redirectTo: 'network',
        pathMatch: 'full'
      },
      {
        path: 'network',
        loadComponent: () => import('./pipeline-map.component').then(m => m.PipelineMapComponent)
      },
      {
        path: 'border-crossings',
        loadComponent: () => import('./border-crossings.component').then(m => m.BorderCrossingsComponent)
      }
    ]
  }
];