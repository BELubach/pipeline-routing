import { ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import * as L from 'leaflet';

import { DataSelectComponent } from '../map-legend/data-select-component';
import { CustomBoxComponent } from '../map-legend/custom-box.component';
@Component({
  selector: 'app-map-view',
  standalone: true,
  imports: [DataSelectComponent, CustomBoxComponent],
  templateUrl: './map-view.component.html',
  styleUrl: './map-view.component.css'
})
export class MapViewComponent implements OnInit, OnDestroy {
  private map: L.Map | null = null;

  readonly legendVisibility = {
    showIggielgnSegments: true,
    showGemSegments: true,
    showShippingLanes: true,
    showGenericNodes: true,
    showLngNodes: true,
    showBorderNodes: true

  };

  ngOnInit(): void {
    this.initMap();
  }

  private initMap(): void {
    this.map = L.map('map', {
      center: [45.0, 10.0],
      zoom: 4
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    queueMicrotask(() => this.map?.invalidateSize());
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }
}
