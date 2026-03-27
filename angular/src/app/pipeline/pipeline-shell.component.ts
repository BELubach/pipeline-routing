import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-pipeline-shell',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './pipeline-shell.component.html',
  styleUrl: './pipeline-shell.component.css'
})
export class PipelineShellComponent {}