/**
 * Component Types
 *
 * Type definitions for React components.
 */

import type { ReactNode, ComponentPropsWithoutRef } from 'react';

// =============================================================================
// Base Component Props
// =============================================================================

/** Base props with children */
export interface PropsWithChildren {
  children: ReactNode;
}

/** Base props with optional children */
export interface PropsWithOptionalChildren {
  children?: ReactNode;
}

/** Base props with className */
export interface PropsWithClassName {
  className?: string;
}

/** Combined base props */
export interface BaseComponentProps extends PropsWithOptionalChildren, PropsWithClassName {}

// =============================================================================
// Button Props
// =============================================================================

/** Button variant */
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'link';

/** Button size */
export type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';

/** Button props */
export interface ButtonProps extends ComponentPropsWithoutRef<'button'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

// =============================================================================
// Input Props
// =============================================================================

/** Input size */
export type InputSize = 'sm' | 'md' | 'lg';

/** Input props */
export interface InputProps extends ComponentPropsWithoutRef<'input'> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  inputSize?: InputSize;
}

// =============================================================================
// Layout Props
// =============================================================================

/** Container size */
export type ContainerSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

/** Container props */
export interface ContainerProps extends BaseComponentProps {
  size?: ContainerSize;
  as?: 'div' | 'section' | 'main' | 'article';
}

/** Stack direction */
export type StackDirection = 'horizontal' | 'vertical';

/** Stack spacing */
export type StackSpacing = 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/** Stack props */
export interface StackProps extends BaseComponentProps {
  direction?: StackDirection;
  spacing?: StackSpacing;
  align?: 'start' | 'center' | 'end' | 'stretch';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
  wrap?: boolean;
}

// =============================================================================
// Card Props
// =============================================================================

/** Card variant */
export type CardVariant = 'default' | 'glass' | 'elevated' | 'outlined';

/** Card props */
export interface CardProps extends BaseComponentProps {
  variant?: CardVariant;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  clickable?: boolean;
  onClick?: () => void;
}

// =============================================================================
// Badge Props
// =============================================================================

/** Badge variant */
export type BadgeVariant = 'success' | 'danger' | 'warning' | 'neutral' | 'primary' | 'accent';

/** Badge size */
export type BadgeSize = 'sm' | 'md' | 'lg';

/** Badge props */
export interface BadgeProps extends BaseComponentProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
}

// =============================================================================
// Modal Props
// =============================================================================

/** Modal size */
export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

/** Modal props */
export interface ModalProps extends PropsWithChildren {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  size?: ModalSize;
  closeOnOverlayClick?: boolean;
  showCloseButton?: boolean;
}

// =============================================================================
// Toast Props
// =============================================================================

/** Toast variant */
export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

/** Toast props */
export interface ToastProps {
  id: string;
  variant: ToastVariant;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// =============================================================================
// Progress Props
// =============================================================================

/** Progress variant */
export type ProgressVariant = 'default' | 'gradient' | 'success' | 'danger' | 'warning';

/** Progress props */
export interface ProgressProps extends PropsWithClassName {
  value: number;
  max?: number;
  variant?: ProgressVariant;
  size?: 'sm' | 'md' | 'lg';
  showValue?: boolean;
  animated?: boolean;
}

// =============================================================================
// Table Props
// =============================================================================

/** Table column */
export interface TableColumn<T> {
  key: keyof T | string;
  header: string;
  width?: string | number;
  sortable?: boolean;
  render?: (row: T, index: number) => ReactNode;
}

/** Table props */
export interface TableProps<T> extends PropsWithClassName {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: T, index: number) => void;
  sortBy?: string;
  sortDirection?: 'asc' | 'desc';
  onSort?: (key: string) => void;
}

// =============================================================================
// Dropdown Props
// =============================================================================

/** Dropdown item */
export interface DropdownItem {
  key: string;
  label: string;
  icon?: ReactNode;
  disabled?: boolean;
  danger?: boolean;
  divider?: boolean;
}

/** Dropdown props */
export interface DropdownProps extends PropsWithClassName {
  trigger: ReactNode;
  items: DropdownItem[];
  onSelect: (key: string) => void;
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end';
}

// =============================================================================
// Tooltip Props
// =============================================================================

/** Tooltip props */
export interface TooltipProps extends PropsWithChildren {
  content: ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
}

// =============================================================================
// Analysis Component Props
// =============================================================================

/** Upload zone props */
export interface UploadZoneProps extends PropsWithClassName {
  onFilesSelected: (files: File[]) => void;
  accept?: string[];
  maxSize?: number;
  maxFiles?: number;
  disabled?: boolean;
}

/** Result card props */
export interface ResultCardProps {
  prediction: 'real' | 'fake' | 'uncertain';
  confidence: number;
  showDetails?: boolean;
}

/** Frame viewer props */
export interface FrameViewerProps extends PropsWithClassName {
  frames: Array<{
    frameNumber: number;
    imageUrl: string;
    prediction: 'real' | 'fake';
    confidence: number;
    heatmapUrl?: string;
  }>;
  selectedFrame?: number;
  onFrameSelect?: (frameNumber: number) => void;
  showHeatmap?: boolean;
}

// =============================================================================
// Chart Props
// =============================================================================

/** Chart data point */
export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: string | number;
}

/** Line chart props */
export interface LineChartProps extends PropsWithClassName {
  data: ChartDataPoint[];
  xKey: string;
  yKey: string;
  height?: number;
  showGrid?: boolean;
  showTooltip?: boolean;
}

/** Pie chart props */
export interface PieChartProps extends PropsWithClassName {
  data: ChartDataPoint[];
  height?: number;
  innerRadius?: number;
  showLabels?: boolean;
}
