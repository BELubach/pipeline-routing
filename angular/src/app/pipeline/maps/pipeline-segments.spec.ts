import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PipelineSegments } from './pipeline-segments';

describe('PipelineSegments', () => {
  let component: PipelineSegments;
  let fixture: ComponentFixture<PipelineSegments>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PipelineSegments],
    }).compileComponents();

    fixture = TestBed.createComponent(PipelineSegments);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
