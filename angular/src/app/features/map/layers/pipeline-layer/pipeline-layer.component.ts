import * as L from 'leaflet';

import { GemPipelineSegment, RouteSegment } from '../../models/pipeline-segments';
import { NodeMarkerUtil } from '../../utils/node-marker.util';
import { Node } from '../../models/generic-node.model';

export interface NodeTypeFilter {
    type: string;
    label: string;
    color: string;
    selected: boolean;
    count: number;
}

interface SegmentRenderConfig {
    iggielgnSegments: RouteSegment[];
    gemSegments: GemPipelineSegment[];
    maritimeSegments: RouteSegment[];
    maritimeNodes: Node[];
    showIggielgnSegments: boolean;
    showGemSegments: boolean;
    showMaritimeSegments: boolean;
    showMaritimeNodes: boolean;
}

interface MarkerRenderConfig {
    nodes: Node[];
    nodeTypes: NodeTypeFilter[];
    fitBounds: boolean;
    onMarkerClick: (node: Node) => void;
}

export class PipelineLayerComponent {
    private map: L.Map | null = null;
    private readonly markersLayer: L.LayerGroup = L.layerGroup();
    private readonly segmentsLayer: L.LayerGroup = L.layerGroup();

    /** Hooks this layer up to the map so lines and markers show up on screen. Call this first. */
    initialize(map: L.Map): void {
        this.map = map;
        this.segmentsLayer.addTo(this.map);
        this.markersLayer.addTo(this.map);
    }

    /** Wipes everything off the map — all markers and all lines. */
    clear(): void {
        this.markersLayer.clearLayers();
        this.segmentsLayer.clearLayers();
    }

    /** Draws all the pipeline lines and shipping lanes on the map based on what the user has toggled on. */
    renderSegments(config: SegmentRenderConfig): void {
        if (!this.map) {
            return;
        }

        if (config.showIggielgnSegments) {
            config.iggielgnSegments.forEach((segment) => {
                this.drawLineString(segment.geometry?.coordinates, {
                    color: '#0074D9',
                    weight: 4,
                    opacity: 0.7
                });
            });
        }

        if (config.showGemSegments) {
            config.gemSegments.forEach((segment) => {
                this.drawMultiLineString(segment.geometry.coordinates, {
                    color: '#FF4136',
                    weight: 4,
                    opacity: 0.7,
                    dashArray: '8, 8'
                });
            });
        }

        if (config.showMaritimeSegments) {
            config.maritimeSegments.forEach((segment) => {
                this.drawLineString(segment.geometry?.coordinates, {
                    color: '#FF851B',
                    weight: 3,
                    opacity: 0.6,
                    dashArray: '5, 5'
                });
            });
        }

        if (config.showMaritimeNodes) {
            config.maritimeNodes.forEach((node) => {
                const marker = NodeMarkerUtil.createNodeMarker(node).addTo(this.markersLayer);
                marker.bindPopup(`Node ID: ${node.id}`);
            });
        }
    }

    /**
     * Puts a marker on the map for each node.
     * Skips nodes with bad coordinates, filters by selected node types, and deduplicates overlapping positions.
     * If fitBounds is true, zooms the map to fit all markers.
     * Returns how many markers were actually placed.
     */
    renderMarkers(config: MarkerRenderConfig): number {
        if (!this.map) {
            return 0;
        }

        const selectedTypes = new Set(config.nodeTypes.filter((nodeType) => nodeType.selected).map((nodeType) => nodeType.type));
        const seenCoordinates = new Set<string>();
        const uniqueNodes: Node[] = [];

        for (const node of config.nodes) {
            // skip nodes that don't have valid coordinates
            if (!Number.isFinite(node.lat) || !Number.isFinite(node.lon)) {
                continue;
            }

            const nodeType = node.node_type || 'generic';
            if (selectedTypes.size > 0 && !selectedTypes.has(nodeType)) {
                continue;
            }

            // skip nodes sitting on top of each other
            const key = `${node.lat.toFixed(6)}|${node.lon.toFixed(6)}`;
            if (seenCoordinates.has(key)) {
                continue;
            }

            seenCoordinates.add(key);
            uniqueNodes.push(node);
        }

        uniqueNodes.forEach((node) => {
            const marker = NodeMarkerUtil.createNodeMarker(node).addTo(this.markersLayer);
            marker.on('click', () => config.onMarkerClick(node));
        });

        if (config.fitBounds && uniqueNodes.length > 0) {
            const bounds = L.latLngBounds(uniqueNodes.map((node) => [node.lat, node.lon] as [number, number]));
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }

        return uniqueNodes.length;
    }



    /** Draws a single continuous line from an array of [lon, lat] coordinate pairs. */
    private drawLineString(coordinates: [number, number][] | null | undefined, style: L.PolylineOptions): void {
        if (!coordinates) {
            return;
        }

        L.polyline(coordinates.map(([lon, lat]) => [lat, lon] as [number, number]), style).addTo(this.segmentsLayer);
    }

    /** Same as drawLineString but for a line that is made up of multiple separate pieces. */
    private drawMultiLineString(coordinates: [number, number][][] | null | undefined, style: L.PolylineOptions): void {
        if (!coordinates) {
            return;
        }

        coordinates.forEach((line) => {
            L.polyline(line.map(([lon, lat]) => [lat, lon] as [number, number]), style).addTo(this.segmentsLayer);
        });
    }

    private drawNodeMarker(node: Node, onClick: (node: Node) => void): void {
        const marker = NodeMarkerUtil.createNodeMarker(node).addTo(this.markersLayer);
        marker.on('click', () => onClick(node));
    }   
}