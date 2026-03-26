import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-pipeline-map-shell',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './pipeline-map-shell.component.html',
  styleUrl: './pipeline-map-shell.component.css'
})
export class PipelineMapShellComponent {}