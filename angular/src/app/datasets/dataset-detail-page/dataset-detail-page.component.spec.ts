import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DatasetDetailPageComponent } from './dataset-detail-page.component';

describe('DatasetDetailPageComponent', () => {
  let component: DatasetDetailPageComponent;
  let fixture: ComponentFixture<DatasetDetailPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DatasetDetailPageComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DatasetDetailPageComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
