import { Component, EventEmitter, Input, Output } from "@angular/core";
import { RouteResponse } from "../../models/pipeline-segments";

@Component({
    selector: 'app-current-route',
    template: `<div class="current-route">
        <h3>Current Route</h3>
        @if (route) {
                        <p><strong>Source:</strong> {{ sourceName }}</p>
                        <p><strong>Target:</strong> {{ targetName }}</p>
                        <p><strong>Total Distance:</strong> {{ route.total_distance_km.toFixed(2) }} km</p>
                        <button type="button" class="current-route__clear" (click)="clearRoute.emit()">Clear route</button>
                } @else {
                        <p>Select start and end nodes to load a route.</p>
        }
       </div>`,
    styleUrls: ['./current-route.component.css']
})
export class CurrentRouteComponent {
    @Input() route: RouteResponse | null = null;
        @Input() sourceName = '';
        @Input() targetName = '';
        @Output() clearRoute = new EventEmitter<void>();
}