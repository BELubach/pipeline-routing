import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { PipelineNode } from '../../models/pipeline-node.model';

@Component({
  selector: 'app-node-selection-popover',
  standalone: true,
  imports: [CommonModule],
  styleUrl: './node-selection-popup.component.css',
  templateUrl: './node-selection-popup.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class NodeSelectionPopoverComponent {
  @Input() popupMode: 'node-info' | 'route-summary' = 'node-info';
  @Input() sourceNode?: PipelineNode;
  @Input() routeDistanceKm: number | null = null;
  @Input() routeNodes: string[] = [];
  @Output() clearRoute = new EventEmitter<void>();

  onClearRoute(): void {
    this.clearRoute.emit();
  }
}
