import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { BorderNode } from '../models/border-node.model';
import { NodeId, PipelineNode, ReachableNodesResponse } from '../models/pipeline-node.model';
import { GemPipelineSegment, PipelineSegment, RouteResponse, ShippingLane } from '../models/pipeline-segments';

interface RawRoutePathStep {
  seq: number;
  node_id: NodeId;
  node_name: string;
  edge_id: number;
  distance_km: number | null;
  total_distance: number;
}

interface RawRouteGeometryStep {
  seq: number;
  edge_id: number;
  start_node: NodeId;
  end_node: NodeId;
  distance_km: number | null;
  total_distance: number;
  geometry: {
    type: 'LineString';
    coordinates: [number, number][];
  } | null;
}

@Injectable({
  providedIn: 'root'
})
export class PipelineService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1';

  getNodes(): Observable<PipelineNode[]> {
    return this.http.get<{ metadata: any; data: PipelineNode[] }>(`${this.apiUrl}/iggielgn/nodes-unified`)
      .pipe(map(res => res.data));
  }


  getBorderCrossings(): Observable<BorderNode[]> {
    return this.http.get<BorderNode[]>(`${this.apiUrl}/pipelines/border-crossings`);
  }

  getPipelineSegments(): Observable<PipelineSegment[]> {
    return this.http
      .get<{ metadata: any; data: PipelineSegment[] }>(`${this.apiUrl}/iggielgn/segments`)
      .pipe(map(res => res.data));
  }

  getGemSegments(): Observable<GemPipelineSegment[]> {
    return this.http
      .get<{ metadata: any; data: GemPipelineSegment[] }>(`${this.apiUrl}/gem/segments`)
      .pipe(map(res => res.data));
  }

  getRoute(sourceNodeId: NodeId, targetNodeId: NodeId): Observable<RouteResponse> {
    return this.http
      .get<{
        metadata?: any;
        data?: RouteResponse | RawRoutePathStep[] | RawRouteGeometryStep[];
      } | RouteResponse | RawRoutePathStep[] | RawRouteGeometryStep[]>(
        `${this.apiUrl}/routes/path/${sourceNodeId}/${targetNodeId}`
      )
      .pipe(map((res) => this.normalizeRouteResponse(res, sourceNodeId, targetNodeId)));
  }

  private normalizeRouteResponse(
    response: { metadata?: any; data?: RouteResponse | RawRoutePathStep[] | RawRouteGeometryStep[] } | RouteResponse | RawRoutePathStep[] | RawRouteGeometryStep[],
    sourceNodeId: NodeId,
    targetNodeId: NodeId
  ): RouteResponse {
    const payload = (response as { data?: RouteResponse | RawRoutePathStep[] | RawRouteGeometryStep[] })?.data ?? response;

    if (Array.isArray(payload)) {
      if (this.isGeometryRoutePayload(payload)) {
        const sortedSegments = [...payload].sort((a, b) => a.seq - b.seq);
        const path = sortedSegments.map((segment) => ({
          segment_id: segment.edge_id,
          from_node_id: segment.start_node,
          to_node_id: segment.end_node,
          length_km: Number(segment.distance_km ?? 0),
          geometry: segment.geometry
        }));
        const nodeSequence: NodeId[] = sortedSegments.length > 0
          ? [sortedSegments[0].start_node, ...sortedSegments.map((segment) => segment.end_node)]
          : [];
        const totalDistanceKm = sortedSegments.reduce((maxDistance, segment) => {
          const cumulative = Number(segment.total_distance ?? 0) + Number(segment.distance_km ?? 0);
          return Math.max(maxDistance, Number.isFinite(cumulative) ? cumulative : maxDistance);
        }, 0);

        return {
          source_node_id: sourceNodeId,
          target_node_id: targetNodeId,
          total_distance_km: totalDistanceKm,
          num_segments: sortedSegments.length,
          path,
          node_sequence: nodeSequence
        };
      }

      const nodeSequence = payload.map((step) => step.node_id);
      const totalDistanceKm = Number(payload[payload.length - 1]?.total_distance ?? 0);
      return {
        source_node_id: sourceNodeId,
        target_node_id: targetNodeId,
        total_distance_km: Number.isFinite(totalDistanceKm) ? totalDistanceKm : 0,
        num_segments: Math.max(nodeSequence.length - 1, 0),
        path: [],
        node_sequence: nodeSequence
      };
    }

    const route = payload as RouteResponse;
    return {
      source_node_id: route?.source_node_id ?? sourceNodeId,
      target_node_id: route?.target_node_id ?? targetNodeId,
      total_distance_km: Number(route?.total_distance_km ?? 0),
      num_segments: Number(route?.num_segments ?? route?.path?.length ?? 0),
      path: route?.path ?? [],
      node_sequence: route?.node_sequence
    };
  }

  private isGeometryRoutePayload(
    payload: RawRoutePathStep[] | RawRouteGeometryStep[]
  ): payload is RawRouteGeometryStep[] {
    return payload.length > 0 && 'start_node' in payload[0] && 'end_node' in payload[0];
  }

  getShippingLanes(limit?: number): Observable<ShippingLane[]> {
    let url = `${this.apiUrl}/shipping-lanes`;
    if (limit) {
      url += `?limit=${limit}`;
    }
    return this.http.get<ShippingLane[]>(url);
  }
}

