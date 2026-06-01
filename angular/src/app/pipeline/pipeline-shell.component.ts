import { Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';

@Component({
  selector: 'app-pipeline-shell',
  imports: [RouterLink, RouterLinkActive, RouterOutlet, ButtonModule, DialogModule, InputTextModule],
  templateUrl: './pipeline-shell.component.html',
  styleUrl: './pipeline-shell.component.css'
})
export class PipelineShellComponent {
  protected readonly shellDialogVisible = signal(false);

  protected openShellDialog(): void {
    this.shellDialogVisible.set(true);
  }

  protected closeShellDialog(): void {
    this.shellDialogVisible.set(false);
  }

  protected saveShellDialog(): void {
    this.shellDialogVisible.set(false);
  }
}