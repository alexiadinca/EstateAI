import { Component, input } from '@angular/core';

import { FieldOrigin } from '../core/api/analyses.service';

export const ORIGIN_LABELS: Record<FieldOrigin, string> = {
  listing: 'From listing',
  description: 'From description',
  corrected: 'Corrected',
};

/**
 * Small label showing where a value came from. Nothing is shown for manually entered values,
 * so imported, described and corrected values stand out without cluttering the form.
 */
@Component({
  selector: 'app-origin-tag',
  template: `
    @if (origin(); as current) {
      <span class="origin-tag" [class]="'origin-tag--' + current">{{ labels[current] }}</span>
    }
  `,
  styles: `
    .origin-tag {
      display: inline-block;
      margin-left: var(--space-2);
      padding: 0.05rem 0.5rem;
      border-radius: 999px;
      font-size: 0.6875rem;
      font-weight: 500;
      letter-spacing: 0.02em;
      vertical-align: middle;
      white-space: nowrap;
    }

    .origin-tag--listing {
      color: var(--color-primary);
      background: var(--color-surface-tinted);
    }

    .origin-tag--description {
      color: var(--color-text);
      background: var(--color-surface-muted);
      border: var(--border-width) dashed var(--color-accent);
    }

    .origin-tag--corrected {
      color: var(--color-success);
      background: var(--color-success-surface);
    }
  `,
})
export class OriginTag {
  readonly origin = input<FieldOrigin | null | undefined>(null);
  protected readonly labels = ORIGIN_LABELS;
}
