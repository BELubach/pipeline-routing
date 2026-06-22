import { Component, EventEmitter, Input, Output } from "@angular/core";
import { RouteResponse } from "../../models/pipeline-segments";

@Component({
    selector: 'app-current-route',
    template: `<div class="card border rounded p-6 m-4">
            <div class="card-title text-lg font-bold">
            <h3>Current Route</h3>

      </div>
        <div class="card-content ">

        @if (route) {
                <p><strong>Source:</strong> {{ sourceName }}</p>
                <p><strong>Target:</strong> {{ targetName }}</p>
                <p><strong>Total Distance:</strong> {{ route.total_distance_km.toFixed(2) }} km</p>
                <button type="button" class="button text-white bg-red-800 rounded px-2 hover:bg-red-700 hover:cursor-pointer" (click)="clearRoute.emit()">Clear route</button>
        } @else {
                <p>Select start and end nodes to load a route.</p>
        }
        
      </div>
       </div>`,
})
export class CurrentRouteComponent {
    @Input() route: RouteResponse | null = null;
    @Input() sourceName = '';
    @Input() targetName = '';
    @Output() clearRoute = new EventEmitter<void>();
}