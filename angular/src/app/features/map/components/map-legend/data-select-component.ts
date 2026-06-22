import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';


export interface LegendVisibility {
    showIggielgnSegments: boolean;
    showGemSegments: boolean;
    showShippingLanes: boolean;
    showGenericNodes: boolean;
    showLngNodes: boolean;
    showBorderNodes: boolean;
}


@Component({
    selector: 'app-data-select',
    standalone: true,
    imports: [FormsModule],
    templateUrl: './data-select-component.html'
})
export class DataSelectComponent {
    @Input() visibility: LegendVisibility = {
        showIggielgnSegments: true,
        showGemSegments: true,
        showShippingLanes: true, 
        showGenericNodes: true, 
        showLngNodes: true,
        showBorderNodes: true
    };
    @Input() iggielgnCount = 0;
    @Input() gemCount = 0;
    @Input() shippingLaneCount = 0;

    @Output() visibilityChanged = new EventEmitter<LegendVisibility>();


    onVisibilityChanged(): void {
        this.visibilityChanged.emit(this.visibility);
    }

}