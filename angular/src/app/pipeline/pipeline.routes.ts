import { Routes } from '@angular/router';

export const PIPELINE_ROUTES: Routes = [
    {
        path: '',
        loadComponent: () => import('./pipeline-shell.component').then((m) => m.PipelineShellComponent),
        children: [
            {
                path: '',
                redirectTo: 'network',
                pathMatch: 'full'
            },
            {
                path: 'network',
                loadComponent: () => import('../features/map/components/map-view/map-view.component').then((m) => m.MapViewComponent)
            },
            {
                path: 'gem-segments',
                loadComponent: () => import('../features/map/components/map-view/map-view.component').then((m) => m.MapViewComponent)
            }
        ]
    }
];