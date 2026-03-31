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
                loadComponent: () => import('./maps/pipeline-map.component').then((m) => m.PipelineMapComponent)
            },
            {
                path: 'border-crossings',
                loadComponent: () => import('./maps/border-crossings.component').then((m) => m.BorderCrossingsComponent)
            },
            {
                path: 'segments',
                loadComponent: () => import('./maps/pipeline-segments').then((m) => m.PipelineSegments)
            }
        ]
    }
];