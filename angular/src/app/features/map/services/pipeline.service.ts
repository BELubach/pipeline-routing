import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { BorderNode } from '../models/border-node.model';
import { GemPipelineSegment, RouteResponse, RouteSegment } from '../models/pipeline-segments';
import { Node } from '../models/generic-node.model';

interface RawRoutePathStep {
  seq: number;
  node_id: number;
  node_name: string;
  edge_id: number;
  distance_km: number | null;
  total_distance: number;
}

interface RawRouteGeometryStep {
  seq: number;
  edge_id: number;
  start_node: number;
  end_node: number;
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

  getNodes(): Observable<Node[]> {
    return this.http.get<{ metadata: any; data: Node[] }>(`${this.apiUrl}/iggielgn/nodes-unified`)
      .pipe(map(res => res.data));
  }

  getBorderCrossings(): Observable<BorderNode[]> {
    return this.http.get<BorderNode[]>(`${this.apiUrl}/pipelines/border-crossings`);
  }

  getPipelineSegments(): Observable<RouteSegment[]> {
    return this.http
      .get<{ metadata: any; data: RouteSegment[] }>(`${this.apiUrl}/iggielgn/segments`)
      .pipe(map(res => res.data));
  }

  getGemSegments(): Observable<GemPipelineSegment[]> {
    return this.http
      .get<{ metadata: any; data: GemPipelineSegment[] }>(`${this.apiUrl}/gem/segments`)
      .pipe(map(res => res.data));
  }

  getMaritimeNodes(limit?: number): Observable<Node[]> {
    let url = `${this.apiUrl}/maritime-routes/nodes`;
    if (limit) {
      url += `?limit=${limit}`;
    }
    return this.http.get<Node[]>(url);
  }

  getMaritimeSegments(limit?: number): Observable<RouteSegment[]> {
    let url = `${this.apiUrl}/maritime-routes/segments`;
    if (limit) {
      url += `?limit=${limit}`;
    }
    return this.http.get<RouteSegment[]>(url);
  }






  /** Asks the API for the shortest route between two nodes and returns it as a clean RouteResponse, regardless of what format the API sends back. */
  getRoute(sourceNodeId: number, targetNodeId: number): Observable<RouteResponse> {
    return this.http
      .get<{
        metadata?: any;
        data?: RouteResponse | RawRoutePathStep[] | RawRouteGeometryStep[];
      } | RouteResponse | RawRoutePathStep[] | RawRouteGeometryStep[]>(
        `${this.apiUrl}/routes/path/${sourceNodeId}/${targetNodeId}`
      )
      .pipe(map((res) => this.normalizeRouteResponse(res, sourceNodeId, targetNodeId)));
  }

  /**
   * The API can return route data in three different shapes depending on the endpoint version.
   * This squashes all of them into one consistent RouteResponse object so the rest of the app doesn't have to care.
   */
  private normalizeRouteResponse(
    response: { metadata?: any; data?: RouteResponse | RawRoutePathStep[] | RawRouteGeometryStep[] } | RouteResponse | RawRoutePathStep[] | RawRouteGeometryStep[],
    sourceNodeId: number,
    targetNodeId: number
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
        const nodeSequence: number[] = sortedSegments.length > 0
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

  /** Returns true if the array coming from the API contains geometry (coordinates), false if it's just a list of node ids. */
  private isGeometryRoutePayload(
    payload: RawRoutePathStep[] | RawRouteGeometryStep[]
  ): payload is RawRouteGeometryStep[] {
    return payload.length > 0 && 'start_node' in payload[0] && 'end_node' in payload[0];
  }


}

