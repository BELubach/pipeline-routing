import { Component, OnInit, signal } from '@angular/core';
import { TitleCasePipe, DecimalPipe } from '@angular/common';
import { DatasetService } from '../services/dataset.service';
import { DatasetMetadata } from '../models/dataset.models';
import { ActivatedRoute } from '@angular/router';
import { TagModule } from 'primeng/tag';
import { CardModule } from 'primeng/card';
import { ChipModule } from 'primeng/chip';
import { DividerModule } from 'primeng/divider';
import { TableModule } from 'primeng/table';
import { BadgeModule } from 'primeng/badge';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

@Component({
  selector: 'app-dataset-detail-page.component',
  imports: [TagModule, CardModule, ChipModule, DividerModule, TableModule, BadgeModule, ProgressSpinnerModule, DecimalPipe],
  templateUrl: './dataset-detail-page.component.html',
 
})
export class DatasetDetailPageComponent implements OnInit {

  dataset = signal<DatasetMetadata | null>(null);

  constructor(
    private datasetservice: DatasetService,
    private route: ActivatedRoute,
  ) { }

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.loadDatasetDetails(params['id']);
    });
  }

  loadDatasetDetails(datasetId: string) {
    this.datasetservice.getDatasetDetails(datasetId).subscribe({
      next: (datasetDetails) => {
        this.dataset.set(datasetDetails);
        console.log('Dataset details loaded:', datasetDetails);
      },
      error: (error) => {
        console.error('Error loading dataset details:', error);
      }
    });
  }

}
