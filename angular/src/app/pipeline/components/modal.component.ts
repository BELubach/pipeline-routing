

import { Component, input, output } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';

@Component({
    selector: 'app-modal',
    imports: [ButtonModule, DialogModule],
    templateUrl: './modal.component.html',
    styleUrl: './modal.component.css'
})
export class ModalComponent {
    readonly title = input('Dialog');
    readonly visible = input(false);
    readonly width = input('25rem');
    readonly cancelLabel = input('Cancel');
    readonly confirmLabel = input('Save');

    readonly visibleChange = output<boolean>();
    readonly cancel = output<void>();
    readonly confirm = output<void>();

    onVisibleChange(visible: boolean): void {
        this.visibleChange.emit(visible);
    }

    onCancel(): void {
        this.cancel.emit();
        this.visibleChange.emit(false);
    }

    onConfirm(): void {
        this.confirm.emit();
        this.visibleChange.emit(false);
    }
}