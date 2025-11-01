export type TicketStatus =
  | 'open'
  | 'locked'
  | 'resolved_harmful'
  | 'resolved_malfunction'
  | 'resolved_normal'
  | 'dismissed';

export interface Ticket {
  id: string;
  title: string;
  description: string;
  status: TicketStatus;
  location: string;
  category: string;
}

export type TicketsByStatus = Record<TicketStatus, Ticket[]>;

export interface ThreatData {
  entity_id: string;
  headline_score: number;
}
