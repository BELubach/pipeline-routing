import { Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DatasetSummary } from '../models/dataset.models';
import { DatasetService } from '../services/dataset.service';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

@Component({
  selector: 'app-dataset-list.component',
  imports: [CardModule, ButtonModule, TagModule, ProgressSpinnerModule, RouterLink],
  templateUrl: './dataset-list-page.component.html',
})
export class DatasetListComponent implements OnInit {
  datasets = signal<DatasetSummary[]>([]);

  constructor(
    private datasetservice: DatasetService
  ) { }

  ngOnInit() {
    this.loadDatasets();
  }

  loadDatasets() {
    this.datasetservice.getDatasetSummaries().subscribe({
      next: (datasets) => {
        this.datasets.set(datasets);
      },
      error: (error) => {
        console.error('Error loading datasets:', error);
      }
    });
  }
}
