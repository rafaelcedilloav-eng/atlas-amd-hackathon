declare module "react-simple-maps" {
  import { ComponentType, ReactNode, CSSProperties, MouseEvent } from "react";

  interface GeographyStyle {
    default?: CSSProperties;
    hover?: CSSProperties;
    pressed?: CSSProperties;
  }

  interface GeographyProps {
    geography: {
      rsmKey: string;
      id?: string | number;
      properties?: Record<string, unknown>;
      [key: string]: unknown;
    };
    style?: GeographyStyle;
    onMouseEnter?: (event: MouseEvent) => void;
    onMouseLeave?: (event: MouseEvent) => void;
    onClick?: (event: MouseEvent) => void;
    className?: string;
  }

  interface GeographiesProps {
    geography: string | object;
    children: (props: { geographies: GeographyProps["geography"][] }) => ReactNode;
    parseGeographies?: (data: unknown) => unknown[];
  }

  interface ComposableMapProps {
    projection?: string;
    projectionConfig?: {
      scale?: number;
      center?: [number, number];
      rotate?: [number, number, number];
      parallels?: [number, number];
    };
    style?: CSSProperties;
    width?: number;
    height?: number;
    className?: string;
    children?: ReactNode;
  }

  interface ZoomableGroupProps {
    center?: [number, number];
    zoom?: number;
    minZoom?: number;
    maxZoom?: number;
    translateExtent?: [[number, number], [number, number]];
    onMoveStart?: (pos: { coordinates: [number, number]; zoom: number }) => void;
    onMove?: (pos: { coordinates: [number, number]; zoom: number; x: number; y: number; dragging: boolean }) => void;
    onMoveEnd?: (pos: { coordinates: [number, number]; zoom: number }) => void;
    children?: ReactNode;
  }

  export const ComposableMap: ComponentType<ComposableMapProps>;
  export const Geographies: ComponentType<GeographiesProps>;
  export const Geography: ComponentType<GeographyProps>;
  export const ZoomableGroup: ComponentType<ZoomableGroupProps>;
}
