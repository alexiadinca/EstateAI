import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, DestroyRef, ElementRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { startWith } from 'rxjs';

import { describeApiError } from '../../../core/api/api-errors';
import {
  AnalysesService,
  BuildingStructure,
  City,
  PropertyAnalysisRequest,
  PropertyCondition,
  PropertyType,
} from '../../../core/api/analyses.service';
import {
  amenityLabel,
  CONDITION_LABELS,
  floorLabel,
  NOT_STATED,
  propertyHeadline,
  STRUCTURE_LABELS,
} from '../../../shared/property-labels';
import { notBlank } from '../../../shared/validators';
import {
  AmenityChoice,
  atMostTwoDecimals,
  floorWithinBuilding,
  LIMITS,
  toAnalysisRequest,
  wholeNumber,
} from './property-form';

type CitiesState =
  | { status: 'loading' }
  | { status: 'loaded'; cities: City[] }
  | { status: 'error'; message: string };

type FieldName =
  | 'cityId'
  | 'neighborhood'
  | 'usableArea'
  | 'rooms'
  | 'floor'
  | 'totalFloors'
  | 'constructionYear'
  | 'askingPrice';

/**
 * Manual property entry in two steps: the user fills in the details, reviews them,
 * and only then saves. Values are kept when the user goes back or when saving fails.
 */
@Component({
  selector: 'app-new-property',
  imports: [ReactiveFormsModule, RouterLink, CurrencyPipe, DecimalPipe],
  templateUrl: './new-property.html',
  styleUrl: './new-property.scss',
})
export class NewProperty {
  private readonly analysesService = inject(AnalysesService);
  private readonly router = inject(Router);
  private readonly formBuilder = inject(NonNullableFormBuilder);
  private readonly elementRef = inject<ElementRef<HTMLElement>>(ElementRef);

  protected readonly limits = LIMITS;
  protected readonly structureOptions = Object.entries(STRUCTURE_LABELS) as [
    BuildingStructure,
    string,
  ][];
  protected readonly conditionOptions = Object.entries(CONDITION_LABELS) as [
    PropertyCondition,
    string,
  ][];
  protected readonly amenityChoices: { value: AmenityChoice; label: string }[] = [
    { value: 'unknown', label: NOT_STATED },
    { value: 'yes', label: 'Yes' },
    { value: 'no', label: 'No' },
  ];

  protected readonly form = this.formBuilder.group(
    {
      cityId: this.formBuilder.control<number | null>(null, Validators.required),
      neighborhood: [
        '',
        [Validators.required, notBlank, Validators.maxLength(LIMITS.neighborhoodMaxLength)],
      ],
      propertyType: this.formBuilder.control<PropertyType>('apartment'),
      usableArea: this.formBuilder.control<number | null>(null, [
        Validators.required,
        Validators.min(LIMITS.minUsableArea),
        Validators.max(LIMITS.maxUsableArea),
        atMostTwoDecimals,
      ]),
      rooms: this.formBuilder.control<number | null>(null, [
        Validators.required,
        Validators.min(1),
        Validators.max(LIMITS.maxRooms),
        wholeNumber,
      ]),
      floor: this.formBuilder.control<number | null>(null, [
        Validators.min(LIMITS.minFloor),
        Validators.max(LIMITS.maxFloors),
        wholeNumber,
      ]),
      totalFloors: this.formBuilder.control<number | null>(null, [
        Validators.min(1),
        Validators.max(LIMITS.maxFloors),
        wholeNumber,
      ]),
      constructionYear: this.formBuilder.control<number | null>(null, [
        Validators.min(LIMITS.minConstructionYear),
        Validators.max(LIMITS.maxConstructionYear),
        wholeNumber,
      ]),
      structure: this.formBuilder.control<BuildingStructure | ''>(''),
      condition: this.formBuilder.control<PropertyCondition | ''>(''),
      hasElevator: this.formBuilder.control<AmenityChoice>('unknown'),
      hasBalcony: this.formBuilder.control<AmenityChoice>('unknown'),
      hasParking: this.formBuilder.control<AmenityChoice>('unknown'),
      askingPrice: this.formBuilder.control<number | null>(null, [
        Validators.required,
        Validators.min(1),
        atMostTwoDecimals,
      ]),
    },
    { validators: floorWithinBuilding },
  );

  protected readonly citiesState = signal<CitiesState>({ status: 'loading' });
  protected readonly step = signal<'details' | 'review'>('details');
  protected readonly submitted = signal(false);
  protected readonly saving = signal(false);
  protected readonly saveError = signal<string | null>(null);
  /** The request shown on the review step and sent when the user confirms. */
  protected readonly reviewedRequest = signal<PropertyAnalysisRequest | null>(null);

  protected readonly propertyType = toSignal(
    this.form.controls.propertyType.valueChanges.pipe(
      startWith(this.form.controls.propertyType.value),
    ),
    { requireSync: true },
  );
  protected readonly isHouse = computed(() => this.propertyType() === 'house');

  protected readonly reviewedCity = computed(() => {
    const request = this.reviewedRequest();
    const citiesState = this.citiesState();
    if (!request || citiesState.status !== 'loaded') {
      return null;
    }
    return citiesState.cities.find((city) => city.city_id === request.city_id) ?? null;
  });

  // Label helpers used by the review step.
  protected readonly propertyHeadline = propertyHeadline;
  protected readonly amenityLabel = amenityLabel;
  protected readonly floorLabel = floorLabel;
  protected readonly structureLabels = STRUCTURE_LABELS;
  protected readonly conditionLabels = CONDITION_LABELS;
  protected readonly notStated = NOT_STATED;

  constructor() {
    this.loadCities();

    // The apartment floor and the lift do not apply to a house, so their fields are
    // disabled and cleared instead of keeping a hidden value.
    const { floor, hasElevator } = this.form.controls;
    this.form.controls.propertyType.valueChanges
      .pipe(takeUntilDestroyed(inject(DestroyRef)))
      .subscribe((propertyType) => {
        if (propertyType === 'house') {
          floor.reset(null);
          floor.disable();
          hasElevator.reset('unknown');
          hasElevator.disable();
        } else {
          floor.enable();
          hasElevator.enable();
        }
      });
  }

  protected loadCities(): void {
    this.citiesState.set({ status: 'loading' });
    this.analysesService.getSupportedCities().subscribe({
      next: (cities) => this.citiesState.set({ status: 'loaded', cities }),
      error: (error: HttpErrorResponse) =>
        this.citiesState.set({ status: 'error', message: describeApiError(error) }),
    });
  }

  protected showError(field: FieldName): boolean {
    const control = this.form.controls[field];
    return control.invalid && (control.touched || this.submitted());
  }

  protected hasError(field: FieldName, errorCode: string): boolean {
    return this.form.controls[field].hasError(errorCode);
  }

  protected showFloorAboveBuilding(): boolean {
    const { floor, totalFloors } = this.form.controls;
    const visited = floor.touched || totalFloors.touched || this.submitted();
    return visited && this.form.hasError('floorAboveBuilding');
  }

  protected goToReview(): void {
    this.submitted.set(true);
    this.saveError.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.focusFirstInvalidField();
      return;
    }
    this.reviewedRequest.set(toAnalysisRequest(this.form.getRawValue()));
    this.step.set('review');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  protected backToDetails(): void {
    this.step.set('details');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  protected confirmAndSave(): void {
    const request = this.reviewedRequest();
    if (!request || this.saving()) {
      return;
    }
    this.saving.set(true);
    this.saveError.set(null);
    this.analysesService.createAnalysis(request).subscribe({
      next: (analysis) => this.router.navigate(['/analyses', analysis.analysis_id]),
      error: (error: HttpErrorResponse) => {
        this.saving.set(false);
        this.saveError.set(describeSaveError(error));
      },
    });
  }

  /** Moves keyboard focus to the first field that needs a correction. */
  private focusFirstInvalidField(): void {
    // Waits one tick so the error states rendered by this submit are in the page.
    setTimeout(() => {
      this.elementRef.nativeElement.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();
    });
  }
}

/** Shows the server's validation message when it explains what to correct. */
function describeSaveError(error: HttpErrorResponse): string {
  if (error.status === 422) {
    const detail: unknown = error.error?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') {
      return `Check the details: ${detail[0].msg.replace(/^Value error, /, '')}`;
    }
    return 'Some details are not valid. Go back and check them.';
  }
  return describeApiError(error);
}
