export interface BorderNode {
  id: string;
  lat: number;
  lon: number;
  name: string;
  country_code: string;
  from_country: string;
  to_country: string;
  from_TSO: string | null;
  to_TSO: string | null;
}